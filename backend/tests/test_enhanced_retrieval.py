import pytest
from sqlalchemy import select

from knowledge.documents.dto import MetadataPatch
from knowledge.documents.entities import Document, DocumentRevision, Passage
from knowledge.documents.service import DocumentService
from knowledge.documents.repository import citation_dict, select_ranked_hits
from knowledge.rag.candidates import merge_candidates
from knowledge.rag.context import citation, conflict_companions, experiment_companions, prioritize_conflict_notes
from knowledge.rag.dto import RetrievalRequest
from knowledge.rag.service import RetrievalService, relevant_relations
from knowledge.rag.planning import plan_requirements, reranking_query
from test_rag_contract import indexed_source


def test_fusion_keeps_distinct_occurrences_and_does_not_double_count_one_pool():
    first = {"passageId": "a", "sourceRevisionId": "r1", "text": "same", "methods": ["vector"]}
    duplicate_source = {"passageId": "b", "sourceRevisionId": "r2", "text": "same", "methods": ["lexical"]}
    once = merge_candidates([[first], [duplicate_source, first]])
    repeated = merge_candidates([[first, first], [duplicate_source, first]])
    assert once == repeated
    assert [hit["passageId"] for hit in once] == ["a", "b"]
    assert "fusionScore" not in first


def test_same_original_editions_share_diversity_limit_without_merging_passage_ids():
    hits = [{"passageId": str(i), "sourceRevisionId": f"r{i}", "documentId": f"d{i}",
             "lineageKey": "original-a" if i < 4 else "original-b"} for i in range(5)]
    result = select_ranked_hits(hits, limit=4, per_document_limit=3)
    assert [hit["passageId"] for hit in result["hits"]] == ["0", "1", "2", "4"]


def test_power_comparison_explicitly_plans_numeric_energy_evidence():
    plan = plan_requirements("A와 B의 전력 차이를 수치로 비교하고 조건이 부족하면 표시해 주세요.")
    assert plan[0]["id"] == "power"
    assert "비트당 에너지" in plan[0]["query"]
    assert "지연" not in plan[0]["query"]
    mixed = plan_requirements("A와 B의 경로, 전력, 지연을 비교하고 전력 수치가 부족하면 표시해 주세요.")
    assert {"path", "power", "delay", "comparison"} <= {item["id"] for item in mixed}


def test_numeric_request_prioritizes_requested_parameter_without_changing_subject_or_qualitative_query():
    question = "A와 B의 전력과 지연을 비교하고 전력 차이를 수치로 알려 주세요."
    focused = reranking_query(question, plan_requirements(question))
    assert focused.startswith(question + "\n중점 확인:")
    assert "비트당 에너지" in focused.split("\n")[1]
    assert "지연" not in focused.split("\n")[1]
    temperature = "증착 온도의 측정값과 성장률을 설명해 주세요."
    assert "온도 조건" in reranking_query(temperature, plan_requirements(temperature)).split("\n")[1]
    for query in ("A와 B의 전력 차이를 설명해 주세요.", "열압착의 원리와 조건을 알려 주세요."):
        assert reranking_query(query, plan_requirements(query)) == query


def test_experimental_result_recovers_original_methods_from_same_lineage():
    result = {"passageId": "result", "sourceRevisionId": "r1", "lineageKey": "study-a",
              "locator": "4. Results", "text": "The measured growth rate was 1.07 Å/cycle."}
    summary = {"passageId": "summary", "sourceRevisionId": "r2", "lineageKey": "study-a",
               "locator": "실험 결과", "text": "온도별 실험 결과", "documentForm": "editorial_summary"}
    other = {"passageId": "other", "sourceRevisionId": "r3", "lineageKey": "study-b",
             "locator": "2. Materials and Methods", "text": "Different sample, 20 °C.", "documentForm": "text_extraction"}
    conditions = {"passageId": "conditions", "sourceRevisionId": "r1", "lineageKey": "study-a",
                  "locator": "3. Experimental Details", "text": "Samples at 175 and 275 °C.", "documentForm": "text_extraction"}
    companions = experiment_companions([result, summary, other, conditions], [result, summary])
    assert [hit["passageId"] for hit in companions] == ["conditions"]
    assert companions[0]["text"] == conditions["text"]
    assert conditions.get("methods") is None


def test_explicit_source_discrepancy_note_is_prioritized_without_manufacturing_one():
    hits = [{"passageId": "a", "text": "시편 조건이 다르다."},
            {"passageId": "b", "locator": "원문 내부의 차이와 적용 한계", "text": "두 절의 유량이 20 sccm과 50 sccm으로 다르게 제시됐다."}]
    assert [h["passageId"] for h in prioritize_conflict_notes(hits)] == ["b", "a"]
    assert [h["passageId"] for h in hits] == ["a", "b"]


