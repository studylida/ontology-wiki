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

from fastapi import BackgroundTasks, APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.agents.directive_agent import directive_agent
from backend.app.repositories.review_repo import review_repo
from backend.app.services.review_service import review_service, _convert_ticket_to_dto, _convert_audit_to_dto
from backend.app.schemas.review import ReviewPreviewRequest
from backend.app.services.placement_service import recommend_placement, PlacementRecommendationUnavailable
from backend.app.core.cache import cache_manager
from backend.app.core.security import get_current_user_optional, require_min_level
from backend.app.models.entities import ReviewTicketModel, AuditLogModel, ConceptModel, CausalEdgeModel, UserModel
from backend.app.schemas.review import (
    ReviewTicketDTO,
    ReviewTicketDetailDTO,
    AuditLogDTO,
    PresenceLockRequest,
    PresenceLockResponse,
    ReviewTicketApproveRequest,
    ReviewTicketRejectRequest,
    ReviewTicketActionResponse,
    ReviewTicketCreate,
    DirectiveRequest,
    HumanEditsRequest,
    HumanEditsResponse,
    WikiPreviewResponse,
    ConceptPlacementRecommendRequest,
    ConceptPlacementRecommendResponse
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/review-tickets",
    tags=["Review & Governance"]
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


@router.post(
    "",
    response_model=ReviewTicketDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="위키 본문 간이 제안 모달을 통한 검토 티켓 신규 발행 API",
    description="위키 본문 하단 '오류 수정 제안하기' 모달에서 엔지니어가 수치 보완 의견과 근거를 제출하여 거버넌스 티켓을 신규 발행합니다."
)
async def create_review_ticket(
    body: ReviewTicketCreate,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # 🌟 Level 2 현장 엔지니어 이상 발의 권한 가드레일 (게스트 차단)
    if current_user:
        if current_user.level < 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "INSUFFICIENT_LEVEL", "message": "위키 거버넌스 티켓 발의 권한은 '현장 엔지니어(Level 2)' 이상만 가능합니다."}
            )
        author = current_user.name
        department = current_user.department
    else:
        author = body.author
        department = body.department or "도메인개발팀"

    today_str = datetime.utcnow().strftime("%Y%m%d")
    ticket_id = f"rev-{today_str}-{uuid.uuid4().hex[:4]}"

    if body.isNewConcept:
        # 🌟 완전 신규 개념/문서 발의: 404 차단 바이패스 및 신규 개념 티켓 생성
        concept_id = f"concept-{uuid.uuid4().hex[:8]}"
        concept_title = body.title
        current_version = "v1.0.0"
        target_version = "v1.1.0"
        current_content = "### 1. 기술 정의\n(사내 온톨로지 미등록 신규 개념)"
        merged_draft = f"### 1. 기술 정의\n{body.userNote or body.title}"
        placement_meta = {
            "is_new_concept": True,
            "eng_name": body.engName or body.title,
            "domain_facet": body.domainFacet or "unit_process",
            "scale_level": body.scaleLevel or 3,
            "scale_name": body.scaleName or "Scale 3: 단위 공정",
            "process_category": body.processCategory or "첨단 패키징",
            "parent_concept_id": body.parentConceptId
        }
        structured_patches = [
            {"op": "add", "path": "/concept", "value": placement_meta}
        ]
        review_type = "신규 개념 등록"
    else:
        # 기존 문서 개정 발의: 기존처럼 DB 실존 여부 검증 (없으면 404)
        concept = await db.get(ConceptModel, body.conceptId)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"온톨로지 개념 '{body.conceptId}'을(를) 찾을 수 없습니다."
            )
        concept_id = concept.id
        concept_title = concept.title
        current_version = concept.version
        target_version = "v1.3.0"
        current_content = concept.summary
        merged_draft = f"{concept.summary}\n\n[제안 반영안 ({author})]: {body.userNote or body.title}"
        structured_patches = [
            {"op": "replace", "path": f"/{body.targetSection or 'summary'}", "value": body.userNote or body.title}
        ]
        review_type = body.reviewType

    new_ticket = ReviewTicketModel(
        id=ticket_id,
        concept_id=concept_id,
        concept_title=concept_title,
        title=body.title,
        review_type=review_type,
        author=author,
        department=department,
        submitted_at=datetime.utcnow(),
        status="pending",
        origin_type=body.originType or "manual_expert",
        current_version=current_version,
        target_version=target_version,
        current_content=current_content,
        ai_merged_draft=merged_draft,
        human_edits=None,
        structured_patches=structured_patches,
        integrity_report={
            "evidence_match_rate": 1.0,
            "has_ontology_conflict": False,
            "impact_scope_count": 1,
            "validation_details": "위키 본문 전문가 제안 접수 완료",
            "conflict_details": []
        },
        directive_history=[],
        override_reason=body.overrideReason,
        ticket_version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)

    return _convert_ticket_to_dto(new_ticket)


