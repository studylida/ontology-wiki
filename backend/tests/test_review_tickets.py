"""Tests for Step 3-4: Review Tickets and Knowledge Governance API.

Covers:
- GET /api/v1/review-tickets (Listing and filtering)
- GET /api/v1/review-tickets/{id} (2-Segment draft, integrity report, presence lock)
- POST /api/v1/review-tickets/{id}/presence (Distributed non-blocking presence lock workflow)
- POST /api/v1/review-tickets/{id}/approve (WORM Merkle audit log, concept version inheritance, reason preservation)
- POST /api/v1/review-tickets/{id}/reject (Rejection with immutable audit trail)
- GET /api/v1/review-tickets/{id}/audit-logs (Merkle hash verification)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, delete

from backend.app.main import app
from backend.app.core.database import async_session_factory
from backend.app.models.entities import ReviewTicketModel, ConceptModel, AuditLogModel
from backend.app.core.cache import cache_manager


@pytest.fixture(autouse=True)
async def setup_and_restore_seed_state():
    """Backup core seed concepts before test and clean up temporary test tickets after test."""
    await cache_manager.init()
    backup_concepts = {}
    async with async_session_factory() as db:
        for cid in ["concept-tcb", "concept-cryo-etch"]:
            c = await db.get(ConceptModel, cid)
            if c:
                backup_concepts[cid] = (c.version, c.summary)

    yield

    await cache_manager.close()
    async with async_session_factory() as db:
        # 1. 임시 테스트 티켓 및 감사 로그 정리
        await db.execute(delete(ReviewTicketModel).where(ReviewTicketModel.id.notin_(["rev-20261016-001", "rev-20261015-002"])))
        await db.execute(delete(AuditLogModel).where(AuditLogModel.ticket_id.notin_(["rev-20261016-001", "rev-20261015-002"])))
        # 2. 시드 개념 원본 복원
        for cid, (orig_ver, orig_sum) in backup_concepts.items():
            c = await db.get(ConceptModel, cid)
            if c:
                c.version = orig_ver
                c.summary = orig_sum
        await db.commit()


@pytest.mark.asyncio
async def test_list_review_tickets():
    """티켓 목록 조회 및 필터링 테스트."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/review-tickets")
        assert res.status_code == 200
        tickets = res.json()
        assert isinstance(tickets, list)
        assert len(tickets) >= 2

        # status 필터링
        res_pending = await ac.get("/api/v1/review-tickets?status=pending")
        assert res_pending.status_code == 200
        for t in res_pending.json():
            assert t["status"] == "pending"


