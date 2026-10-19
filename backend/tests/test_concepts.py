"""Unit Tests for Concept Details, Causal Subgraph (CTE), and Contextual Explainer APIs.

Verifies:
1. GET /api/v1/concepts/{id} - Concept details, principles, limitations, perspectives.
2. GET /api/v1/concepts/{id} (404 Not Found)
3. GET /api/v1/concepts/{id}/causal-subgraph - 1~2 hop Recursive CTE network & Compensating Parameters.
4. GET /api/v1/concepts/{id}/causal-subgraph performance latency.
5. GET /api/v1/concepts/{id}/contextual-explainer - 0ms popover inline context.
"""
import pytest
from httpx import AsyncClient, ASGITransport
import time

from backend.app.main import app
from backend.app.core.cache import cache_manager


@pytest.fixture(autouse=True)
async def setup_cache():
    """Ensure in-memory/redis cache manager is initialized for testing."""
    await cache_manager.init()
    yield
    await cache_manager.close()


@pytest.mark.asyncio
async def test_get_concept_detail_tcb():
    """열압착 본딩(concept-tcb)의 상세 본문 및 실무 사례(PerspectiveCases) 조회 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/concepts/concept-tcb")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "concept-tcb"
        assert data["title"] == "열압착 본딩"
        assert data["engName"] == "Thermal Compression Bonding (TCB)"
        assert data["domainFacet"] == "unit_process"
        assert data["scaleLevel"] == 3
        assert "summary" in data
        assert "purpose" in data
        assert isinstance(data["principles"], list)
        assert isinstance(data["limitations"], list)

        # 적응형 실무 사례 (PerspectiveCases) 검증
        assert "perspectives" in data
        assert len(data["perspectives"]) >= 1
        p_first = data["perspectives"][0]
        assert "perspectiveId" in p_first
        assert "perspectiveTitle" in p_first
        assert "contextNarrative" in p_first
        assert "caution" in p_first


@pytest.mark.asyncio
async def test_get_concept_detail_not_found():
    """존재하지 않는 개념 ID 조회 시 404 에러 반환 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/concepts/concept-non-existent-999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_get_causal_subgraph_with_compensating_params():
    """1~2 hop Recursive CTE 인과 서브그래프 및 '보상 파라미터(Compensating Parameters)' 서빙 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/concepts/concept-tcb/causal-subgraph?depth=2&direction=both")
        assert response.status_code == 200
        data = response.json()

        assert data["centralConceptId"] == "concept-tcb"
        assert "graph" in data
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 1

        # 중심 노드 확인
        center_nodes = [n for n in graph["nodes"] if n.get("isCenter")]
        assert len(center_nodes) == 1
        assert center_nodes[0]["id"] == "concept-tcb"

        # 🌟 도메인 필수 검증: 보상 파라미터(Compensating Parameters) 탑재 엣지 존재 확인
        comp_edges = [e for e in graph["edges"] if e.get("compensatingParams") is not None]
        assert len(comp_edges) >= 1, "At least one causal edge must have compensatingParams"
        
        comp_param = comp_edges[0]["compensatingParams"]
        assert "parameter" in comp_param
        assert "compensationFormula" in comp_param
        assert "tradeoffCost" in comp_param


@pytest.mark.asyncio
async def test_causal_subgraph_query_latency():
    """Recursive CTE 인과 탐색 API 응답 지연시간 실측 검증 (< 50ms)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.perf_counter()
        response = await client.get("/api/v1/concepts/param-bonding-pressure/causal-subgraph?depth=2")
        duration_ms = (time.perf_counter() - start) * 1000.0

        assert response.status_code == 200
        assert duration_ms < 50.0  # 고성능 CTE 검증


@pytest.mark.asyncio
async def test_get_contextual_explainer():
    """위키 본문 단어 호버 시 0ms 인라인 문맥 해설 조회 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/concepts/concept-tcb/contextual-explainer?term_id=concept-mrmuf")
        assert response.status_code == 200
        data = response.json()

        assert data["childConceptId"] == "concept-mrmuf"
        assert data["parentConceptId"] == "concept-tcb"
        assert "title" in data
        assert "definition" in data
        assert "contextSentence" in data
        assert data["cached"] is True
        assert data["deepLink"] == "/wiki?concept=concept-mrmuf"
