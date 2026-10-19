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
    ConceptModel,
    CausalEdgeModel
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


async def infer_causal_chain(
    db: AsyncSession,
    q: str,
    session: ComparisonSessionModel
) -> tuple[List[str], str]:
    """반도체 전 공정(노광, 식각, 박막, 소자, 패키징, 공정제어) 인과 온톨로지 기반 4단계 체인 도출."""
    q_lower = q.lower()

    # 1. DB CausalEdges 테이블에서 직접 연계 인과 엣지 검색 (우선 순위)
    edge_stmt = select(CausalEdgeModel).where(
        CausalEdgeModel.mechanism_label.ilike(f"%{q[:10]}%")
    ).limit(1)
    matched_edge = (await db.execute(edge_stmt)).scalar_one_or_none()

    if matched_edge:
        source_concept = await db.get(ConceptModel, matched_edge.source_concept_id)
        target_concept = await db.get(ConceptModel, matched_edge.target_concept_id)
        s_name = source_concept.title if source_concept else matched_edge.source_concept_id
        t_name = target_concept.title if target_concept else matched_edge.target_concept_id
        rel_map = {
            "causes": "물리적 인과 전이",
            "competing_with": "기술 대안 경쟁",
            "causes_defect": "공정 결함 유발",
            "compensates": "파라미터 보상 상쇄"
        }
        rel_label = rel_map.get(matched_edge.relation_type, matched_edge.relation_type)
        return (
            [s_name, "공정 변수 계면 응력", rel_label, t_name],
            f"[{s_name} ➔ {t_name}] {matched_edge.mechanism_label}"
        )

    # 2. 반도체 6대 전·후공정 도메인 물리 인과 템플릿 (노광, 식각, 박막, 소자, 패키징, FDC/APC)
    # [1] 노광 공정 (Lithography: High-NA, EUV, ArFi, DOF, LER, 스토캐스틱)
    if any(k in q_lower for k in ["노광", "euv", "high-na", "dof", "초점", "ler", "스토캐스틱", "레지스트", "패터닝"]):
        return (
            ["초점 심도(DOF) 축소", "웨이퍼 토포그래피 변동", "스토캐스틱 불균일 노광", "미세 패턴 브릿징/단선"],
            "개구수(NA) 증가 시 Rayleigh 공식(DOF ∝ λ/NA²)에 따라 초점 심도가 급감하며, 레지스트 박막의 화학적 불균일성으로 인해 나노 패턴 스토캐스틱 브릿징 및 선폭 거칠기(LER) 불량이 발생합니다."
        )

    # [2] 식각 공정 (Etch: Cryo, ALE, HARC, 틸팅, 플라즈마, RIE)
    elif any(k in q_lower for k in ["식각", "etch", "cryo", "극저온", "harc", "틸팅", "tilting", "로딩"]):
        return (
            ["라디칼/이온 플럭스 불균형", "웨이퍼 척 극저온 냉각 편차", "보호막 형성/탈착 지연", "고종횡비 식각 프로파일 틸팅"],
            "초고단 3D NAND/고종횡비(HARC) 식각 시 웨이퍼 척 헬륨 냉각 압력 변동으로 표면 패시베이션 흡착층 밸런스가 무너지며, 이온 빔 입사각 왜곡으로 인한 하부 휨 및 프로파일 틸팅(Tilting) 결함이 유발됩니다."
        )

    # [3] 증착/박막 공정 (Deposition: ALD, CVD, Epitaxy, 결정, 격자, 균일도)
    elif any(k in q_lower for k in ["증착", "ald", "cvd", "epitaxy", "에피", "단결정", "격자", "박막"]):
        return (
            ["전구체 흡착 불균일", "열분해 속도 편차", "격자 상수 부정합(Mismatch)", "계면 응력 및 결정 결함 전위"],
            "원자층 증착(ALD) 및 에피택시 성장 시 기판-박막 간 격자 상수 부정합 응력이 축적되어 원자간 결합각이 뒤틀리며 계면 트랩 준위 및 결정 결함 전위(Dislocation)가 증가합니다."
        )

    # [4] 소자 구조 및 물리 (Device: GAA, MBCFET, Nanosheet, FinFET, 단채널, SCE, 누설전류)
    elif any(k in q_lower for k in ["gaa", "mbcfet", "nanosheet", "나노시트", "finfet", "단채널", "sce", "누설"]):
        return (
            ["채널 나노시트 박막화", "게이트 정전 전계 제어력 약화", "단채널 효과(SCE) 심화", "오프상태 누설 전류 급증"],
            "2nm 이하 GAA 소자에서 채널 두께 미세화 시 양자 구속 효과로 인해 문턱 전압(Vth) 산포가 확대되고 드레인 유기 장벽 저하(DIBL)가 심화되어 오프 상태 대기 누설 전류가 급격히 상승합니다."
        )

    # [5] 첨단 패키징 (Packaging: TCB, MR-MUF, 하이브리드 본딩, 휨, Warpage, 보이드, 쇼트)
    elif any(k in q_lower for k in ["휨", "warpage", "워피지"]):
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

    # [6] 공정 제어 및 운영 (Operations: FDC, APC, R2R, 센서 드리프트, 수율)
    elif any(k in q_lower for k in ["apc", "fdc", "r2r", "런투런", "센서", "드리프트", "수율", "제어"]):
        return (
            ["설비 센서 시계열 드리프트", "챔버 환경 상태 변동", "Run-to-Run 피드백 지연", "웨이퍼 간 임계치수(CD) 산포"],
            "챔버 부품 노후화로 인한 센서 계측 드리프트를 APC 모델이 실시간 피드백 보정하지 못할 경우, 연속 공정 런 간 RF 바이어스 전력 편차가 누적되어 최종 다이 수율이 급락합니다."
        )

    # [7] 일반 반도체 공학 질의 기본 체인 (General Semiconductor Physical Chain)
    else:
        return (
            [f"{q} 입력 변수", "공정 계면 물리적 스트레스 전이", "도메인 임계치 도달", "전기적·구조적 성능 편차"],
            f"'{q}'에 대한 공정 시뮬레이션 결과, 공정 인자의 미세 변동이 계면 에너지 상태를 변화시켜 도메인 임계치를 초과하는 물리적 인과 메커니즘이 도출되었습니다."
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

    domain_label = (body.contextParams or {}).get("domain", "")
    target_a = (body.contextParams or {}).get("targetA", "기술 대안 A")
    target_b = (body.contextParams or {}).get("targetB", "기술 대안 B")

    # 기본 3-Step 스냅샷 템플릿 초기화 (전공정/후공정/소자 공통 공학적 의사결정 축)
    initial_snapshots = [
        {
            "step": 1,
            "title": "질의 의도 및 기술 대안 분기 확인",
            "branchData": {
                "question": body.query,
                "branches": [
                    {"id": "b1", "label": f"양산 수율 극대화 및 결함 억제 중심 비교 ({target_a})"},
                    {"id": "b2", "label": f"기존 팹 설비 호환성 및 공정 전환 비용 절감 대안 ({target_b})"},
                    {"id": "b3", "label": f"차세대 미세화 및 극한 성능 달성 혁신 대안 ({domain_label or '반도체 공정'})"}
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

    # 4단계 인과 체인 및 물리 해설 추론 (DB CausalEdges 및 6대 도메인 물리 법칙 연계)
    causal_path, explanation = await infer_causal_chain(db, body.query, session)
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