@pytest.mark.asyncio
async def test_get_review_ticket_detail():
    """티켓 상세 조회: 2-Segment 초안, 정합성 보고서, 사유 필드 및 presence lock 상태 확인."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/review-tickets/rev-20261016-001")
        assert res.status_code == 200
        data = res.json()

        assert data["id"] == "rev-20261016-001"
        assert data["conceptId"] == "concept-tcb"
        assert "currentContent" in data
        assert "aiMergedDraft" in data
        assert "integrityReport" in data
        assert "evidenceMatchRate" in data["integrityReport"]
        assert "isLocked" in data
        assert "currentEditor" in data
        # 🌟 도메인 필수 용어: 사유 / overrideReason 탑재 확인
        assert "overrideReason" in data


@pytest.mark.asyncio
async def test_get_review_ticket_not_found():
    """존재하지 않는 티켓 조회 시 404 확인."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/review-tickets/rev-non-existent-999")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_presence_lock_workflow():
    """동시 편집 사전 차단 Presence Lock 전체 워크플로우 검증."""
    ticket_id = "rev-20261016-001"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 초기 락 상태 확인
        status_res = await ac.post(
            f"/api/v1/review-tickets/{ticket_id}/presence",
            json={"userId": "user_alpha", "action": "status"}
        )
        assert status_res.status_code == 200

        # 기존 잔여 락 정리
        await cache_manager.release_presence_lock(ticket_id, "user_alpha")
        await cache_manager.release_presence_lock(ticket_id, "user_beta")

        # 2. 엔지니어 Alpha가 편집 락 획득 (acquire)
        res_alpha = await ac.post(
            f"/api/v1/review-tickets/{ticket_id}/presence",
            json={"userId": "user_alpha", "action": "acquire", "ttlSeconds": 30}
        )
        assert res_alpha.status_code == 200
        data_alpha = res_alpha.json()
        assert data_alpha["acquired"] is True
        assert data_alpha["holder"] == "user_alpha"
        assert data_alpha["isLocked"] is True

        # 3. 다른 엔지니어 Beta가 동시 진입 시도시 차단 확인
        res_beta = await ac.post(
            f"/api/v1/review-tickets/{ticket_id}/presence",
            json={"userId": "user_beta", "action": "acquire", "ttlSeconds": 30}
        )
        assert res_beta.status_code == 200
        data_beta = res_beta.json()
        assert data_beta["acquired"] is False
        assert data_beta["holder"] == "user_alpha"
        assert "편집 중입니다" in data_beta["message"]

        # 4. 티켓 상세 조회 시 isLocked=True, currentEditor='user_alpha' 노출 확인
        detail_res = await ac.get(f"/api/v1/review-tickets/{ticket_id}")
        assert detail_res.json()["isLocked"] is True
        assert detail_res.json()["currentEditor"] == "user_alpha"

        # 5. 엔지니어 Alpha가 락 유지 시간 연장 (renew)
        renew_res = await ac.post(
            f"/api/v1/review-tickets/{ticket_id}/presence",
            json={"userId": "user_alpha", "action": "renew", "ttlSeconds": 45}
        )
        assert renew_res.status_code == 200
        assert renew_res.json()["acquired"] is True

        # 6. 엔지니어 Alpha가 편집 완료 후 락 안전 해제 (release)
        release_res = await ac.post(
            f"/api/v1/review-tickets/{ticket_id}/presence",
            json={"userId": "user_alpha", "action": "release"}
        )
        assert release_res.status_code == 200
        assert release_res.json()["acquired"] is False

        # 7. 이제 엔지니어 Beta가 락을 정상 획득 가능
        res_beta_retry = await ac.post(
            f"/api/v1/review-tickets/{ticket_id}/presence",
            json={"userId": "user_beta", "action": "acquire", "ttlSeconds": 30}
        )
        assert res_beta_retry.status_code == 200
        assert res_beta_retry.json()["acquired"] is True
        assert res_beta_retry.json()["holder"] == "user_beta"

        # 뒷정리
        await cache_manager.release_presence_lock(ticket_id, "user_beta")


@pytest.mark.asyncio
async def test_approve_review_ticket_with_merkle_worm_audit():
    """승인 집행: WORM 머클 해시 감사 로그 생성, 온톨로지 개념 버전 승계 및 Presence 해제 검증."""
    import uuid
    ticket_id = f"rev-test-merkle-{uuid.uuid4().hex[:6]}"
    async with async_session_factory() as db:
        # 독립적인 테스트용 티켓 생성
        test_ticket = ReviewTicketModel(
            id=ticket_id,
            concept_id="concept-tcb",
            concept_title="열압착 본딩 (TCB)",
            title="[테스트] TCB 16단 양산 가압력 보정안 승인 검증",
            review_type="parameter_compensation",
            author="test_eng",
            department="패키징개발",
            status="pending",
            current_version="v1.2",
            target_version="v1.3",
            current_content="기존 TCB 본딩 요약문입니다.",
            ai_merged_draft="AI 생성 가압력 최적화 초안: 145N 초음파 인가 조건 확정.",
            human_edits="엔지니어 최종 수정안: 145N 가압 시 솔더 쇼트율 0.02% 이하 검증 완료.",
            integrity_report={"evidence_match_rate": 0.98, "has_ontology_conflict": False, "impact_scope_count": 2},
            override_reason="Lam Research 공인 실측 데이터와 100% 일치 확인"
        )
        db.add(test_ticket)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 승인 전 락 설정
        await cache_manager.acquire_presence_lock(ticket_id, "approver_park", ttl_seconds=30)

        # 승인 요청 실행
        approve_payload = {
            "approvedBy": "approver_park",
            "overrideReason": "IEEE Transactions 실측 검증 완료 및 파일럿 라인 수율 99.8% 달성 확인",
            "targetVersion": "v1.3",
            "humanEdits": "최종 승인본: 16단 적층 시 145N 최적 가압력 및 초음파 보상 확정 적용."
        }
        res = await ac.post(f"/api/v1/review-tickets/{ticket_id}/approve", json=approve_payload)
        assert res.status_code == 200
        data = res.json()

        # 응답 기본 검증
        assert data["ticket"]["status"] == "approved"
        assert data["ticket"]["approvedBy"] == "approver_park"
        assert data["conceptUpdated"] is True
        assert data["conceptVersion"] == "v1.3"

        # WORM 머클 감사 로그 검증
        audit_log = data["auditLog"]
        assert audit_log is not None
        assert audit_log["ticketId"] == ticket_id
        assert audit_log["actionType"] == "approve"
        assert len(audit_log["entryHash"]) == 64  # SHA-256
        assert len(audit_log["previousLogHash"]) == 64
        assert audit_log["digitalSignature"] is not None

        # Presence Lock 자동 해제 검증
        holder = await cache_manager.get_presence_holder(ticket_id)
        assert holder is None

    # DB 실제 반영 상태 직접 확인
    async with async_session_factory() as db:
        concept = await db.get(ConceptModel, "concept-tcb")
        assert concept is not None
        assert concept.version == "v1.3"
        assert "최종 승인본" in concept.summary


