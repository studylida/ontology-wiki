"""Review Tickets and Knowledge Governance REST API.

Provides:
- GET /api/v1/review-tickets (List & filter governance tickets)
- GET /api/v1/review-tickets/{id} (Ticket detail with 2-segment draft, integrity report, presence lock status)
- POST /api/v1/review-tickets/{id}/presence (Pre-edit distributed presence lock)
- POST /api/v1/review-tickets/{id}/approve (Approve ticket, WORM merkle-audit log, concept version inheritance)
- POST /api/v1/review-tickets/{id}/reject (Reject ticket with immutable audit record)
- GET /api/v1/review-tickets/{id}/audit-logs (Audit log trail with Merkle verification)
"""
import uuid
import json
import hmac
import hashlib
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.cache import cache_manager
from backend.app.models.entities import ReviewTicketModel, AuditLogModel, ConceptModel
from backend.app.schemas.review import (
    ReviewTicketDTO,
    ReviewTicketDetailDTO,
    AuditLogDTO,
    PresenceLockRequest,
    PresenceLockResponse,
    ReviewTicketApproveRequest,
    ReviewTicketRejectRequest,
    ReviewTicketActionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/review-tickets",
    tags=["Review & Governance"]
)


def _convert_ticket_to_dto(ticket: ReviewTicketModel) -> ReviewTicketDTO:
    """Helper to convert ReviewTicketModel to ReviewTicketDTO with proper ISO dates."""
    return ReviewTicketDTO(
        id=ticket.id,
        concept_id=ticket.concept_id,
        concept_title=ticket.concept_title,
        title=ticket.title,
        review_type=ticket.review_type,
        author=ticket.author,
        department=ticket.department,
        submitted_at=ticket.submitted_at.isoformat() if ticket.submitted_at else None,
        status=ticket.status,
        source_session_id=ticket.source_session_id,
        origin_type=ticket.origin_type,
        current_version=ticket.current_version,
        target_version=ticket.target_version,
        current_content=ticket.current_content,
        ai_merged_draft=ticket.ai_merged_draft,
        human_edits=ticket.human_edits,
        structured_patches=ticket.structured_patches or {},
        integrity_report=ticket.integrity_report or {},
        directive_history=ticket.directive_history or [],
        override_reason=ticket.override_reason,
        approved_at=ticket.approved_at.isoformat() if ticket.approved_at else None,
        approved_by=ticket.approved_by,
        applied_concept_version=ticket.applied_concept_version,
        ticket_version=ticket.ticket_version
    )


def _convert_audit_to_dto(audit: AuditLogModel) -> AuditLogDTO:
    """Helper to convert AuditLogModel to AuditLogDTO."""
    return AuditLogDTO(
        audit_id=audit.audit_id,
        ticket_id=audit.ticket_id,
        concept_id=audit.concept_id,
        action_type=audit.action_type,
        actor=audit.actor or {},
        governance_snapshot=audit.governance_snapshot or {},
        previous_log_hash=audit.previous_log_hash,
        entry_hash=audit.entry_hash,
        digital_signature=audit.digital_signature,
        timestamp=audit.timestamp.isoformat() if audit.timestamp else None
    )


