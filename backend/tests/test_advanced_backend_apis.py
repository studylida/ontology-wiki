"""Unit Tests for Advanced Backend APIs (Comparison clarify/patch/matrix, Deep Research, and Chatbot).

Ensures 100% full compliance with docs/backend_architecture_specification.md Section 4.3, 4.5, and 4.6.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.database import async_session_factory
from backend.app.models.entities import (
    ComparisonSessionModel,
    ResearchSessionModel,
    ReviewTicketModel
)


@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Teardown fixture to clean up temporary sessions/tickets created during tests."""
    yield
    async with async_session_factory() as session:
        # Clean up temporary tickets created by export-ticket, strictly preserving golden seeded tickets
        stmt = select(ReviewTicketModel).where(
            ReviewTicketModel.id.notin_(["rev-20261016-001", "rev-20261015-002"])
        )
        tickets = (await session.execute(stmt)).scalars().all()
        for t in tickets:
            await session.delete(t)

        # Clean up temporary research sessions created by discover, preserving initial session
        stmt2 = select(ResearchSessionModel).where(ResearchSessionModel.id != "res-20261016-01")
        res_sessions = (await session.execute(stmt2)).scalars().all()
        for r in res_sessions:
            await session.delete(r)

        await session.commit()


@pytest.mark.asyncio
async def test_comparison_clarify_success():
    """Test POST /api/v1/comparison/clarify and alias /api/v1/comparison-sessions/clarify."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "query": "HBM3E 16단 적층에서 TCB랑 LAB 어떻게 달라?",
            "customAxes": ["단위 소모 전력 (W/die)"]
        }
        res = await ac.post("/api/v1/comparison/clarify", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "recognizedIntent" in data
        assert len(data["branches"]) == 3
        assert len(data["dynamicAxesPool"]) >= 3
        # Ensure custom axis was added to dynamicAxesPool
        assert any("단위 소모 전력" in ax["label"] for ax in data["dynamicAxesPool"])
        assert len(data["clarificationQuestions"]) == 3

        # Test alias endpoint
        res_alias = await ac.post("/api/v1/comparison-sessions/clarify", json=payload)
        assert res_alias.status_code == 200
        assert res_alias.json()["recognizedIntent"] == data["recognizedIntent"]


@pytest.mark.asyncio
async def test_comparison_clarify_out_of_domain():
    """Test POST /api/v1/comparison/clarify with non-semiconductor query returns 400 with suggested keywords."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/comparison/clarify", json={"query": "오늘 저녁 맛있는 파스타 요리 레시피 추천해줘"})
        assert res.status_code == 400
        data = res.json()
        assert data["detail"]["code"] == "OUT_OF_DOMAIN_QUERY"
        assert len(data["detail"]["suggestedKeywords"]) > 0