@pytest.mark.asyncio
async def test_approve_with_expert_reason_preserves_and_provides_guide():
    """'전문가 사유' 텍스트 포함 승인 시 400 차단 없이 보존하며 친절 가이드 팁 서빙 검증."""
    import uuid
    ticket_id = f"rev-test-guide-{uuid.uuid4().hex[:6]}"
    async with async_session_factory() as db:
        ticket = ReviewTicketModel(
            id=ticket_id,
            concept_id="concept-cryo-etch",
            concept_title="극저온 식각 (Cryo Etch)",
            title="[테스트] 극저온 식각 파라미터 개정",
            review_type="edge_tuning",
            author="eng_choi",
            status="pending",
            current_version="v1.1",
            target_version="v1.2",
            current_content="기존 극저온 식각",
            ai_merged_draft="AI 초안: 헬륨 냉각 압력 보정",
            integrity_report={"evidence_match_rate": 0.95, "has_ontology_conflict": False, "impact_scope_count": 1}
        )
        db.add(ticket)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "approvedBy": "approver_lee",
            "overrideReason": "전문가 사유에 근거하여 300단 낸드 채널 홀 프로파일 개선 확정"
        }
        res = await ac.post(f"/api/v1/review-tickets/{ticket_id}/approve", json=payload)
        assert res.status_code == 200
        data = res.json()

        # 400으로 튕겨나가지 않고 정상 승인 처리됨
        assert data["ticket"]["status"] == "approved"
        # 사유가 그대로 보존됨
        assert "전문가 사유에 근거하여" in data["ticket"]["overrideReason"]
        # 친절 가이드 팁 안내 포함
        assert data["guideTip"] is not None
        assert "💡 안내:" in data["guideTip"]


@pytest.mark.asyncio
async def test_reject_review_ticket():
    """반려 처리 및 WORM 감사 로그 기록 검증."""
    import uuid
    ticket_id = f"rev-test-reject-{uuid.uuid4().hex[:6]}"
    async with async_session_factory() as db:
        ticket = ReviewTicketModel(
            id=ticket_id,
            concept_id="concept-tcb",
            concept_title="열압착 본딩 (TCB)",
            title="[테스트] 결함 임계치 미달 티켓",
            review_type="edge_tuning",
            author="eng_jung",
            status="pending",
            current_version="v1.2",
            target_version="v1.3",
            current_content="기존 TCB",
            ai_merged_draft="미검증 초안",
            integrity_report={"evidence_match_rate": 0.60, "has_ontology_conflict": True, "impact_scope_count": 5}
        )
        db.add(ticket)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "rejectedBy": "reviewer_senior",
            "rejectReason": "공인 백서 실측 수치와의 오차가 40% 이상으로 데이터 신뢰성 부족"
        }
        res = await ac.post(f"/api/v1/review-tickets/{ticket_id}/reject", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["ticket"]["status"] == "rejected"
        assert data["conceptUpdated"] is False
        assert "반려 처리되었습니다" in data["message"]

        # 감사 로그 확인
        audit_res = await ac.get(f"/api/v1/review-tickets/{ticket_id}/audit-logs")
        assert audit_res.status_code == 200
        logs = audit_res.json()
        assert len(logs) >= 1
        assert logs[-1]["actionType"] == "reject"
        assert logs[-1]["governanceSnapshot"]["rejectReason"] == payload["rejectReason"]

