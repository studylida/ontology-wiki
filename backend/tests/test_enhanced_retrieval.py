import asyncio
import pytest
from sqlalchemy import select

from knowledge.core.errors import AppError
from knowledge.documents.dto import MetadataPatch
from knowledge.documents.entities import Passage
from knowledge.documents.service import DocumentService
from knowledge.documents.repository import select_ranked_hits
from knowledge.rag.candidates import merge_candidates
from knowledge.rag.context import citation
from knowledge.rag.dto import RetrievalRequest
from knowledge.rag.service import RetrievalService
from knowledge.rag.planning import plan_requirements, reranking_query
from knowledge.rag.entities import RetrievalRun
from test_rag_contract import indexed_source


def test_fusion_keeps_distinct_occurrences_and_does_not_double_count_one_pool():
    first = {"passageId": "a", "sourceRevisionId": "r1", "text": "same", "methods": ["vector"]}
    duplicate_source = {"passageId": "b", "sourceRevisionId": "r2", "text": "same", "methods": ["graph"]}
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
async def test_reranker_sees_broad_pool_once_then_keeps_neighbor_conditions(sessions, settings, principal, reviewer, embedding_client):
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
    assert ranker.calls == 1
    assert "## 관찰" in result["hits"][0]["text"]
    assert any("250°C" in hit["text"] and "neighbor" in hit["methods"] for hit in result["hits"])
    assert result["pipeline"]["reranking"]["status"] == "completed"


@pytest.mark.asyncio
async def test_graph_is_extended_only_and_unknown_ids_never_become_evidence(sessions, settings, principal, reviewer, embedding_client):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    async with sessions() as session:
        passage_id = await session.scalar(select(Passage.id).where(Passage.source_revision_id == source["currentRevisionId"]))

    class Graph:
        calls = 0

        async def search(self, query, manifest):
            self.calls += 1
            assert manifest["revisions"][0]["sourceRevisionId"] == source["currentRevisionId"]
            return {"status": "ready", "passageIds": ["invented-id", passage_id], "usage": {"components": []}}

    graph = Graph()
    rag = RetrievalService(sessions, embedding_client, settings, graph_search=graph)
    basic = await rag.search(principal, RetrievalRequest(message="DRAM"))
    assert graph.calls == 0 and basic["pipeline"]["graph"]["status"] == "not_requested"
    extended = await rag.search(principal, RetrievalRequest(message="DRAM", extended=True))
    assert graph.calls == 1
    assert [hit["passageId"] for hit in extended["hits"]] == [passage_id]
    assert "graph" in extended["hits"][0]["methods"]


@pytest.mark.asyncio
async def test_graph_metadata_change_during_reranking_rejects_stale_evidence(sessions, settings, principal, reviewer, embedding_client):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client)

    class Graph:
        async def search(self, query, manifest):
            return {"status": "ready", "passageIds": [], "usage": {"components": []}}

    class EditMetadata:
        async def rerank(self, query, hits):
            await DocumentService(sessions, settings).patch_metadata(reviewer, source["currentRevisionId"],
                MetadataPatch(author="Corrected author"))
            return {"hits": hits}

        async def aclose(self):
            pass

    with pytest.raises(AppError) as failure:
        await RetrievalService(sessions, embedding_client, settings, reranker=EditMetadata(), graph_search=Graph()).search(
            principal, RetrievalRequest(message="DRAM", extended=True))
    assert failure.value.code == "SOURCE_SNAPSHOT_CHANGED"


@pytest.mark.asyncio
async def test_unavailable_graph_reports_degradation_with_existing_evidence(sessions, settings, principal, reviewer, embedding_client):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client)

    class Graph:
        async def search(self, query, manifest):
            return {"status": "unavailable", "reason": "snapshot_changed", "passageIds": [], "usage": {"components": []}}

    result = await RetrievalService(sessions, embedding_client, settings, graph_search=Graph()).search(principal,
        RetrievalRequest(message="DRAM", extended=True))
    assert result["hits"]
    assert result["pipeline"]["graph"] == {"status": "unavailable", "reason": "snapshot_changed"}
    assert any("관계 검색을 사용할 수 없어" in warning for warning in result["warnings"])


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [RuntimeError, asyncio.CancelledError])
async def test_graph_interruption_keeps_observed_and_unknown_costs(sessions, settings, principal, reviewer, embedding_client, error_type):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client)

    class Graph:
        async def search(self, query, manifest):
            error = error_type()
            error.usage = {"components": [
                {"operation": "graph", "calls": 1, "costUsd": .01},
                {"operation": "graph", "calls": 1, "costUsd": None}]}
            raise error

    with pytest.raises(error_type) as failure:
        await RetrievalService(sessions, embedding_client, settings, graph_search=Graph()).search(principal,
            RetrievalRequest(message="DRAM", extended=True))
    usage = failure.value.usage
    assert usage["knownCostUsd"] >= .01
    assert usage["costUsd"] is None and usage["unknownCostCalls"] == 1
    async with sessions() as session:
        stored = await session.scalar(select(RetrievalRun))
        assert stored.result["usage"] == usage
        assert stored.result["pipeline"]["graph"]["status"] in ("failed", "cancelled")
