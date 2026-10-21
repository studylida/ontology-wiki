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

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.cache import cache_manager
from backend.app.models.entities import ReviewTicketModel, AuditLogModel, ConceptModel, CausalEdgeModel
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
    db: AsyncSession = Depends(get_db)
):
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
        merged_draft = f"{concept.summary}\n\n[제안 반영안 ({body.author})]: {body.userNote or body.title}"
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
        author=body.author,
        department=body.department or "도메인개발팀",
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
    body: ReviewTicketApproveRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    if x_user_role and x_user_role.lower() == "line_engineer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CHIEF_REVIEWER_ONLY",
                "message": "위키 버전 승인 및 거버넌스 집행 권한은 '수석검토관(chief_reviewer)' 전용입니다. 현장 엔지니어(line_engineer)는 승인 권한이 없습니다."
            }
        )

    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    now_utc = datetime.utcnow()
    final_reason = body.overrideReason or ticket.override_reason or ""
    guide_tip = None

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
    # 1. 온톨로지 세맨틱 버전(vMAJOR.MINOR.PATCH) 자동 계산
    concept = await db.get(ConceptModel, ticket.concept_id)
    cur_ver = (concept.version if concept else ticket.current_version) or "v1.2.0"
    
    # 버전 승계 규칙:
    # 1. 신규 개념 등록 (new_concept) 또는 공인 출처 공식 폐기(Breaking Change) -> minor (v1.2.x -> v1.3.0)
    #    (명시적 플래그/목록 또는 Tier 1 AI 사유 문맥 의도 판별을 통해 Human-in-the-Loop 인가)
    # 2. 일상적 파라미터/문맥 수정 -> patch (v1.2.0 -> v1.2.1)
    from backend.app.core.citation_manager import EvidenceCitationManager
    is_new = "신규" in (ticket.review_type or "") or ticket.review_type == "new_concept"
    has_deprecation_flag = body.allowCitationDeletion or bool(body.deprecatedCitations)
    has_deprecation_reason = await EvidenceCitationManager.is_deprecation_intended(
        final_reason,
        gemini_key=x_gemini_key,
        openai_key=x_openai_key
    )
    has_deprecation = has_deprecation_flag or has_deprecation_reason
    auto_bump_type = "minor" if (is_new or has_deprecation) else "patch"
    
    def _bump_version(v_str: str, b_type: str) -> str:
        cleaned = (v_str or "").strip().lstrip("v")
        parts = cleaned.split(".")
        maj, min_v, pat = 1, 0, 0
        try:
            if len(parts) >= 1 and parts[0].isdigit(): maj = int(parts[0])
            if len(parts) >= 2 and parts[1].isdigit(): min_v = int(parts[1])
            if len(parts) >= 3 and parts[2].isdigit(): pat = int(parts[2])
        except Exception:
            pass
        if b_type == "major": return f"v{maj + 1}.0.0"
        elif b_type == "minor": return f"v{maj}.{min_v + 1}.0"
        return f"v{maj}.{min_v}.{pat + 1}"

    applied_ver = body.targetVersion or ticket.target_version or _bump_version(cur_ver, auto_bump_type)
    gov_snapshot = {
        "ticketId": ticket.id,
        "conceptId": ticket.concept_id,
        "conceptTitle": ticket.concept_title,
        "appliedVersion": applied_ver,
        "previousVersion": cur_ver,
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
    else:
        # 🌟 완전 신규 개념 승인 분기: ConceptModel 신규 생성 및 온톨로지 트리 영구 편입
        placement = {}
        if ticket.structured_patches and isinstance(ticket.structured_patches, list):
            for patch in ticket.structured_patches:
                if patch.get("path") == "/concept" and isinstance(patch.get("value"), dict):
                    placement = patch.get("value")
                    break

        new_concept = ConceptModel(
            id=ticket.concept_id,
            title=ticket.concept_title or ticket.title,
            eng_name=placement.get("eng_name", ticket.concept_title or ticket.title),
            aliases=[],
            domain_facet=placement.get("domain_facet", "unit_process"),
            process_category=placement.get("process_category", "첨단 패키징"),
            scale_level=placement.get("scale_level", 3),
            scale_name=placement.get("scale_name", "Scale 3: 단위 공정"),
            version=applied_ver or "v1.0.0",
            status="adopted",
            last_reviewed_at=now_utc,
            last_reviewed_by=body.approvedBy,
            summary=ticket.human_edits or ticket.ai_merged_draft or "### 1. 기술 정의\n(신규 온톨로지 개념)",
            purpose=ticket.override_reason or "신규 공정 개념 편입",
            principles=[],
            limitations=[],
            relations={"is_a": placement.get("parent_concept_id")} if placement.get("parent_concept_id") else {},
            created_at=now_utc,
            updated_at=now_utc
        )
        db.add(new_concept)
        concept_updated = True

        # 상위 개념과의 인과 에지(CausalEdgeModel) 자동 연결
        parent_id = placement.get("parent_concept_id")
        if parent_id:
            parent_concept = await db.get(ConceptModel, parent_id)
            if parent_concept:
                new_edge = CausalEdgeModel(
                    source_concept_id=new_concept.id,
                    target_concept_id=parent_id,
                    relation_type="is_a",
                    polarity="+",
                    weight=1.00,
                    mechanism_label=f"{new_concept.title} is a subtype of {parent_concept.title}"
                )
                db.add(new_edge)

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

    # 7. 3.6절 Contextual Explainer 0ms 사전 컴파일 (Pre-computed Edge Caching)
    try:
        from backend.app.agents.explainer_agent import explainer_agent
        await explainer_agent.precompile_concept_explainers(ticket.concept_id, db)
    except Exception as e:
        logger.warning(f"Failed to precompile explainers on approval: {e}")


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
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    db: AsyncSession = Depends(get_db)
):
    if x_user_role and x_user_role.lower() == "line_engineer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CHIEF_REVIEWER_ONLY",
                "message": "위키 거버넌스 반려 권한은 '수석검토관(chief_reviewer)' 전용입니다. 현장 엔지니어(line_engineer)는 반려 권한이 없습니다."
            }
        )

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
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
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
    from backend.app.agents.directive_agent import directive_agent
    await directive_agent.process_directive(
        ticket=ticket,
        directive_text=text_input,
        override_reason=body.overrideReason,
        db=db,
        allow_citation_deletion=body.allowCitationDeletion,
        deprecated_citations=body.deprecatedCitations,
        gemini_key=x_gemini_key,
        openai_key=x_openai_key
    )

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
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    if not body.editedContent.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="편집 내용이 비어있습니다."
        )

    # 낙관적 판본 충돌 검사
    if body.ticketVersion is not None and body.ticketVersion != ticket.ticket_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"버전 충돌 감지: 현재 티켓 버전은 {ticket.ticket_version}입니다."
        )

    # 🌟 공인 출처 불변성 검증 및 자동 복원 / 공식 폐기 인가
    from backend.app.core.citation_manager import EvidenceCitationManager
    base_text = f"{ticket.current_content or ''}\n{ticket.ai_merged_draft or ''}".strip()
    final_content, restored_tags, deprecated_tags = await EvidenceCitationManager.validate_and_restore(
        original_text=base_text,
        edited_text=body.editedContent,
        allow_citation_deletion=body.allowCitationDeletion,
        deprecated_citations=body.deprecatedCitations,
        override_reason=body.overrideReason
    )

    ticket.human_edits = final_content
    if body.overrideReason:
        ticket.override_reason = body.overrideReason
    ticket.ticket_version += 1
    ticket.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(ticket)

    return HumanEditsResponse(
        ticket_id=ticket.id,
        ticket_version=ticket.ticket_version,
        human_edits=ticket.human_edits,
        integrity_report=ticket.integrity_report or {},
        updated_at=ticket.updated_at.isoformat()
    )


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
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(ReviewTicketModel, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
        )

    concept = await db.get(ConceptModel, ticket.concept_id)
    applied_ver = ticket.applied_concept_version or ticket.target_version or "v1.3"
    draft_content = ticket.human_edits or ticket.ai_merged_draft

    preview_summary = (
        f"<mark class=\"diff-added\">{draft_content}</mark>"
        if highlight_changes else draft_content
    )

    preview_concept = {
        "id": concept.id if concept else ticket.concept_id,
        "title": concept.title if concept else ticket.concept_title,
        "engName": concept.eng_name if concept else "",
        "aliases": concept.aliases if concept and isinstance(concept.aliases, list) else [],
        "domainFacet": concept.domain_facet if concept else "unit_process",
        "processCategory": concept.process_category if concept else "첨단 패키징",
        "scaleLevel": concept.scale_level if concept else 3,
        "scaleName": concept.scale_name if concept else "L3 단위 공정",
        "version": applied_ver,
        "status": "preview",
        "lastReviewedBy": f"{ticket.author} (승인 대기 중)",
        "lastReviewedAt": datetime.utcnow().strftime("%Y.%m.%d (미리보기)"),
        "summary": preview_summary,
        "purpose": concept.purpose if concept else "",
        "principles": concept.principles if concept and isinstance(concept.principles, list) else [],
        "limitations": concept.limitations if concept and isinstance(concept.limitations, list) else []
    }

    return WikiPreviewResponse(
        ticket_id=ticket.id,
        concept_id=ticket.concept_id,
        target_version=applied_ver,
        preview_concept=preview_concept,
        diff_summary={
            "addedCount": 1,
            "modifiedCount": 1,
            "status": "preview"
        }
    )


