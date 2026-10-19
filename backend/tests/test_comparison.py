"""Unit Tests for Comparison Studio Endpoints (/api/v1/comparison-sessions).

Verifies:
1. GET  /api/v1/comparison-sessions - List sessions
2. GET  /api/v1/comparison-sessions/{id} - Detail with snapshots, deepDiveHistory, tuningHistory
3. POST /api/v1/comparison-sessions - Create new session with 3-Step template
4. POST /api/v1/comparison-sessions/{id}/deep-dive - 4-step causal chain tail-question registration
5. POST /api/v1/comparison-sessions/{id}/export-review - Forbidden phrase ('전문가 사유') 400 rejection
6. POST /api/v1/comparison-sessions/{id}/export-review - Success with standard overrideReason
"""
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.cache import cache_manager


@pytest.fixture(autouse=True)
async def setup_cache():
    """Ensure in-memory/redis cache manager is initialized for testing."""
    await cache_manager.init()
    yield
    await cache_manager.close()


@pytest.mark.asyncio
async def test_list_comparison_sessions():
    """비교 세션 목록 조회 API 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/comparison-sessions")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1
        first = data[0]
        assert "id" in first
        assert "title" in first
        assert "isPinned" in first
        assert "query" in first
        assert "snapshots" in first


@pytest.mark.asyncio
async def test_get_comparison_session_detail():
    """시딩된 세션(sess-20261016-001) 상세 및 꼬리질문(deepDiveHistory), 보상파라미터 튜닝 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/comparison-sessions/sess-20261016-001")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "sess-20261016-001"
        assert "snapshots" in data
        snapshots = data["snapshots"]
        assert len(snapshots) >= 3

        # 🌟 도메인 필수 검증: Step 2 tuningHistory (보상 파라미터 튜닝)
        step2 = next((s for s in snapshots if s.get("step") == 2), None)
        assert step2 is not None
        assert "tuningHistory" in step2
        assert len(step2["tuningHistory"]) >= 1

        # 🌟 도메인 필수 검증: Step 3 deepDiveHistory (꼬리질문 이력 및 4단계 인과체인)
        step3 = next((s for s in snapshots if s.get("step") == 3), None)
        assert step3 is not None
        assert "deepDiveHistory" in step3
        assert len(step3["deepDiveHistory"]) >= 1
        tail_q = step3["deepDiveHistory"][0]
        assert "query" in tail_q
        assert "causalPath" in tail_q
        assert len(tail_q["causalPath"]) == 4
        assert tail_q["causalPath"] == ["가압력 누적", "CTE 미스매치", "전단응력", "다이 휨"]


