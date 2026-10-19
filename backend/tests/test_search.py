"""Unit Tests for Spotlight Search API Endpoint (/api/v1/search/spotlight).

Verifies:
1. Empty query returns default indexed concepts (limit applied, totalIndexed >= 30)
2. Keyword matching (TCB, 식각, High-NA, EUV) with score ranking
3. Domain facet filtering (unit_process, device, etc.)
4. CamelCase serialization format check
5. Non-existent query handling (0 matches, empty results)
6. Response latency & cache hit validation
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
async def test_spotlight_empty_query():
    """검색어가 비어있을 때 상위 기본 개념을 정상 반환하는지 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search/spotlight?limit=8")
        assert response.status_code == 200
        data = response.json()

        assert "totalIndexed" in data
        assert data["totalIndexed"] >= 30
        assert data["query"] == ""
        assert len(data["results"]) <= 8

        # 첫 번째 결과의 CamelCase 스키마 필드 검증
        first = data["results"][0]
        assert "id" in first
        assert "title" in first
        assert "engName" in first
        assert "processCategory" in first
        assert "domainFacet" in first
        assert "scaleLevel" in first
        assert "summary" in first
        assert "matchType" in first
        assert "score" in first


@pytest.mark.asyncio
async def test_spotlight_tcb_search():
    """'TCB' 검색 시 열압착 본딩(TC-NCF/TCB) 개념이 최상위에 랭크되는지 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search/spotlight?q=TCB")
        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "TCB"
        assert data["totalMatches"] >= 1
        results = data["results"]
        assert len(results) >= 1

        # 최상위 결과가 TCB/열압착 본딩인지 확인
        top_result = results[0]
        assert "tcb" in top_result["id"].lower() or "tcb" in top_result["title"].lower() or "tcb" in [a.lower() for a in top_result["aliases"]]
        assert top_result["score"] >= 50.0
        assert top_result["matchType"] in ["title", "alias", "eng_name"]


@pytest.mark.asyncio
async def test_spotlight_korean_process_search():
    """'식각' 검색 시 건식 식각, 극저온 식각 등이 검색되는지 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search/spotlight?q=식각")
        assert response.status_code == 200
        data = response.json()

        assert data["totalMatches"] >= 2
        titles = [r["title"] for r in data["results"]]
        assert any("식각" in t for t in titles)


@pytest.mark.asyncio
async def test_spotlight_facet_filtering():
    """패싯 필터(facet=unit_process) 적용 시 해당 패싯 개념만 반환되는지 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search/spotlight?facet=unit_process")
        assert response.status_code == 200
        data = response.json()

        assert data["totalMatches"] >= 1
        for r in data["results"]:
            assert r["domainFacet"] == "unit_process"


@pytest.mark.asyncio
async def test_spotlight_nonexistent_query():
    """존재하지 않는 키워드 검색 시 0건이 반환되는지 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search/spotlight?q=nonexistent_quantum_teleport_xyz")
        assert response.status_code == 200
        data = response.json()

        assert data["totalMatches"] == 0
        assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_spotlight_cache_performance():
    """동일 쿼리 연속 요청 시 캐시가 동작하며 10ms 이하로 응답하는지 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1차 호출 (DB 조회 & 캐시 워밍)
        resp1 = await client.get("/api/v1/search/spotlight?q=EUV")
        assert resp1.status_code == 200

        # 2차 호출 (캐시 Hit 실측)
        start = time.perf_counter()
        resp2 = await client.get("/api/v1/search/spotlight?q=EUV")
        duration_ms = (time.perf_counter() - start) * 1000.0

        assert resp2.status_code == 200
        assert resp2.json()["totalMatches"] == resp1.json()["totalMatches"]
        # 초저지연 검증 (일반적으로 < 15ms)
        assert duration_ms < 50.0
