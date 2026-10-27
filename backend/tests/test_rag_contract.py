import asyncio

import pytest

from knowledge.core.errors import AppError
from knowledge.documents.dto import NewDocument, ReviewRequest
from knowledge.documents.entities import DocumentRevision
from knowledge.documents.service import DocumentService
from knowledge.jobs.indexing import enqueue_index, process_index_job
from knowledge.rag.context import additional_queries, select_context
from knowledge.rag.dto import RetrievalRequest, SourceGroup
from knowledge.rag.service import RetrievalService


async def indexed_source(sessions, settings, principal, reviewer, embedding_client, *, publisher="samsung", author=None, text="DRAM capacitor stores charge."):
    documents = DocumentService(sessions, settings)
    source = await documents.create(principal, NewDocument(title=f"{publisher} technical source", content=text,
        publisherId=publisher, publisher=publisher, author=author, sourceType="official", visibility="shared_candidate"))
    revision_id = source["currentRevisionId"]
    await documents.review(reviewer, revision_id, ReviewRequest(decision="approve", reason="테스트 문헌 검토"))
    async with sessions() as session, session.begin():
        revision = await session.get(DocumentRevision, revision_id)
        job = await enqueue_index(session, revision, embedding_client.profile_id, reviewer.id)
        await session.flush()
        job.status = "running"
        job_id = job.id
    result = await process_index_job(sessions, embedding_client, job_id)
    assert result["status"] == "succeeded"
    return source


def test_context_budget_preserves_occurrence_identity_and_declares_truncation():
    hits = [{"id": "a", "passageId": "a", "text": "a" * 50}, {"id": "b", "passageId": "b", "text": "b" * 50},
            {"id": "a", "passageId": "a", "text": "duplicate"}]
    result = select_context(hits, 75)
    assert [r["passageId"] for r in result] == ["a", "b"]
    assert sum(len(r["text"]) for r in result) == 75
    assert result[1]["contextTruncated"] is True
    assert len(additional_queries("A process? B alternative? C limit?", "conditions", 2)) == 2


def test_author_rank_is_identical_for_all_passages_of_same_revision():
    from knowledge.documents.repository import author_ranking
    hits = [{"sourceRevisionId": "a", "author": "Alice Smith, Bob Lee", "passageId": "z"},
            {"sourceRevisionId": "a", "author": "Alice Smith, Bob Lee", "passageId": "a"},
            {"sourceRevisionId": "b", "author": "Carol Smith, David Lee", "passageId": "b"}]
    scores = author_ranking(hits, ["smith", "lee"])
    assert scores["a"] == scores["b"] == 1 / 61
    assert scores == author_ranking(list(reversed(hits)), ["smith", "lee"])


@pytest.mark.asyncio
async def test_author_metadata_improves_ranking_without_dropping_other_sources(sessions, settings, principal, reviewer, embedding_client):
    from knowledge.documents.repository import DocumentRepository

    first = await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher="first",
        author="Alice Smith, Bob Lee", text="공정 성장률 결과 및 시험 조건.")
    second = await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher="second",
        author="Carol Jones, David Khan", text="공정 성장률 결과 및 시험 조건.")
    async with sessions() as session:
        repo = DocumentRepository(session)
        query = "Smith와 Lee의 연구에서 성장률 결과는?"
        vector = (await embedding_client.embed([query])).vectors[0]
        result = await repo.search(principal, vector, embedding_client.profile_id, query)
        assert result["hits"][0]["sourceRevisionId"] == first["currentRevisionId"]
        assert {hit["sourceRevisionId"] for hit in result["hits"]} == {first["currentRevisionId"], second["currentRevisionId"]}
        combined = "Smith와 Lee의 연구 결과와 Jones와 Khan의 연구 결과를 함께 알려줘"
        vector = (await embedding_client.embed([combined])).vectors[0]
        result = await repo.search(principal, vector, embedding_client.profile_id, combined)
        assert {hit["sourceRevisionId"] for hit in result["hits"]} == {first["currentRevisionId"], second["currentRevisionId"]}


