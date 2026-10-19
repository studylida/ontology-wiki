"""Unit Tests for Group 1 Essential Backend APIs.

Verifies:
1. GET /api/v1/evidences/{id} (Evidence Drawer)
2. GET /api/v1/concepts/tree (Sidebar 4-Facet Tree)
3. POST /api/v1/review-tickets (Wiki Modal Quick Suggestion)
4. POST /api/v1/comparison-sessions/{id}/tune-advisor (Advisor Engine Compensation Rec)
5. POST /api/v1/review-tickets/{id}/directive (Directive Engine Draft Rewriting)
6. PUT /api/v1/review-tickets/{id}/human-edits (In-Place Editor Content Save)
7. GET /api/v1/review-tickets/{id}/wiki-preview (Pre-Approval Wiki Preview Modal)
"""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, delete

from backend.app.main import app
from backend.app.core.cache import cache_manager
from backend.app.core.database import async_session_factory
from backend.app.models.entities import (
    ComparisonSessionModel,
    ReviewTicketModel,
    ConceptModel,
    EvidenceSourceModel
)


@pytest.fixture(autouse=True)
async def setup_and_teardown():
    """Initialize cache and clean up temporary records after test."""
    await cache_manager.init()
    yield
    await cache_manager.close()
    async with async_session_factory() as db:
        await db.execute(
            delete(ReviewTicketModel).where(
                ReviewTicketModel.id.notin_(["rev-20261016-001", "rev-20261015-002"])
            )
        )
        await db.execute(
            delete(ComparisonSessionModel).where(
                ComparisonSessionModel.id != "sess-20261016-001"
            )
        )
        orig_sess = await db.get(ComparisonSessionModel, "sess-20261016-001")
        if orig_sess:
            orig_sess.exported_review_id = "rev-20261016-001"
        await db.commit()


@pytest.mark.asyncio
async def test_get_evidence_detail_success():
    """공인 출처 원문 드로어 서빙 검증."""
    async with async_session_factory() as db:
        ev = (await db.execute(select(EvidenceSourceModel).limit(1))).scalars().first()
        target_id = ev.id if ev else "E-01"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"/api/v1/evidences/{target_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == target_id
        assert "sourceName" in data
        assert "quote" in data
        assert "externalUrl" in data
        assert "credibilityTier" in data


@pytest.mark.asyncio
async def test_get_evidence_detail_not_found():
    """존재하지 않는 출처 조회 시 404 확인."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/evidences/E-NONEXISTENT-999")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_concept_tree():
    """좌측 사이드바 4축 계층형 온톨로지 네비게이션 트리 서빙 검증."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/concepts/tree?facet=unit_process")
        assert res.status_code == 200
        data = res.json()
        assert data["currentFacet"] == "unit_process"
        assert data["totalNodes"] > 0
        assert isinstance(data["tree"], list)
        assert len(data["tree"]) > 0

        first_cat = data["tree"][0]
        assert first_cat["type"] == "category"
        assert "title" in first_cat
        assert len(first_cat["children"]) > 0
        first_concept = first_cat["children"][0]
        assert first_concept["type"] == "concept"
        assert "badge" in first_concept