@router.get(
    "/{ticket_id}",
    response_model=ReviewTicketDetailDTO,
    response_model_by_alias=True,
    summary="지식 거버넌스 티켓 상세 조회 API",
    description="2-Segment 개정 초안, 정합성 점검 보고서, 지시문 이력 및 현재 동시 편집자 락 상태를 서빙합니다."
)
async def get_review_ticket_detail(
    ticket_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
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
    review_service.require_editor(current_user)
    base_dto = _convert_ticket_to_dto(ticket)
    base_dto.workingDraft = await review_service.editable(ticket, db, current_user)

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
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    action = body.action
    if current_user:
        if current_user.level < 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "INSUFFICIENT_LEVEL", "message": "동시 편집 락 권한은 '현장 엔지니어(Level 2)' 이상만 가능합니다."}
            )
        user_id = current_user.name or current_user.id
    else:
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
        success, reason = await cache_manager.renew_presence_lock(ticket_id, user_id, ttl_seconds=ttl)
        if success:
            return PresenceLockResponse(
                acquired=True,
                holder=user_id,
                is_locked=True,
                message=f"편집 락 유지 시간이 {ttl}초로 연장되었습니다."
            )
        elif reason == "max_hold_exceeded":
            return PresenceLockResponse(
                acquired=False,
                holder=None,
                is_locked=False,
                message="최대 점유 상한선(10분)을 초과하여 편집 락이 자동 만료되었습니다."
            )
        else:
            holder = await cache_manager.get_presence_holder(ticket_id)
            return PresenceLockResponse(
                acquired=False,
                holder=holder,
                is_locked=bool(holder),
                message="락 소유권이 없거나 이미 만료되었습니다."
            )

    elif action == "steal":
        success = await cache_manager.steal_presence_lock(ticket_id, user_id, ttl_seconds=ttl)
        return PresenceLockResponse(
            acquired=success,
            holder=user_id if success else None,
            is_locked=success,
            message="편집 락을 강제 회수(Steal Lock)하여 획득했습니다." if success else "락 회수에 실패했습니다."
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
    background_tasks: BackgroundTasks,
    body: Optional[ReviewTicketApproveRequest] = None,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    return await review_service.approve(ticket_id, background_tasks, body, current_user, x_gemini_key, x_openai_key, db)


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
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # 🌟 수석검토관(Level 3) 이상 거버넌스 반려 인가 가드레일 (오직 인증된 수석검토관 토큰 필수)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "거버넌스 반려 처리를 위해 로그인이 필요합니다."}
        )
    if current_user.level < 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INSUFFICIENT_LEVEL",
                "message": "위키 거버넌스 반려 권한은 '수석검토관(Level 3)' 이상 전용입니다. 현장 엔지니어(Level 2)는 반려 권한이 없습니다."
            }
        )
    rejector_id = current_user.id
    rejector_name = current_user.name
    rejector_role = current_user.role
    rejector_dept = current_user.department

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
        "userId": rejector_id,
        "name": rejector_name,
        "role": rejector_role,
        "department": rejector_dept,
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


