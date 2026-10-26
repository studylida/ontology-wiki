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


async def indexed_source(sessions, settings, principal, reviewer, embedding_client, *, publisher="samsung", text="DRAM capacitor stores charge."):
    documents = DocumentService(sessions, settings)
    source = await documents.create(principal, NewDocument(title=f"{publisher} technical source", content=text,
        publisherId=publisher, publisher=publisher, sourceType="official", visibility="shared_candidate"))
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