@pytest.mark.asyncio
async def test_comparison_patch_session():
    """Test PATCH /api/v1/comparison-sessions/{id} for bookmark pin and title update."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_id = "sess-20261016-001"
        patch_payload = {
            "isPinned": True,
            "title": "HBM3E 16단 방열 대안 분석 (최종 수정본)",
            "folderId": "folder-hbm3e"
        }
        res = await ac.patch(f"/api/v1/comparison-sessions/{session_id}", json=patch_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == session_id
        assert data["isPinned"] is True
        assert data["title"] == "HBM3E 16단 방열 대안 분석 (최종 수정본)"
        assert data["folderId"] == "folder-hbm3e"


@pytest.mark.asyncio
async def test_comparison_matrix_recalculate_and_custom_axis():
    """Test POST /api/v1/comparison-sessions/{id}/matrix for filtering and adding custom axis."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_id = "sess-20261016-001"
        payload = {
            "selectedCategories": ["thermal", "defects"],
            "addedCustomAxis": {
                "name": "CAPEX 설비 개조비",
                "description": "기존 TCB 본더 활용 가능 여부 및 라인 전환 비용"
            }
        }
        res = await ac.post(f"/api/v1/comparison-sessions/{session_id}/matrix", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["sessionId"] == session_id
        assert len(data["matrix"]) > 0
        assert any(row["axis"] == "CAPEX 설비 개조비" for row in data["matrix"])
        assert "aiCausalNote" in data


@pytest.mark.asyncio
async def test_research_sessions_list_and_clarify():
    """Test GET /api/v1/research/sessions and POST /api/v1/research/clarify."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Sessions List
        res_list = await ac.get("/api/v1/research/sessions")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert data_list["totalSessions"] >= 1
        assert len(data_list["sessions"]) >= 1

        # 2. Clarify
        clarify_payload = {
            "searchTopic": "차세대 유리기판 TGV 공정 및 물성 표준 규격"
        }
        res_clarify = await ac.post("/api/v1/research/clarify", json=clarify_payload)
        assert res_clarify.status_code == 200
        data_clarify = res_clarify.json()
        assert "trustPoolNotice" in data_clarify
        assert len(data_clarify["scopeFilters"]) >= 2
        assert len(data_clarify["targetInstitutions"]) >= 3
        assert len(data_clarify["suggestedChips"]) >= 3


@pytest.mark.asyncio
async def test_research_discover_synthesize_and_export_ticket():
    """Test Full Deep Research Pipeline: discover ➔ synthesize ➔ export-ticket."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Discover
        discover_payload = {
            "searchTopic": "차세대 유리기판 TGV 공정 및 물성 표준 규격",
            "targetInstitutions": ["Intel Foundry", "IEEE ECTC", "SEMI 3D Packaging"]
        }
        res_discover = await ac.post("/api/v1/research/discover", json=discover_payload)
        assert res_discover.status_code == 200
        data_discover = res_discover.json()
        session_id = data_discover["sessionId"]
        assert len(data_discover["evidenceFeed"]) >= 3
        assert data_discover["synthesisReady"] is True

        ev_ids = [e["id"] for e in data_discover["evidenceFeed"]]

        # 2. Synthesize
        synth_payload = {
            "selectedEvidenceIds": ev_ids
        }
        res_synth = await ac.post(f"/api/v1/research/sessions/{session_id}/synthesize", json=synth_payload)
        assert res_synth.status_code == 200
        data_synth = res_synth.json()
        assert data_synth["sessionId"] == session_id
        assert len(data_synth["candidates"]) >= 2
        assert "narrativeMarkdown" in data_synth["synthesisReport"]

        # 3. Get session by ID
        res_get = await ac.get(f"/api/v1/research/sessions/{session_id}")
        assert res_get.status_code == 200
        assert res_get.json()["sessionId"] == session_id

        # 4. Export Candidate to Review Ticket
        candidate_id = data_synth["candidates"][0]["candidateId"]
        export_payload = {
            "sessionId": session_id,
            "author": "Dr. 수석연구원",
            "department": "선행패키징연구소",
            "userNote": "Intel/SEMI 공인 백서 교차 검증을 통해 합성된 유리기판 TGV 신규 개념 검토 요청."
        }
        res_export = await ac.post(f"/api/v1/research/candidates/{candidate_id}/export-ticket", json=export_payload)
        assert res_export.status_code == 201
        data_export = res_export.json()
        assert "ticketId" in data_export
        assert data_export["status"] == "pending"


@pytest.mark.asyncio
async def test_chatbot_context_and_3way_routing():
    """Test Chatbot endpoints: context detection and 3-way routing (factoid, action_trigger, causal_clarifier)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Context detection with active concept
        res_ctx = await ac.get("/api/v1/chatbot/context?conceptId=concept-tcb")
        assert res_ctx.status_code == 200
        data_ctx = res_ctx.json()
        assert "열압착 본딩" in data_ctx["conceptTitle"]
        assert len(data_ctx["quickQuestionChips"]) == 3

        # 2. Routing: Factoid (스펙 단답 질의)
        res_fact = await ac.post("/api/v1/chatbot/messages", json={
            "message": "TCB 최대 가압력 스펙이 얼마야?",
            "conceptId": "concept-tcb"
        })
        assert res_fact.status_code == 200
        data_fact = res_fact.json()
        assert data_fact["pathType"] == "factoid"
        assert "180N" in data_fact["answerMarkdown"] or "가압력" in data_fact["answerMarkdown"]

        # 3. Routing: Action Trigger (비교/조사 화면 이동)
        res_act = await ac.post("/api/v1/chatbot/messages", json={
            "message": "TCB랑 LAB 장단점 비교해줘",
            "conceptId": "concept-tcb"
        })
        assert res_act.status_code == 200
        data_act = res_act.json()
        assert data_act["pathType"] == "action_trigger"
        assert data_act["actionCard"] is not None
        assert "/comparison" in data_act["actionCard"]["targetUrl"]

        # 4. Routing: Causal Clarifier (결함/인과 원인 질의)
        res_causal = await ac.post("/api/v1/chatbot/messages", json={
            "message": "식각 챔버에서 아킹이 자꾸 튀는데 원인이 뭐야?",
            "conceptId": "concept-dry-etch"
        })
        assert res_causal.status_code == 200
        data_causal = res_causal.json()
        assert data_causal["pathType"] == "causal_clarifier"
        assert len(data_causal["suggestedNodes"]) >= 1

        # 5. Routing: Out of domain
        res_ood = await ac.post("/api/v1/chatbot/messages", json={
            "message": "내일 비 올까?"
        })
        assert res_ood.status_code == 200
        assert res_ood.json()["pathType"] == "out_of_domain"

        # 6. Reset chat
        res_reset = await ac.delete("/api/v1/chatbot/messages?conceptId=concept-tcb")
        assert res_reset.status_code == 200
        assert res_reset.json()["cleared"] is True
