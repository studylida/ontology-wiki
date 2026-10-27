import pytest
from sqlalchemy import select

from knowledge.core.errors import AppError
from knowledge.documents.dto import MetadataPatch
from knowledge.documents.entities import Passage
from knowledge.documents.service import DocumentService
from knowledge.rag.candidates import merge_candidates
from knowledge.rag.dto import RetrievalRequest
from knowledge.rag.service import RetrievalService
from test_rag_contract import indexed_source


def test_fusion_keeps_distinct_occurrences_and_does_not_double_count_one_pool():
    first = {"passageId": "a", "sourceRevisionId": "r1", "text": "same", "methods": ["vector"]}
    duplicate_source = {"passageId": "b", "sourceRevisionId": "r2", "text": "same", "methods": ["graph"]}
    once = merge_candidates([[first], [duplicate_source, first]])
    repeated = merge_candidates([[first, first], [duplicate_source, first]])
    assert once == repeated
    assert [hit["passageId"] for hit in once] == ["a", "b"]
    assert "fusionScore" not in first


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