@pytest.mark.asyncio
async def test_create_comparison_session():
    """신규 비교 세션 생성 및 3-Step 스냅샷 템플릿 초기화 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "High-NA EUV vs 기존 0.33NA 노광 공정 비교",
            "userId": "EMP-DEV-001",
            "query": "2nm GAA 패터닝에서 High-NA 도입 시 수율 및 마스크 비용 비교",
            "contextParams": {
                "targetA": "High-NA EUV (0.55NA)",
                "targetB": "Standard EUV (0.33NA Double Patterning)",
                "domain": "노광 공정"
            }
        }
        response = await client.post("/api/v1/comparison-sessions", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["title"] == payload["title"]
        assert len(data["snapshots"]) == 3
        assert data["snapshots"][0]["step"] == 1
        assert data["snapshots"][1]["step"] == 2
        assert data["snapshots"][2]["step"] == 3


@pytest.mark.asyncio
async def test_add_deep_dive_tail_question():
    """엔지니어 꼬리질문(Deep-Dive) 등록 시 4단계 인과 체인 자동 도출 및 스냅샷 누적 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 먼저 새 세션 생성
        sess_resp = await client.post(
            "/api/v1/comparison-sessions",
            json={
                "title": "TCB 휨 불량 인과 분석",
                "userId": "EMP-QA-02",
                "query": "TC-NCF 공정 불량 분석"
            }
        )
        session_id = sess_resp.json()["id"]

        # 꼬리질문 등록
        dive_payload = {
            "query": "가압 공정에서 다이 휨(Warpage)이 일어나는 물리적 원인은 무엇인가?",
            "stepIndex": 2
        }
        response = await client.post(f"/api/v1/comparison-sessions/{session_id}/deep-dive", json=dive_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sessionId"] == session_id
        tail_q = data["tailQuestion"]
        assert tail_q["query"] == dive_payload["query"]
        assert len(tail_q["causalPath"]) == 4
        # 실제 DB 온톨로지 개념(가압력, TCB 등)과 결함/대안 개념이 연결되었는지 검증
        assert any("가압" in p or "본딩" in p or "tcb" in p.lower() or "단락" in p for p in tail_q["causalPath"])
        assert len(tail_q["explanation"]) > 10

        # 세션 조회하여 실제 스냅샷에 반영되었는지 재확인
        check_resp = await client.get(f"/api/v1/comparison-sessions/{session_id}")
        step3 = check_resp.json()["snapshots"][2]
        assert len(step3["deepDiveHistory"]) == 1


@pytest.mark.asyncio
async def test_export_review_with_expert_reason_preserves_and_guides():
    """사용자가 '전문가 사유'를 기재하더라도 400으로 튕겨내지 않고 안전하게 접수하며 권장 팁을 제공하는지 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "conceptId": "concept-tcb",
            "title": "가압 조건 현장 테스트 결과 반영 건",
            "overrideReason": "수석 엔지니어 현장 의견 및 전문가 사유 기반 가압력 미세 조정",
            "author": "Dr. 홍",
            "reviewType": "파라미터 수정"
        }
        response = await client.post("/api/v1/comparison-sessions/sess-20261016-001/export-review", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "ticketId" in data
        assert "성공적으로 내보내졌습니다" in data["message"]
        assert "실측 데이터나 공인 백서 근거를 보완" in data["message"]


@pytest.mark.asyncio
async def test_export_review_success():
    """공인 백서/실측 데이터 근거 표준 사유(overrideReason)를 통한 티켓 내보내기 성공 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "conceptId": "concept-tcb",
            "title": "비교분석 결과 기반 145N 가압 파라미터 완화 승인 요청",
            "overrideReason": "Lam Research 공인 백서 및 16단 파일럿 팹 라인 실측 결과 145N에서 솔더 쇼트율 0.02% 이하 입증",
            "author": "Dr. 박수석",
            "reviewType": "파라미터 수정"
        }
        response = await client.post("/api/v1/comparison-sessions/sess-20261016-001/export-review", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sessionId"] == "sess-20261016-001"
        assert "ticketId" in data
        assert data["ticketId"].startswith("rev-")
        assert "성공적으로 내보내졌습니다" in data["message"]


@pytest.mark.asyncio
async def test_add_deep_dive_multi_domain_generalization():
    """노광, 식각, 소자 등 반도체 전 공정에 걸친 4단계 물리 인과 체인 도출 일반화 검증."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 세션 생성
        sess = await client.post(
            "/api/v1/comparison-sessions",
            json={"title": "반도체 전 공정 인과 테스트", "userId": "EMP-PHYS", "query": "전 공정 비교"}
        )
        sid = sess.json()["id"]

        # 1. 노광 공정 (High-NA EUV)
        res_litho = await client.post(
            f"/api/v1/comparison-sessions/{sid}/deep-dive",
            json={"query": "High-NA EUV 노광 시 초점 심도(DOF) 감소로 인한 스토캐스틱 결함 경로는?"}
        )
        assert res_litho.status_code == 200
        path_litho = res_litho.json()["tailQuestion"]["causalPath"]
        assert len(path_litho) == 4
        assert any("high-na" in p.lower() or "euv" in p.lower() or "노광" in p for p in path_litho)

        # 2. 식각 공정 (Cryo Etch)
        res_etch = await client.post(
            f"/api/v1/comparison-sessions/{sid}/deep-dive",
            json={"query": "극저온 Cryo 식각 공정에서 고종횡비 홀 틸팅(Tilting) 불량 메커니즘은?"}
        )
        assert res_etch.status_code == 200
        path_etch = res_etch.json()["tailQuestion"]["causalPath"]
        assert len(path_etch) == 4
        assert any("식각" in p or "cryo" in p.lower() or "etch" in p.lower() for p in path_etch)

        # 3. 소자 구조 (2nm GAA Nanosheet)
        res_gaa = await client.post(
            f"/api/v1/comparison-sessions/{sid}/deep-dive",
            json={"query": "2nm GAA 나노시트 소자에서 단채널 효과(SCE)로 인한 누설 전류 발생 원인은?"}
        )
        assert res_gaa.status_code == 200
        path_gaa = res_gaa.json()["tailQuestion"]["causalPath"]
        assert len(path_gaa) == 4
        assert any("gaa" in p.lower() or "나노시트" in p.lower() or "채널" in p for p in path_gaa)
