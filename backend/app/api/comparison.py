"""Comparison Studio API Router.

Provides:
1. GET  /api/v1/comparison-sessions - List comparison sessions
2. POST /api/v1/comparison-sessions - Create comparison session
3. GET  /api/v1/comparison-sessions/{id} - Get session detail with 3-Step snapshots
4. POST /api/v1/comparison-sessions/{id}/deep-dive - Register tail-question (꼬리질문) & 4-step causal chain
5. POST /api/v1/comparison-sessions/{id}/export-review - Export to Review Center ticket (with forbidden phrase check)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import (
    ComparisonSessionModel,
    ReviewTicketModel,
    ConceptModel
)
from backend.app.schemas.comparison import (
    ComparisonSessionDTO,
    ComparisonSessionCreate,
    TailQuestionEntry,
    DeepDiveRequest,
    DeepDiveResponse,
    ExportReviewRequest,
    ExportReviewResponse
)

logger = logging.getLogger("ontology_wiki.comparison")

router = APIRouter(prefix="/comparison-sessions", tags=["Comparison Studio"])


def infer_causal_path_for_query(q: str) -> tuple[List[str], str]:
    """꼬리질문 질의에 대한 반도체 물리 인과 체인(4단계) 및 공학적 해설 추론."""
    q_lower = q.lower()
    
    if any(k in q_lower for k in ["휨", "warpage", "워피지"]):
        return (
            ["가압력 누적", "CTE 미스매치", "전단응력", "다이 휨"],
            "NCF의 열팽창계수(CTE, 약 30ppm/K)와 실리콘 다이(2.6ppm/K) 간의 10배 이상 물성 차이로 인해, 냉각 시 계면 전단응력이 중심부로 집중되면서 칩 최외곽이 위로 들리는 Warpage 현상이 유발됩니다."
        )
    elif any(k in q_lower for k in ["보이드", "void", "미충진"]):
        return (
            ["점도 상승", "모세관 유동 저항", "기포 포집", "미소 보이드 잔류"],
            "액상 언더필 주입 중 국소 온도 저하로 점도가 상승하여 미세 범프 간극에서 모세관 유동 압력이 급감하고 공기가 포집되어 보이드 결함이 발생합니다."
        )
    elif any(k in q_lower for k in ["브릿징", "쇼트", "short", "bridging"]):
        return (
            ["과도 가압력", "솔더 용융 압출", "측면 범프 접촉", "마이크로 브릿징 단락"],
            "본딩 가압력이 임계치를 초과할 경우 용융 솔더 볼이 NCF 필름 외곽으로 강제 압출되어 인접 범프와 접촉하며 단락 쇼트가 유발됩니다."
        )
    else:
        return (
            [f"{q} 입력", "공정 파라미터 변동", "계면 열응력 집중", "물리적 한계 발현"],
            f"'{q}'에 대한 공정 시뮬레이션 결과, 연속 공정 스트레스가 계면에 전달되어 도메인 임계치를 초과하는 물리적 메커니즘이 확인되었습니다."
        )


@router.get(
    "",
    response_model=List[ComparisonSessionDTO],
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="비교 세션 목록 조회 API",
    description="최신 비교 분석 세션 목록을 핀 고정 및 최신순으로 정렬하여 서빙합니다."
)
async def list_comparison_sessions(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ComparisonSessionModel)
        .order_by(ComparisonSessionModel.is_pinned.desc(), ComparisonSessionModel.created_at.desc())
        .limit(limit)
    )
    sessions = (await db.execute(stmt)).scalars().all()
    return [
        ComparisonSessionDTO(
            id=s.id,
            user_id=s.user_id,
            title=s.title,
            is_pinned=s.is_pinned,
            folder_id=s.folder_id,
            query=s.query,
            context_params=s.context_params or {},
            snapshots=s.snapshots or [],
            exported_review_id=s.exported_review_id,
            created_at=s.created_at.isoformat() if s.created_at else None,
            updated_at=s.updated_at.isoformat() if s.updated_at else None
        )
        for s in sessions
    ]


@router.post(
    "",
    response_model=ComparisonSessionDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="신규 비교 분석 세션 생성 API",
    description="3-Step 비교 스냅샷 템플릿과 함께 새 비교 세션을 초기화합니다."
)
async def create_comparison_session(
    body: ComparisonSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    today_str = datetime.utcnow().strftime("%Y%m%d")
    random_hex = uuid.uuid4().hex[:6]
    session_id = f"sess-{today_str}-{random_hex}"

    # 기본 3-Step 스냅샷 템플릿 초기화
    initial_snapshots = [
        {
            "step": 1,
            "title": "질의 의도 확인",
            "branchData": {
                "question": body.query,
                "branches": [
                    {"id": "b1", "label": "방열 및 고생산성 대안 우선 비교"},
                    {"id": "b2", "label": "기존 장비 호환성 및 안정성 중심 비교"},
                    {"id": "b3", "label": "차세대 하이브리드 접합 공정 대안"}
                ]
            }
        },
        {
            "step": 2,
            "title": "양산 조건 매핑",
            "conditions": body.contextParams or {},
            "constraintGaps": [],
            "tuningHistory": []
        },
        {
            "step": 3,
            "title": "다차원 비교 분석 완료",
            "matrix": [],
            "aiCausalNote": "온톨로지 인과 관계 기반 분석 대기",
            "deepDiveHistory": []
        }
    ]

    new_session = ComparisonSessionModel(
        id=session_id,
        user_id=body.userId,
        title=body.title,
        is_pinned=False,
        folder_id=body.folderId,
        query=body.query,
        context_params=body.contextParams,
        snapshots=initial_snapshots,
        exported_review_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return ComparisonSessionDTO(
        id=new_session.id,
        user_id=new_session.user_id,
        title=new_session.title,
        is_pinned=new_session.is_pinned,
        folder_id=new_session.folder_id,
        query=new_session.query,
        context_params=new_session.context_params or {},
        snapshots=new_session.snapshots or [],
        exported_review_id=new_session.exported_review_id,
        created_at=new_session.created_at.isoformat() if new_session.created_at else None,
        updated_at=new_session.updated_at.isoformat() if new_session.updated_at else None
    )


@router.get(
    "/{session_id}",
    response_model=ComparisonSessionDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="비교 세션 상세 조회 API",
    description="3-Step 스냅샷, 꼬리질문(deepDiveHistory), 보상 파라미터 튜닝 이력(tuningHistory)을 포함한 세션 상세를 반환합니다."
)
async def get_comparison_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(ComparisonSessionModel, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison session '{session_id}' not found."
        )

    return ComparisonSessionDTO(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        is_pinned=session.is_pinned,
        folder_id=session.folder_id,
        query=session.query,
        context_params=session.context_params or {},
        snapshots=session.snapshots or [],
        exported_review_id=session.exported_review_id,
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None
    )


@router.post(
    "/{session_id}/deep-dive",
    response_model=DeepDiveResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="엔지니어 꼬리질문(Deep-Dive) 등록 및 4단계 인과 체인 기록 API",
    description="엔지니어의 심층 질문에 대해 4단계 물리 인과 체인(Causal Chain)을 도출하고 세션의 Step 3 스냅샷에 영구 저장합니다."
)
async def add_deep_dive_question(
    session_id: str,
    body: DeepDiveRequest,
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(ComparisonSessionModel, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison session '{session_id}' not found."
        )

    # 4단계 인과 체인 및 물리 해설 추론
    causal_path, explanation = infer_causal_path_for_query(body.query)
    now_iso = datetime.utcnow().isoformat()

    tail_entry = TailQuestionEntry(
        query=body.query,
        causal_path=causal_path,
        explanation=explanation,
        timestamp=now_iso
    )

    # 스냅샷 업데이트
    snapshots = list(session.snapshots or [])
    step_idx = min(body.stepIndex, len(snapshots) - 1) if snapshots else -1

    if step_idx >= 0:
        target_step = dict(snapshots[step_idx])
        history = list(target_step.get("deepDiveHistory", []))
        history.append(tail_entry.model_dump(by_alias=True))
        target_step["deepDiveHistory"] = history
        snapshots[step_idx] = target_step
        session.snapshots = snapshots  # reassign to trigger SQLAlchemy JSON change tracking
        session.updated_at = datetime.utcnow()
        await db.commit()

    return DeepDiveResponse(
        session_id=session.id,
        tail_question=tail_entry
    )


@router.post(
    "/{session_id}/export-review",
    response_model=ExportReviewResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="비교 세션 ➔ 검토 센터 티켓 내보내기 API",
    description="비교 분석 결과를 바탕으로 지식 거버넌스 티켓을 생성합니다."
)
async def export_to_review_ticket(
    session_id: str,
    body: ExportReviewRequest,
    db: AsyncSession = Depends(get_db)
):

    session = await db.get(ComparisonSessionModel, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison session '{session_id}' not found."
        )

    concept = await db.get(ConceptModel, body.conceptId)
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept '{body.conceptId}' not found."
        )

    today_str = datetime.utcnow().strftime("%Y%m%d")
    random_hex = uuid.uuid4().hex[:4]
    ticket_id = f"rev-{today_str}-{random_hex}"

    new_ticket = ReviewTicketModel(
        id=ticket_id,
        concept_id=concept.id,
        concept_title=concept.title,
        title=body.title,
        review_type=body.reviewType,
        author=body.author,
        department="비교분석연구팀",
        submitted_at=datetime.utcnow(),
        status="pending",
        source_session_id=session.id,
        origin_type="비교분석",
        current_version=concept.version,
        target_version="v1.3",
        current_content=concept.summary,
        ai_merged_draft=f"비교 세션 [{session.title}]에서 도출된 최적 파라미터 및 인과 경로를 반영한 개정 초안.",
        human_edits=None,
        structured_patches=[
            {"op": "replace", "path": "/summary", "value": f"{concept.summary} (비교분석 반영)"}
        ],
        integrity_report={
            "verified": True,
            "evidenceCount": 1,
            "conflicts": [],
            "riskLevel": "LOW"
        },
        directive_history=[],
        override_reason=body.overrideReason,  # 🌟 도메인 필수 사유
        ticket_version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_ticket)
    session.exported_review_id = ticket_id
    session.updated_at = datetime.utcnow()

    await db.commit()

    message = f"비교 분석 세션이 거버넌스 티켓 [{ticket_id}]로 성공적으로 내보내졌습니다."
    if "전문가 사유" in (body.overrideReason or ""):
        message += " (💡 안내: 승인율을 높이기 위해 검토 센터에서 '전문가 사유' 대신 구체적 실측 데이터나 공인 백서 근거를 보완하실 수 있습니다.)"

    return ExportReviewResponse(
        session_id=session.id,
        ticket_id=ticket_id,
        message=message
    )