def test_explicit_discrepancy_is_included_only_for_selected_source():
    selected = [{"passageId": "a", "sourceRevisionId": "r1", "lineageKey": "study-a"}]
    other = {"passageId": "b", "lineageKey": "study-b", "text": "원문 내부에 수치 불일치"}
    note = {"passageId": "c", "lineageKey": "study-a", "text": "원문 내부에 유량 불일치: 20 sccm과 50 sccm"}
    merely_different = {"passageId": "d", "lineageKey": "study-a", "text": "시편 A는 20, 시편 B는 50"}
    figure = {"passageId": "e", "lineageKey": "study-a", "text": "원문 내부 그림 5의 시편 ID 불일치"}
    assert [h["passageId"] for h in conflict_companions([other, merely_different, figure, note], selected)] == ["c"]


@pytest.mark.asyncio
async def test_relation_evidence_is_checked_against_question_before_inclusion():
    anchors = [{"passageId": f"direct-{i}", "text": "SRAM과 DRAM"} for i in range(5)]
    related = {"id": "related", "evidence": [{"passageId": "r", "excerpt": "DRAM의 메모리 셀"}]}
    unrelated = {"id": "unrelated", "evidence": [{"passageId": "u", "excerpt": "SSD 보조기억장치"}]}

    class Rank:
        async def rerank(self, query, hits):
            assert query == "SRAM과 DRAM 비교"
            by_id = {hit["passageId"]: hit for hit in hits}
            return {"hits": [by_id[k] for k in ["direct-0", "r", "direct-1", "direct-2", "direct-3", "u", "direct-4"]], "elapsedMs": 1}

    kept, info = await relevant_relations(Rank(), "SRAM과 DRAM 비교", anchors, [related, unrelated])
    assert [card["id"] for card in kept] == ["related"]
    assert info["status"] == "ranked" and info["kept"] == 1
    assert related["evidence"][0]["excerpt"] == "DRAM의 메모리 셀"

    direct = {"id": "already-direct", "evidence": [{"passageId": "direct-0", "excerpt": "SRAM과 DRAM"}]}
    kept_without_reranker, info = await relevant_relations(None, "질문", anchors, [direct, unrelated])
    assert kept_without_reranker == [direct] and info["status"] == "direct_evidence_only"
    kept_without_anchors, info = await relevant_relations(Rank(), "질문", [], [unrelated])
    assert kept_without_anchors == [] and info["status"] == "direct_evidence_only"


@pytest.mark.asyncio
async def test_verified_lineage_reaches_answer_citation(sessions, settings, principal, reviewer, embedding_client):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    await DocumentService(sessions, settings).patch_metadata(reviewer, source["currentRevisionId"],
        MetadataPatch(lineage_key="doi:verified-original"))
    found = await RetrievalService(sessions, embedding_client, settings).search(principal,
        RetrievalRequest(message="DRAM"))
    projected = citation(found["hits"][0])
    assert projected["lineageKey"] == "doi:verified-original"
    assert projected["passageId"] == found["hits"][0]["passageId"]


@pytest.mark.asyncio
async def test_saved_source_views_are_not_reused_as_generation_evidence(sessions, settings, principal, reviewer, embedding_client, monkeypatch):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    from knowledge.ontology.repository import OntologyRepository
    view = {"id": "derived", "summary": "원문을 대신할 수 없는 AI 관점", "aspect": "principle"}
    async def context(self, *args):
        return {"sourceViews": [view], "relations": [], "relatedConcepts": []}
    monkeypatch.setattr(OntologyRepository, "context", context)
    result = await RetrievalService(sessions, embedding_client, settings).search(principal,
        RetrievalRequest(message="DRAM"))
    assert result["sourceViews"] == [view]
    assert result["grounding"]["sourceViews"] == []
    assert result["grounding"]["passages"]


@pytest.mark.asyncio
async def test_reranker_preserves_neighbor_conditions_for_principle_request(sessions, settings, principal, reviewer, embedding_client):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client,
        text="\n\n".join(f"## 무관 설명 {i}\n일반적인 금속." for i in range(10)) +
             "\n\n## 조건\n시편을 250°C에서 1시간 가열했다.\n\n## 관찰\n구리 계면이 결합했다.")

    class RankObservations:
        calls = 0

        async def rerank(self, query, hits):
            self.calls += 1
            assert len(hits) > 8
            return {"hits": sorted(hits, key=lambda hit: "## 관찰" not in hit["text"]), "elapsedMs": 1}

        async def aclose(self):
            pass

    ranker = RankObservations()
    options = settings.model_copy(update={"retrieval_limit": 1})
    result = await RetrievalService(sessions, embedding_client, options, reranker=ranker).search(principal,
        RetrievalRequest(message="구리 접합 원리와 조건", extended=True))
    assert ranker.calls == 2
    assert "## 관찰" in result["hits"][0]["text"]
    assert any("250°C" in hit["text"] and "neighbor" in hit["methods"] for hit in result["hits"])
    assert result["pipeline"]["reranking"]["status"] == "completed"