@pytest.mark.asyncio
async def test_chemical_tokens_and_author_matches_keep_distinct_sources(sessions, settings, principal, reviewer, embedding_client):
    from knowledge.documents.repository import DocumentRepository

    chemical = await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher="chemical",
        author="Alice Smith, Bob Lee", text="# 소스\n\n## 측정\nAl₂O₃ 및 SiO₂와 H₂O의 실험 값.")
    other = await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher="other",
        author="Carol Jones, David Khan", text="thermal metal material")
    international = await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher="intl",
        author="Emir Bostancı", text="전기저항 단위 ωμ 결과")
    async with sessions() as session:
        repo = DocumentRepository(session)
        for term in ("Al₂O₃", "SiO₂", "H₂O"):
            vector = (await embedding_client.embed([term])).vectors[0]
            result = await repo.search(principal, vector, "missing-profile", term)
            assert {hit["sourceRevisionId"] for hit in result["hits"]} == {chemical["currentRevisionId"]}
        for term in ("Bostancı의", "ωμ"):
            vector = (await embedding_client.embed([term])).vectors[0]
            result = await repo.search(principal, vector, "missing-profile", term)
            assert {hit["sourceRevisionId"] for hit in result["hits"]} == {international["currentRevisionId"]}, ascii(term)

    # Title/author metadata is matched once per document, even for many passages.
    long_source = await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher="long",
        author="Alice Smith, Bob Lee", text="\n\n".join(f"## 단락 {i}\n자료" for i in range(75)))
    from sqlalchemy import select
    from knowledge.documents.entities import Passage
    async with sessions() as session, session.begin():
        first = await session.scalar(select(Passage).where(Passage.source_revision_id == long_source["currentRevisionId"], Passage.ordinal == 0))
        first.excluded = True
    async with sessions() as session:
        repo = DocumentRepository(session)
        query = "Smith와 Lee의 연구와 Jones와 Khan의 연구를 비교"
        vector = (await embedding_client.embed([query])).vectors[0]
        result = await repo.search(principal, vector, "missing-profile", query)
        ids = {hit["sourceRevisionId"] for hit in result["hits"]}
        assert {chemical["currentRevisionId"], other["currentRevisionId"], long_source["currentRevisionId"]} <= ids


@pytest.mark.asyncio
async def test_author_signal_keeps_relevant_experiment_passages_in_long_document(sessions, settings, principal, reviewer, embedding_client):
    from knowledge.documents.repository import DocumentRepository

    text = "# 일반 개요\n\n## 시험 조건\n성장률 실험조건 두 요인을 함께 살폈다.\n\n## 측정 결과\n성장률 실험조건의 결과를 관찰했다.\n\n" + "\n\n".join(f"## 부록 {i}\n설명" for i in range(75))
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client,
        author="Alice Smith, Bob Lee", text=text)
    query = "Smith와 Lee의 연구에서 성장률 실험조건"
    vector = (await embedding_client.embed(["성장률 실험조건"])).vectors[0]
    async with sessions() as session:
        result = await DocumentRepository(session).search(principal, vector, embedding_client.profile_id, query)
    hits = [h for h in result["hits"] if h["sourceRevisionId"] == source["currentRevisionId"]]
    assert any("시험 조건" in h["locator"] for h in hits)
    assert any("측정 결과" in h["locator"] for h in hits)