@router.post(
    "/recommend-placement",
    response_model=ConceptPlacementRecommendResponse,
    response_model_by_alias=True,
    summary="신규 개념 온톨로지 편입 위치 AI 자동 추천 API",
    description="엔지니어가 입력한 기술명과 개요를 바탕으로 4-Tier AI(OpenAI/Gemini) 및 온톨로지 지식 그래프를 스캔하여 최적의 패싯, 스케일 레벨, 공정군 및 상위 개념을 자동 추천합니다."
)
async def recommend_concept_placement(
    body: ConceptPlacementRecommendRequest,
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    db: AsyncSession = Depends(get_db)
):
    # 🌟 Tier 1 AI 클라우드 추론 시도 (API 키 제공 시)
    active_key = x_openai_key or x_gemini_key or settings.OPENAI_API_KEY or settings.GEMINI_API_KEY
    if active_key:
        try:
            from backend.app.core.llm_gateway import LLMGateway
            gateway = LLMGateway(default_timeout_sec=10.0)

            # DB의 기존 개념 후보 목록 조회 (상위 개념 매칭용)
            stmt = select(ConceptModel.id, ConceptModel.title, ConceptModel.scale_level, ConceptModel.domain_facet).limit(30)
            res_c = await db.execute(stmt)
            known_concepts = [{"id": r[0], "title": r[1], "scale": r[2], "facet": r[3]} for r in res_c.all()]

            system_instruction = (
                "당신은 첨단 반도체 공정 및 소자 인과 온톨로지(Semiconductor Causal Ontology) 수석 아키텍트입니다.\n"
                "엔지니어가 제안한 신규 기술/문서의 제목과 개요를 분석하여 온톨로지 지식 체계에서 최적의 편입 위치를 정확히 판별하세요.\n\n"
                "온톨로지 4대 패싯 (domainFacet):\n"
                "- 'device': 트랜지스터, 메모리 셀 등 소자 물성 및 구조\n"
                "- 'unit_process': 노광, 식각, 박막, 세정, 본딩 등 단위 공정 메커니즘\n"
                "- 'fab': 팹 유틸리티, 챔버 설비, 진공, 배관, OES FDC 등 팹 단위 기술\n"
                "- 'infra': 클린룸 환경, 케미컬 공급, 스크러버 등 인프라\n\n"
                "온톨로지 5대 스케일 (scaleLevel / scaleName):\n"
                "1: Scale 1: 원자·분자 물성 (ALD, 계면 화학, 격자 변형)\n"
                "2: Scale 2: 나노 디바이스 (FinFET, GAA, CFET, 비트라인 에어갭)\n"
                "3: Scale 3: 단위 공정 (TCB, Cryo 식각, High-NA 노광, CMP)\n"
                "4: Scale 4: 팹 / 모듈 라인 (FDC 제어, 챔버 매칭, 수율 라인)\n"
                "5: Scale 5: 첨단 패키징 / 서브시스템 (HBM, MR-MUF, 3D IC, TGV 유리기판, SiP)\n\n"
                f"현재 등록된 주요 온톨로지 개념 후보:\n{json.dumps(known_concepts, ensure_ascii=False)}\n\n"
                "반드시 아래 JSON 포맷으로만 응답하세요:\n"
                "{\n"
                '  "domainFacet": "unit_process",\n'
                '  "scaleLevel": 5,\n'
                '  "scaleName": "Scale 5: 첨단 패키징 / 서브시스템",\n'
                '  "processCategory": "첨단 패키징",\n'
                '  "parentConceptId": "가장 인접한 개념 ID 또는 null",\n'
                '  "parentConceptTitle": "상위 개념명 또는 null",\n'
                '  "reasoning": "도메인 물리 공학적 위치 추천 사유 (1~2문장)"\n'
                "}"
            )

            user_prompt = f"신규 기술명: {body.title}\n핵심 기술 정의 및 개요: {body.summary or '상세 개요 미입력'}"

            llm_res = await gateway.generate_text(
                prompt=user_prompt,
                system_instruction=system_instruction,
                openai_key=x_openai_key,
                gemini_key=x_gemini_key,
                tier="tier1_fast",
                timeout_sec=8.0
            )

            if llm_res:
                clean_json = llm_res.strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                parsed = json.loads(clean_json)
                return ConceptPlacementRecommendResponse(
                    domain_facet=parsed.get("domainFacet", "unit_process"),
                    scale_level=int(parsed.get("scaleLevel", 3)),
                    scale_name=parsed.get("scaleName", f"Scale {parsed.get('scaleLevel', 3)}"),
                    process_category=parsed.get("processCategory", "첨단 반도체 공정"),
                    parent_concept_id=parsed.get("parentConceptId"),
                    parent_concept_title=parsed.get("parentConceptTitle"),
                    reasoning=f"[AI 지능형 온톨로지 분석] {parsed.get('reasoning', '')}"
                )
        except Exception as e:
            logger.warning(f"Tier 1 AI placement recommendation failed, falling back to deterministic heuristic: {e}")

    # 🌟 Tier 4: 결정론적 도메인 공학 규칙 기반 Fallback
    query_text = f"{body.title} {body.summary or ''}".lower()

    if any(k in query_text for k in ["패키징", "packaging", "본딩", "bonding", "muf", "ncf", "tgv", "인터포저", "기판", "substrate", "wlp", "2.5d", "3d"]):
        facet = "unit_process"
        scale = 5 if any(k in query_text for k in ["tgv", "기판", "모듈", "2.5d", "3d", "서브시스템"]) else 3
        scale_name = "Scale 5: 첨단 패키징 / 서브시스템" if scale == 5 else "Scale 3: 단위 공정"
        category = "첨단 패키징"
        reasoning = f"'{body.title}'의 핵심 키워드에서 칩간 접합 및 패키징 기판 연계 특성이 분석되어 [{scale_name}]의 [{category}] 공정군으로 편입을 추천합니다."
    elif any(k in query_text for k in ["식각", "etch", "rie", "플라즈마", "plasma", "cryo", "이온"]):
        facet = "unit_process"
        scale = 3
        scale_name = "Scale 3: 단위 공정"
        category = "식각 공정"
        reasoning = f"'{body.title}'에서 미세 패턴 제거 및 플라즈마 반응 특성이 감지되어 [{scale_name}]의 [{category}] 공정군으로 편입을 추천합니다."
    elif any(k in query_text for k in ["원자", "atomic", "ald", "박막", "증착", "cvd", "단분자"]):
        facet = "unit_process"
        scale = 1
        scale_name = "Scale 1: 원자·분자 물성"
        category = "박막 증착"
        reasoning = f"'{body.title}'에서 원자 수준 표면 반응 메커니즘이 감지되어 [{scale_name}]으로 편입을 추천합니다."
    elif any(k in query_text for k in ["팹", "fab", "클린룸", "배관", "용수", "공조", "스크러버", "환경"]):
        facet = "fab"
        scale = 4
        scale_name = "Scale 4: 팹 / 모듈 라인"
        category = "팹 인프라"
        reasoning = f"'{body.title}'에서 팹 유틸리티 및 환경 제어 특성이 감지되어 [{scale_name}]의 [팹 인프라]로 편입을 추천합니다."
    else:
        facet = "unit_process"
        scale = 3
        scale_name = "Scale 3: 단위 공정"
        category = "단위 공정 기술"
        reasoning = f"'{body.title}'의 기술적 범위를 고려하여 표준 반도체 [{scale_name}]으로 기본 편입을 추천합니다."

    # 가장 인접한 기존 상위 개념 탐색 (유사도 매칭)
    parent_concept_id = None
    parent_concept_title = None
    stmt = select(ConceptModel).where(ConceptModel.scale_level <= scale).order_by(ConceptModel.scale_level.desc())
    result = await db.execute(stmt)
    candidate_concepts = result.scalars().all()
    if candidate_concepts:
        for c in candidate_concepts:
            if c.domain_facet == facet and (c.process_category == category or c.scale_level == scale):
                parent_concept_id = c.id
                parent_concept_title = c.title
                break
        if not parent_concept_id:
            parent_concept_id = candidate_concepts[0].id
            parent_concept_title = candidate_concepts[0].title

    return ConceptPlacementRecommendResponse(
        domain_facet=facet,
        scale_level=scale,
        scale_name=scale_name,
        process_category=category,
        parent_concept_id=parent_concept_id,
        parent_concept_title=parent_concept_title,
        reasoning=reasoning
    )