@pytest.mark.asyncio
async def test_create_review_ticket_via_wiki_modal():
    """위키 본문 간이 제안 모달에서 티켓 신규 발행 검증."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "conceptId": "concept-tcb",
            "title": "TCB 16단 적층 시 NCF 필름 유출 한계 하중 수치 보완 제안",
            "author": "Dr. 김수석",
            "department": "수율분석팀",
            "reviewType": "파라미터 수정",
            "originType": "manual_expert",
            "targetSection": "limitations",
            "userNote": "과도 하중 임계치가 180N이 아닌 165N으로 정정되어야 합니다.",
            "overrideReason": "최신 2026.01 공인 백서 실측 수치 반영"
        }
        res = await ac.post("/api/v1/review-tickets", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["id"].startswith("rev-")
        assert data["conceptId"] == "concept-tcb"
        assert data["author"] == "Dr. 김수석"
        assert data["status"] == "pending"
        assert "165N" in data["aiMergedDraft"]


@pytest.mark.asyncio
async def test_tune_advisor_workflow():
    """AI 파라미터 튜닝 상담 모달: 위험 감지 및 보상안 역제안 & 자동 반영 검증."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 튜닝 상담 요청 (조작 불가 제약 질문)
        req_payload = {
            "userPrompt": "우리 라인 장비 한계로 본딩 가압력을 150N 이상 못 주는데 어떻게 조정하지?",
            "applyCompensation": "compensationA"
        }
        res = await ac.post("/api/v1/comparison-sessions/sess-20261016-001/tune-advisor", json=req_payload)
        assert res.status_code == 200
        data = res.json()

        assert "riskDetected" in data
        assert "advisorRecommendation" in data
        assert "compensationA" in data["advisorRecommendation"]
        assert "compensationB" in data["advisorRecommendation"]
        assert "appliedResult" in data
        assert data["appliedResult"]["appliedPlan"] == "compensationA"
        assert "updatedConditions" in data["appliedResult"]

        # 세션 조회하여 tuningHistory에 누적되었는지 확인
        detail_res = await ac.get("/api/v1/comparison-sessions/sess-20261016-001")
        step2 = detail_res.json()["snapshots"][1]
        assert len(step2["tuningHistory"]) >= 1


@pytest.mark.asyncio
async def test_review_ticket_directive_and_human_edits_and_preview():
    """검토 센터: 전문가 지시문 반영, 직접 편집 저장, 위키 미리보기 전체 플로우 검증."""
    ticket_id = f"rev-flow-{uuid.uuid4().hex[:6]}"
    async with async_session_factory() as db:
        ticket = ReviewTicketModel(
            id=ticket_id,
            concept_id="concept-tcb",
            concept_title="열압착 본딩 (TCB)",
            title="[테스트] TCB 검토 플로우",
            review_type="파라미터 수정",
            author="test_eng",
            status="pending",
            current_version="v1.2",
            target_version="v1.3",
            current_content="기존 TCB 요약문",
            ai_merged_draft="초기 AI 초안입니다.",
            integrity_report={"evidence_match_rate": 0.9, "has_ontology_conflict": False, "impact_scope_count": 1}
        )
        db.add(ticket)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 전문가 지시문 전송 (POST /directive)
        dir_payload = {
            "directiveText": "Scale 2 실리콘 관통전극(TSV) 계면 응력 연계를 추가해줘.",
            "overrideReason": "IEEE ECTC 2026 실측 반영"
        }
        res_dir = await ac.post(f"/api/v1/review-tickets/{ticket_id}/directive", json=dir_payload)
        assert res_dir.status_code == 200
        data_dir = res_dir.json()
        assert "TSV" in data_dir["aiMergedDraft"]
        assert len(data_dir["directiveHistory"]) == 1

        # 2. 전문가 직접 편집 저장 (PUT /human-edits)
        edit_payload = {
            "ticketVersion": 1,
            "editedContent": "전문가가 직접 수정한 최종 정밀 본문입니다."
        }
        res_edit = await ac.put(f"/api/v1/review-tickets/{ticket_id}/human-edits", json=edit_payload)
        assert res_edit.status_code == 200
        data_edit = res_edit.json()
        assert data_edit["ticketVersion"] == 2
        assert "전문가가 직접 수정한" in data_edit["humanEdits"]

        # 3. 위키 페이지 승인 반영 미리보기 (GET /wiki-preview)
        res_prev = await ac.get(f"/api/v1/review-tickets/{ticket_id}/wiki-preview?highlightChanges=true")
        assert res_prev.status_code == 200
        data_prev = res_prev.json()
        assert data_prev["ticketId"] == ticket_id
        assert data_prev["targetVersion"] == "v1.3"
        assert "<mark class=\"diff-added\">" in data_prev["previewConcept"]["summary"]
        assert data_prev["diffSummary"]["status"] == "preview"