@pytest.mark.asyncio
async def test_current_snapshot_explicit_scope_and_groups_intersect(sessions, settings, principal, reviewer, embedding_client):
    first = await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    second = await indexed_source(sessions, settings, principal, reviewer, embedding_client,
        publisher="sk", text="DRAM cell capacitor retention requires refresh.")
    rag = RetrievalService(sessions, embedding_client, settings)
    result = await rag.search(principal, RetrievalRequest(message="DRAM capacitor", sourceGroups=[
        SourceGroup(groupId="samsung", publisherId="samsung", sourceType="official"),
        SourceGroup(groupId="sk", publisherId="sk", sourceType="official")]))
    assert {h["sourceRevisionId"] for h in result["hits"]} == {first["currentRevisionId"], second["currentRevisionId"]}
    assert all(g["hitCount"] > 0 for g in result["groupCoverage"])
    narrowed = await rag.search(principal, RetrievalRequest(message="DRAM capacitor", sourceRevisionIds=[first["currentRevisionId"]],
        sourceGroups=[SourceGroup(groupId="sk", publisherId="sk")]))
    assert narrowed["hits"] == []
    assert narrowed["groupCoverage"][0]["status"] == "missing"
    assert narrowed["usage"]["calls"] == 0


@pytest.mark.asyncio
async def test_basic_search_includes_neighboring_experiment_conditions(sessions, settings, principal, reviewer, embedding_client, monkeypatch):
    from knowledge.documents.repository import DocumentRepository

    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client,
        text="# 연구\n\n## 시험 조건\n시험편은 250°C에서 1시간 가열했다.\n\n## 관찰 결과\n계면의 결정립이 성장했다.\n\n## 결론\n추가 측정이 필요하다.")
    revision = source["currentRevisionId"]
    real_search = DocumentRepository.search

    async def observation_only(self, *args, **kwargs):
        result = await real_search(self, *args, **kwargs)
        result["hits"] = [hit for hit in result["hits"] if "관찰 결과" in hit["locator"]]
        assert len(result["hits"]) == 1
        return result

    monkeypatch.setattr(DocumentRepository, "search", observation_only)
    result = await RetrievalService(sessions, embedding_client, settings).search(principal,
        RetrievalRequest(message="결정립 관찰 결과와 시험 조건", sourceRevisionIds=[revision], extended=False))
    passages = result["grounding"]["passages"]
    assert any("관찰 결과" in passage["locator"] for passage in passages)
    assert any("시험 조건" in passage["locator"] and "250°C" in passage["text"] for passage in passages)
    assert all(hit["sourceRevisionId"] == revision and "neighborOf" not in hit for hit in result["hits"])
    assert len({hit["passageId"] for hit in result["hits"]}) == len(result["hits"])
    assert result["usage"]["fixtureCalls"] == 1


@pytest.mark.asyncio
async def test_neighbors_do_not_displace_direct_sources_under_small_budget(sessions, settings, principal, reviewer, embedding_client, monkeypatch):
    from knowledge.documents.repository import DocumentRepository

    for publisher in ("first", "second"):
        await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher=publisher,
            text="# 보고서\n\n## 조건\n" + "시험 조건. " * 120 + "\n\n## 관찰\n직접 검색된 관찰 결과.")
    real_search, real_neighbors = DocumentRepository.search, DocumentRepository.get_neighbors

    async def observations_only(self, *args, **kwargs):
        result = await real_search(self, *args, **kwargs)
        result["hits"] = [hit for hit in result["hits"] if "관찰" in hit["locator"]]
        assert len(result["hits"]) == 2
        return result

    async def no_neighbors(self, *args, **kwargs):
        return []

    monkeypatch.setattr(DocumentRepository, "search", observations_only)
    monkeypatch.setattr(DocumentRepository, "get_neighbors", no_neighbors)
    rag = RetrievalService(sessions, embedding_client, settings.model_copy(update={"context_max_characters": 1800}))
    request = RetrievalRequest(message="관찰 결과")
    baseline = await rag.search(principal, request)
    monkeypatch.setattr(DocumentRepository, "get_neighbors", real_neighbors)
    result = await rag.search(principal, request)
    baseline_ids = [hit["passageId"] for hit in baseline["hits"]]
    assert len(baseline_ids) == 2
    assert [hit["passageId"] for hit in result["hits"][:2]] == baseline_ids
    assert result["exploration"]["grounding"]["groundingCharacters"] <= 1800