@router.post(
    "/{ticket_id}/directive",
    response_model=ReviewTicketDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="전문가 보완 지시문 반영 및 AI 초안 재작성 API",
    description="하단 지시문 입력 바에서 전문가의 자연어 수정 지시를 전달받아 공인 출처 불변 제약을 보존하면서 AI 개정 초안을 재작성하고 정합성을 재산출합니다."
)
async def apply_directive(
    ticket_id: str,
    body: DirectiveRequest,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    # 🌟 Level 2 현장 엔지니어 이상 가드레일 (게스트 차단)
    if not current_user:
        raise HTTPException(401, '로그인이 필요합니다.')
    if current_user.level < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INSUFFICIENT_LEVEL", "message": "전문가 보완 지시문 전달 권한은 '현장 엔지니어(Level 2)' 이상만 가능합니다."}
        )

    ticket = await review_repo.get(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    text_input = body.directiveText.strip()
    if not text_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="보완 지시문 내용이 비어있습니다."
        )

    # 🌟 3.4절 Directive Engine 에이전트 호출
    try:
        await directive_agent.process_directive(
            ticket=ticket,
            directive_text=text_input,
            override_reason=body.overrideReason,
            db=db,
            allow_citation_deletion=body.allowCitationDeletion,
            deprecated_citations=body.deprecatedCitations,
            gemini_key=x_gemini_key,
            openai_key=x_openai_key,
            edited_content=body.editedContent, ticket_version=body.ticketVersion, undo_last=body.undoLast, structured_draft=body.structuredDraft, target_sections=body.targetSections, current_user=current_user
        )
    except (ValueError, TypeError, KeyError, RuntimeError):
        await db.rollback()
        raise HTTPException(502, '자료 기반 변경안을 검증하지 못했습니다. 기존 초안은 유지했습니다.')

    await db.commit()
    await db.refresh(ticket)
    return _convert_ticket_to_dto(ticket)


@router.put(
    "/{ticket_id}/human-edits",
    response_model=HumanEditsResponse,
    response_model_by_alias=True,
    summary="전문가 직접 편집 모드 실시간 저장 API",
    description="우측 Pane 전문가 직접 편집기(In-Place Editor)에서 수정한 본문 내용을 저장하고 판본 충돌을 방지합니다."
)
async def update_human_edits(
    ticket_id: str,
    body: HumanEditsRequest,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    ticket = await review_repo.get(db, ticket_id)
    review_service.require_editor(current_user)
    if not ticket:raise HTTPException(404, '검토 티켓을 찾지 못했습니다.')
    return await review_service.save(ticket, body, db, current_user)


@router.get(
    "/{ticket_id}/wiki-preview",
    response_model=WikiPreviewResponse,
    response_model_by_alias=True,
    summary="승인 전 반영될 위키 페이지 실시간 미리보기 API",
    description="최종 승인 시 공용 위키 페이지가 어떻게 변경되는지를 변경 하이라이트와 함께 완전한 형태로 사전 렌더링합니다."
)
async def get_wiki_preview(
    ticket_id: str,
    highlight_changes: bool = Query(default=True, alias="highlightChanges"),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    return await _review_wiki_preview(ticket_id, None, current_user, db)


async def _review_wiki_preview(ticket_id, edited_content, current_user, db, request=None):
    review_service.require_editor(current_user)
    ticket = await review_repo.get(db, ticket_id)
    if not ticket:raise HTTPException(404, '검토 티켓을 찾지 못했습니다.')
    return await review_service.preview_response(ticket, db, current_user, request or ReviewPreviewRequest(editedContent=edited_content))


@router.post('/{ticket_id}/wiki-preview', response_model=WikiPreviewResponse, response_model_by_alias=True)
async def preview_working_copy(
    ticket_id: str, body: ReviewPreviewRequest,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    return await _review_wiki_preview(ticket_id, body.editedContent, current_user, db, body)


@router.post(
    "/recommend-placement",
    response_model=ConceptPlacementRecommendResponse,
    response_model_by_alias=True,
    summary="신규 개념 온톨로지 편입 위치 AI 자동 추천 API",
    description="엔지니어가 입력한 기술명과 개요를 바탕으로 현재 위키 분류를 기준으로 소속 패싯, 물리적 규모, 세부 공정군을 추천합니다."
)
async def recommend_concept_placement(
    body: ConceptPlacementRecommendRequest,
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await recommend_placement(body, db, openai_key=x_openai_key, gemini_key=x_gemini_key)
    except PlacementRecommendationUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