@router.get(
    "",
    response_model=List[ReviewTicketDTO],
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="지식 거버넌스 티켓 목록 조회 API",
    description="상태(status) 및 대상 개념(conceptId) 필터링과 최신순 정렬을 지원하는 티켓 목록 API입니다."
)
async def list_review_tickets(
    status: Optional[str] = Query(None, description="상태 필터 ('pending', 'approved', 'rejected')"),
    concept_id: Optional[str] = Query(None, alias="conceptId", description="대상 개념 ID 필터"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ReviewTicketModel)
    if status:
        stmt = stmt.where(ReviewTicketModel.status == status)
    if concept_id:
        stmt = stmt.where(ReviewTicketModel.concept_id == concept_id)

    stmt = stmt.order_by(
        ReviewTicketModel.submitted_at.desc(),
        ReviewTicketModel.created_at.desc()
    ).limit(limit).offset(offset)

    tickets = (await db.execute(stmt)).scalars().all()
    return [_convert_ticket_to_dto(t) for t in tickets]


@router.get(
    "/{ticket_id}",
    response_model=ReviewTicketDetailDTO,
    response_model_by_alias=True,
    summary="지식 거버넌스 티켓 상세 조회 API",
    description="2-Segment 개정 초안, 정합성 점검 보고서, 지시문 이력 및 현재 동시 편집자 락 상태를 서빙합니다."
)
async def get_review_ticket_detail(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    # Redis / In-Memory Presence Lock 점유자 확인
    current_editor = await cache_manager.get_presence_holder(ticket_id)
    base_dto = _convert_ticket_to_dto(ticket)

    return ReviewTicketDetailDTO(
        **base_dto.model_dump(by_alias=False),
        current_editor=current_editor,
        is_locked=bool(current_editor)
    )


@router.post(
    "/{ticket_id}/presence",
    response_model=PresenceLockResponse,
    response_model_by_alias=True,
    summary="동시 편집 사전 차단 Presence Lock API",
    description="티켓 진입 시 편집 충돌을 사전 방지하기 위해 비차단 락을 획득/갱신/해제합니다."
)
async def manage_presence_lock(
    ticket_id: str,
    body: PresenceLockRequest,
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    action = body.action
    user_id = body.userId
    ttl = body.ttlSeconds

    if action == "acquire":
        success = await cache_manager.acquire_presence_lock(ticket_id, user_id, ttl_seconds=ttl)
        holder = await cache_manager.get_presence_holder(ticket_id)
        if success:
            return PresenceLockResponse(
                acquired=True,
                holder=user_id,
                is_locked=True,
                message=f"티켓 [{ticket_id}]의 편집 락을 성공적으로 획득했습니다 (TTL: {ttl}초)."
            )
        else:
            return PresenceLockResponse(
                acquired=False,
                holder=holder,
                is_locked=True,
                message=f"현재 '{holder}' 엔지니어가 편집 중입니다. 충돌 방지를 위해 읽기 전용으로 유지됩니다."
            )

    elif action == "renew":
        holder = await cache_manager.get_presence_holder(ticket_id)
        if holder == user_id:
            await cache_manager.acquire_presence_lock(ticket_id, user_id, ttl_seconds=ttl)
            return PresenceLockResponse(
                acquired=True,
                holder=user_id,
                is_locked=True,
                message=f"편집 락 유지 시간이 {ttl}초로 연장되었습니다."
            )
        else:
            return PresenceLockResponse(
                acquired=False,
                holder=holder,
                is_locked=bool(holder),
                message="락 소유권이 없거나 이미 만료되었습니다."
            )

    elif action == "release":
        success = await cache_manager.release_presence_lock(ticket_id, user_id)
        current_holder = await cache_manager.get_presence_holder(ticket_id)
        return PresenceLockResponse(
            acquired=False,
            holder=current_holder,
            is_locked=bool(current_holder),
            message="편집 락이 안전하게 해제되었습니다." if success else "락 소유자가 아니거나 이미 해제된 상태입니다."
        )

    elif action == "status":
        holder = await cache_manager.get_presence_holder(ticket_id)
        return PresenceLockResponse(
            acquired=(holder == user_id),
            holder=holder,
            is_locked=bool(holder),
            message=f"현재 점유자: {holder or '점유 없음'}"
        )

    raise HTTPException(status_code=400, detail=f"지원하지 않는 액션입니다: {action}")


@router.post(
    "/{ticket_id}/approve",
    response_model=ReviewTicketActionResponse,
    response_model_by_alias=True,
    summary="지식 거버넌스 승인 집행 API",
    description="WORM 불변 머클 해시 감사 로그를 기록하고, 온톨로지 개념 및 버전을 영구 승계 반영합니다."
)
async def approve_review_ticket(
    ticket_id: str,
    body: ReviewTicketApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    now_utc = datetime.utcnow()
    final_reason = body.overrideReason or ticket.override_reason or ""

    # UX 친절 안내: "전문가 사유"와 같은 주관적 단어가 들어있더라도 차단하지 않고 안전 저장하며 팁 안내
    guide_tip = None
    if "전문가 사유" in final_reason:
        guide_tip = "💡 안내: 표준 승인 절차를 위해 '전문가 사유' 대신 정량적 공인 백서/실측 수치를 명시해 주시면 거버넌스 품질 신뢰도가 한층 높아집니다."

    # 1. 이전 최신 감사 로그 조회 (머클 해시 체인 연결)
    latest_audit_stmt = select(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(1)
    latest_audit = (await db.execute(latest_audit_stmt)).scalars().first()
    previous_log_hash = latest_audit.entry_hash if latest_audit else "0" * 64

    # 2. WORM 감사 로그 데이터 조립
    audit_id = f"aud-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    actor_info = {
        "userId": body.approvedBy,
        "role": "DomainGovernanceApprover",
        "action": "approve"
    }
    applied_ver = body.targetVersion or ticket.target_version or "v1.3"
    gov_snapshot = {
        "ticketId": ticket.id,
        "conceptId": ticket.concept_id,
        "conceptTitle": ticket.concept_title,
        "appliedVersion": applied_ver,
        "previousVersion": ticket.current_version,
        "overrideReason": final_reason,
        "integrityReport": ticket.integrity_report or {},
        "humanEditsSummary": (body.humanEdits or ticket.human_edits or "")[:200]
    }

    # Merkle SHA-256 Entry Hash 계산
    raw_hash_source = f"{previous_log_hash}|{audit_id}|{ticket.id}|approve|{json.dumps(actor_info, sort_keys=True)}|{json.dumps(gov_snapshot, sort_keys=True)}|{now_utc.isoformat()}"
    entry_hash = hashlib.sha256(raw_hash_source.encode("utf-8")).hexdigest()

    # HMAC 디지털 서명
    digital_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        entry_hash.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # 감사 로그 저장
    audit_entry = AuditLogModel(
        audit_id=audit_id,
        ticket_id=ticket.id,
        concept_id=ticket.concept_id,
        action_type="approve",
        actor=actor_info,
        governance_snapshot=gov_snapshot,
        previous_log_hash=previous_log_hash,
        entry_hash=entry_hash,
        digital_signature=digital_sig,
        timestamp=now_utc
    )
    db.add(audit_entry)

    # 3. 티켓 상태 갱신
    ticket.status = "approved"
    ticket.approved_at = now_utc
    ticket.approved_by = body.approvedBy
    ticket.applied_concept_version = applied_ver
    if body.humanEdits:
        ticket.human_edits = body.humanEdits
    if body.overrideReason:
        ticket.override_reason = body.overrideReason
    ticket.updated_at = now_utc

    # 4. 온톨로지 개념(ConceptModel) 본문 및 버전 영구 승계
    concept = await db.get(ConceptModel, ticket.concept_id)
    concept_updated = False
    if concept:
        concept.version = applied_ver
        if ticket.human_edits:
            concept.summary = ticket.human_edits
        elif ticket.ai_merged_draft:
            concept.summary = ticket.ai_merged_draft
        concept.updated_at = now_utc
        concept_updated = True

    # 5. Presence Lock 자동 해제
    await cache_manager.release_presence_lock(ticket.id, body.approvedBy)

    await db.commit()
    await db.refresh(ticket)
    await db.refresh(audit_entry)

    # 6. Stale Cache 방지를 위한 연관 캐시 즉시 무효화 (위키 상세 / 서브그래프 / 문맥해설 / 전역검색)
    await cache_manager.delete(f"concept:detail:{ticket.concept_id}")
    await cache_manager.delete_prefix(f"concept:subgraph:{ticket.concept_id}:")
    await cache_manager.delete_prefix(f"concept:explainer:{ticket.concept_id}:")
    await cache_manager.delete_prefix("spotlight:")

    return ReviewTicketActionResponse(
        ticket=_convert_ticket_to_dto(ticket),
        audit_log=_convert_audit_to_dto(audit_entry),
        concept_updated=concept_updated,
        concept_version=applied_ver,
        guide_tip=guide_tip,
        message=f"거버넌스 티켓 [{ticket.id}]이(가) 공식 승인되었으며, 개념 '{ticket.concept_title}'이(가) {applied_ver} 버전으로 영구 승계되었습니다."
    )


@router.post(
    "/{ticket_id}/reject",
    response_model=ReviewTicketActionResponse,
    response_model_by_alias=True,
    summary="지식 거버넌스 반려 API",
    description="반려 사유와 함께 WORM 불변 감사 로그를 기록하고 티켓을 반려 처리합니다."
)
async def reject_review_ticket(
    ticket_id: str,
    body: ReviewTicketRejectRequest,
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    now_utc = datetime.utcnow()

    # 머클 해시 체인 연결
    latest_audit_stmt = select(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(1)
    latest_audit = (await db.execute(latest_audit_stmt)).scalars().first()
    previous_log_hash = latest_audit.entry_hash if latest_audit else "0" * 64

    audit_id = f"aud-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    actor_info = {
        "userId": body.rejectedBy,
        "role": "DomainGovernanceReviewer",
        "action": "reject"
    }
    gov_snapshot = {
        "ticketId": ticket.id,
        "conceptId": ticket.concept_id,
        "rejectReason": body.rejectReason,
        "previousVersion": ticket.current_version
    }

    raw_hash_source = f"{previous_log_hash}|{audit_id}|{ticket.id}|reject|{json.dumps(actor_info, sort_keys=True)}|{json.dumps(gov_snapshot, sort_keys=True)}|{now_utc.isoformat()}"
    entry_hash = hashlib.sha256(raw_hash_source.encode("utf-8")).hexdigest()

    digital_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        entry_hash.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    audit_entry = AuditLogModel(
        audit_id=audit_id,
        ticket_id=ticket.id,
        concept_id=ticket.concept_id,
        action_type="reject",
        actor=actor_info,
        governance_snapshot=gov_snapshot,
        previous_log_hash=previous_log_hash,
        entry_hash=entry_hash,
        digital_signature=digital_sig,
        timestamp=now_utc
    )
    db.add(audit_entry)

    ticket.status = "rejected"
    ticket.updated_at = now_utc

    # Presence Lock 자동 해제
    await cache_manager.release_presence_lock(ticket.id, body.rejectedBy)

    await db.commit()
    await db.refresh(ticket)
    await db.refresh(audit_entry)

    return ReviewTicketActionResponse(
        ticket=_convert_ticket_to_dto(ticket),
        audit_log=_convert_audit_to_dto(audit_entry),
        concept_updated=False,
        concept_version=ticket.current_version,
        guide_tip=None,
        message=f"거버넌스 티켓 [{ticket.id}]이(가) 반려 처리되었습니다. 반려 사유: {body.rejectReason}"
    )


@router.get(
    "/{ticket_id}/audit-logs",
    response_model=List[AuditLogDTO],
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="티켓 WORM 감사 로그 이력 조회 API",
    description="머클 해시 체인으로 보호되는 티켓의 불변 거버넌스 감사 로그 이력을 조회합니다."
)
async def get_ticket_audit_logs(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    stmt = (
        select(AuditLogModel)
        .where(AuditLogModel.ticket_id == ticket_id)
        .order_by(AuditLogModel.id.asc())
    )
    audit_logs = (await db.execute(stmt)).scalars().all()
    return [_convert_audit_to_dto(a) for a in audit_logs]