@pytest.mark.asyncio
async def test_pending_review_context_never_enters_shared_search(sessions, settings, principal, reviewer, other_principal, embedding_client):
    docs = DocumentService(sessions, settings)
    pending = await docs.create(principal, NewDocument(title="검토 문헌", content="pending DRAM capacitor evidence",
                                                       visibility="shared_candidate"))
    revision_id = pending["currentRevisionId"]
    rag = RetrievalService(sessions, embedding_client, settings)
    public = await rag.search(reviewer, RetrievalRequest(message="DRAM", sourceRevisionIds=[revision_id]))
    assert public["hits"] == []
    review = await rag.search(reviewer, RetrievalRequest(message="DRAM", documentContextIds=[revision_id]))
    assert review["hits"] and review["hits"][0]["sourceRevisionId"] == revision_id
    assert review["appliedFilters"]["sourceRevisionIds"] == []
    assert review["sourceViews"] == [] and review["usage"]["calls"] == 0
    with pytest.raises(AppError):
        await rag.search(other_principal, RetrievalRequest(message="DRAM", documentContextIds=[revision_id]))


@pytest.mark.asyncio
async def test_withdrawal_immediately_removes_search_and_restored_answer(app, sessions, settings, principal, reviewer, embedding_client):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    from knowledge.rag.dto import AnswerRequest
    answers = app.state.services.answers
    handle = await answers.create(principal, AnswerRequest(clientRequestId="withdrawal", message="DRAM capacitor"))
    await asyncio.wait_for(answers.runtimes[handle["runId"]].task, 10)
    before = await answers.get(principal, handle["runId"])
    assert before["status"] == "completed" and before["message"]["citations"]
    await DocumentService(sessions, settings).review(reviewer, source["currentRevisionId"],
                                                    ReviewRequest(decision="withdraw", reason="테스트 즉시 권한 철회"))
    after = await answers.get(principal, handle["runId"])
    assert after["message"]["status"] == "restricted" and after["message"]["content"] == ""
    with pytest.raises(AppError) as denied:
        await answers.check_stream(principal, handle["runId"], 0)
    assert denied.value.status_code == 403
    search = await app.state.services.rag.search(principal, RetrievalRequest(message="DRAM"))
    assert search["hits"] == []


@pytest.mark.asyncio
async def test_extended_keeps_pinned_revision_and_stops_on_no_novelty(sessions, settings, principal, reviewer, embedding_client):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    result = await RetrievalService(sessions, embedding_client, settings).search(principal,
        RetrievalRequest(message="DRAM capacitor? DRAM charge?", extended=True, aspect="retention"))
    assert result["stopReason"] == "no_new_evidence"
    assert result["usage"]["calls"] <= 1 + settings.extended_max_queries
    assert result["appliedFilters"]["sourceRevisionIds"] == [source["currentRevisionId"]]
    assert result["queries"] and all(q["query"] for q in result["queries"])


@pytest.mark.asyncio
async def test_unstructured_korean_extended_has_bounded_missing_aspect_plan(sessions, settings, principal, reviewer, embedding_client):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    result = await RetrievalService(sessions, embedding_client, settings).search(principal,
        RetrievalRequest(message="DRAM의 작동 원리와 한계를 알려 주세요", extended=True))
    assert {item["id"] for item in result["requirementCoverage"]} == {"principle", "limits"}
    assert result["exploration"]["extraQueries"] == 1
    assert len(result["queries"]) == 2
    assert result["semanticSufficiency"] == "not_evaluated"
    assert result["usage"]["calls"] == 0 and result["usage"]["fixtureCalls"] == 2
    assert result["usage"]["costUsd"] is None