@pytest.mark.asyncio
async def test_principle_focus_adds_a_new_source_without_displacing_the_direct_result(sessions, settings, principal, reviewer, embedding_client):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client, text="기술의 일반적인 소개와 응용")
    await indexed_source(sessions, settings, principal, reviewer, embedding_client, text="각 요소가 작용해 결과가 생기는 원리")
    await indexed_source(sessions, settings, principal, reviewer, embedding_client, text="그 밖의 주변 기술 설명")

    class Rank:
        async def rerank(self, query, hits):
            focused = "각 요소의 역할과 변화" in query
            def priority(hit):
                if "일반적인 소개" in hit["text"]:
                    return 0
                if "작용해 결과" in hit["text"]:
                    return 1 if focused else 2
                return 2 if focused else 1
            return {"hits": sorted(hits, key=priority), "elapsedMs": 1}
        async def aclose(self):
            pass

    options = settings.model_copy(update={"retrieval_limit": 1})
    found = await RetrievalService(sessions, embedding_client, options, reranker=Rank()).search(
        principal, RetrievalRequest(message="기술의 원리와 적용 조건", extended=True))
    assert "일반적인 소개" in found["hits"][0]["text"]
    assert any("작용해 결과" in h["text"] and "principle_focus" in h["methods"] for h in found["hits"])
    assert found["pipeline"]["principleFocus"]["count"] == 1


@pytest.mark.asyncio
async def test_experiment_condition_survives_lineage_cap_and_nonadjacent_section(sessions, settings, principal, reviewer, embedding_client):
    text = "\n\n".join(["## 실험 조건\n시편을 250°C에서 30분 가열했다."] +
        [f"## 배경 {i}\n일반적인 표면 설명 {i}." for i in range(6)] +
        ["## 결과 A\n시편 접합률은 90%였다.", "## 결과 B\n시편 접합률은 80%였다."])
    await indexed_source(sessions, settings, principal, reviewer, embedding_client, text=text)

    class Rank:
        async def rerank(self, query, hits):
            def priority(hit):
                text = hit["text"]
                return 0 if "## 결과 A" in text else 1 if "## 결과 B" in text else 2 if "## 실험 조건" in text else 3
            return {"hits": sorted(hits, key=priority), "elapsedMs": 1}

        async def aclose(self):
            pass

    options = settings.model_copy(update={"retrieval_limit": 2})
    found = await RetrievalService(sessions, embedding_client, options, reranker=Rank()).search(
        principal, RetrievalRequest(message="접합 실험 결과와 조건", extended=True))
    selected = found["grounding"]["passages"]
    assert any("접합률은 90%" in p["text"] for p in selected)
    assert any("250°C" in p["text"] for p in selected)
    assert found["pipeline"]["experimentCompanions"]["count"] == 1
    assert any("experiment_companion" in h.get("methods", []) for h in found["hits"])


@pytest.mark.asyncio
async def test_irrelevant_relation_not_added_to_answer_but_source_is_preserved(sessions, settings, principal, reviewer, embedding_client, monkeypatch):
    main = await indexed_source(sessions, settings, principal, reviewer, embedding_client, text="SRAM과 DRAM의 셀 구조")
    related = await indexed_source(sessions, settings, principal, reviewer, embedding_client, text="SRAM과 DRAM의 차이")
    other = await indexed_source(sessions, settings, principal, reviewer, embedding_client, text="SSD의 저장 매체")
    revision_ids = [v["currentRevisionId"] for v in (main, related, other)]
    async with sessions() as session:
        rows = (await session.execute(select(Passage, DocumentRevision, Document)
            .join(DocumentRevision, Passage.source_revision_id == DocumentRevision.id).join(Document)
            .where(Passage.source_revision_id.in_(revision_ids)))).all()
    refs = {r.id: citation_dict(p, r, d) for p, r, d in rows}
    main_id, related_id, other_id = (refs[r]["passageId"] for r in revision_ids)

    from knowledge.ontology.repository import OntologyRepository
    async def context(self, *args):
        return {"relatedConcepts": [], "sourceViews": [], "relations": [
            {"id": "related", "evidence": [refs[revision_ids[1]]]},
            {"id": "other", "evidence": [refs[revision_ids[2]]]}]}
    monkeypatch.setattr(OntologyRepository, "context", context)

    class Rank:
        async def rerank(self, query, hits):
            positions = {main_id: 0, related_id: 1, other_id: 2}
            return {"hits": sorted(hits, key=lambda h: positions[h["passageId"]]), "elapsedMs": 1}
        async def aclose(self):
            pass

    options = settings.model_copy(update={"retrieval_limit": 1})
    found = await RetrievalService(sessions, embedding_client, options, reranker=Rank()).search(
        principal, RetrievalRequest(message="SRAM과 DRAM 비교", extended=True))
    assert [relation["id"] for relation in found["relations"]] == ["related"]
    assert other_id not in [hit["passageId"] for hit in found["hits"]]
    assert found["pipeline"]["relationRelevance"]["status"] == "ranked"
    async with sessions() as session:
        assert await session.get(Passage, other_id) is not None