@pytest.mark.asyncio
async def test_extended_timeout_keeps_basic_evidence_and_cancels_extra_call(sessions, settings, principal, reviewer, embedding_client, monkeypatch):
    from knowledge.documents.repository import DocumentRepository
    from knowledge.integrations.providers import FixtureEmbeddingClient
    await indexed_source(sessions, settings, principal, reviewer, embedding_client)

    # This test targets cancellation during the additional provider call. Do not
    # require an unrelated PostgreSQL neighbor query to finish within 30 ms.
    async def immediate_neighbors(self, *args, **kwargs):
        return []
    monkeypatch.setattr(DocumentRepository, "get_neighbors", immediate_neighbors)

    class SlowAdditionalCall(FixtureEmbeddingClient):
        def __init__(self):
            self.calls, self.was_cancelled = 0, False
        async def embed(self, texts):
            self.calls += 1
            if self.calls == 2:
                try:
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    self.was_cancelled = True
                    raise
            return await super().embed(texts)

    slow = SlowAdditionalCall()
    result = await RetrievalService(sessions, slow, settings.model_copy(update={"extended_seconds": .03})).search(principal,
        RetrievalRequest(message="DRAM의 원리와 한계", extended=True))
    assert result["stopReason"] == "time_budget"
    assert result["hits"] and slow.calls == 2 and slow.was_cancelled
    assert result["queries"][-1]["status"] == "time_budget"
    assert result["timings"]["extendedMs"] < 1000


@pytest.mark.asyncio
async def test_extended_stops_at_context_budget_without_extra_model_call(sessions, settings, principal, reviewer, embedding_client):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client, text="DRAM capacitor evidence. " * 150)
    result = await RetrievalService(sessions, embedding_client, settings.model_copy(update={"context_max_characters": 1000})).search(principal,
        RetrievalRequest(message="DRAM 원리와 한계", extended=True))
    assert result["stopReason"] == "context_budget"
    assert result["exploration"]["extraQueries"] == 0
    assert sum(len(hit["text"]) for hit in result["hits"]) <= 1000
    assert result["exploration"]["grounding"]["groundingCharacters"] <= 1000
    assert result["usage"]["fixtureCalls"] == 1


@pytest.mark.asyncio
async def test_literal_condition_mentions_never_certify_quantitative_sufficiency(sessions, settings, principal, reviewer, embedding_client):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client,
        text="HBM 온도와 압력 조건, 휨과 수율 차이는 중요하다. 정확한 수치는 이 문헌에 없다.")
    result = await RetrievalService(sessions, embedding_client, settings).search(principal,
        RetrievalRequest(message="HBM 온도와 압력, 허용 휨 수치와 양사 수율 차이의 정확한 조건은?", extended=True))
    assert result["exploration"]["extraQueries"] >= 1
    assert result["stopReason"] == "no_new_evidence"
    assert result["semanticSufficiency"] == "not_evaluated"
    assert {"temperature", "pressure", "warpage", "yield"} <= {r["id"] for r in result["requirementCoverage"]}
    assert all(r["status"] in ("candidate_found", "unknown") for r in result["requirementCoverage"])
    assert result["queries"][1]["requirementId"] == "temperature"
    assert "온도 조건·수치와 측정 범위" in result["queries"][1]["query"]


@pytest.mark.asyncio
async def test_review_hold_during_query_never_reenters_shared_search_via_owner_scope(sessions, settings, principal, reviewer, embedding_client):
    from knowledge.integrations.providers import FixtureEmbeddingClient
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    class HoldDuringQuery(FixtureEmbeddingClient):
        async def embed(self, texts):
            await DocumentService(sessions, settings).review(reviewer, source["currentRevisionId"],
                ReviewRequest(decision="hold", reason="공용 승인 보류"))
            return await super().embed(texts)
    result = await RetrievalService(sessions, HoldDuringQuery(), settings).search(principal, RetrievalRequest(message="DRAM"))
    assert result["hits"] == [], "Being the document owner must not expand the public RAG snapshot"
    assert result["sourceViews"] == [] and result["relations"] == []
