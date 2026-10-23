"""Ontology Concept and Causal Subgraph API Router.

Provides:
1. GET /api/v1/concepts/{id} - Concept details, principles, limitations, and adaptive perspective cases.
2. GET /api/v1/concepts/{id}/causal-subgraph - 0.65ms Recursive CTE causal network with Compensating Parameters.
3. GET /api/v1/concepts/{id}/contextual-explainer - 0ms popover inline context definitions.
"""
from typing import Optional, List, Dict, Any, Literal
import re
import json
import logging
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.cache import cache_manager
from backend.app.core.security import mask_tier3_perspective, get_current_user_optional, require_min_level
from backend.app.services.auth_service import AccessControlService
from backend.app.models.entities import (
    ConceptModel,
    CausalEdgeModel,
    PerspectiveCaseModel,
    UserModel
)
from backend.app.schemas.ontology import (
    ConceptDetailResponse,
    PerspectiveCaseDTO,
    CausalSubgraphResponse,
    SubgraphNode,
    SubgraphEdge,
    CompensatingParamSchema,
    ContextualExplanationDTO,
    ContextualExplanationRequest,
    ConceptTreeNode,
    ConceptTreeResponse
)
from backend.app.schemas.review import (
    ConceptPlacementRecommendRequest,
    ConceptPlacementRecommendResponse
)
from backend.app.services.concept_service import (
    concept_service, ContextualExplanationNotFound, ContextualExplanationRestricted,
    ContextualExplanationUnavailable,
)
from backend.app.services.case_explanation_service import (case_explanation_service, CaseExplanationChanged, CaseExplanationUnavailable)
from backend.app.services.placement_service import recommend_placement, PlacementRecommendationUnavailable
from backend.app.repositories.concept_repo import concept_repo

logger = logging.getLogger("ontology_wiki.concepts")

router = APIRouter(prefix="/concepts", tags=["Concepts & Causal Ontology"])


@router.post(
    "/recommend-placement",
    response_model=ConceptPlacementRecommendResponse,
    response_model_by_alias=True,
    summary="신규 개념 온톨로지 편입 위치 AI 자동 추천 API (Concepts 별칭)",
    description="엔지니어가 입력한 기술명과 개요를 바탕으로 현재 위키 분류를 기준으로 소속 패싯, 물리적 규모, 세부 공정군을 추천합니다."
)
async def recommend_concept_placement_alias(
    body: ConceptPlacementRecommendRequest,
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await recommend_placement(body, db, openai_key=x_openai_key, gemini_key=x_gemini_key)
    except PlacementRecommendationUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get(
    "/tree",
    response_model=ConceptTreeResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="좌측 사이드바 4축 계층형 온톨로지 네비게이션 트리 조회 API",
    description="4대 업무 분류(소자, 공정, 운영, 소재) 및 단위 공정 카테고리별 계층형 온톨로지 트리를 서빙합니다."
)
async def get_concept_tree(
    facet: Optional[str] = Query(
        default="unit_process",
        description="4대 업무 분야 분류 필터 (device, unit_process, operations, materials_infra)"
    ),
    scale: Optional[int] = Query(
        default=None,
        description="물리적 규모(Scale 1~5) 필터"
    ),
    expanded_id: Optional[str] = Query(default=None, alias="expandedId", description="기본 활성화할 개념 ID"),
    db: AsyncSession = Depends(get_db)
):
    target_facet = facet or "unit_process"
    cache_key = f"concept:tree:scale:{scale}" if scale is not None else f"concept:tree:{target_facet}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return ConceptTreeResponse(**cached)

    # 1. 대상 패싯 또는 스케일의 개념 전체 조회
    if scale is not None:
        stmt = (
            select(ConceptModel)
            .options(selectinload(ConceptModel.perspectives))
            .where(ConceptModel.scale_level == scale)
            .order_by(ConceptModel.title.asc())
        )
    else:
        stmt = (
            select(ConceptModel)
            .options(selectinload(ConceptModel.perspectives))
            .where(ConceptModel.domain_facet == target_facet)
            .order_by(ConceptModel.scale_level.asc(), ConceptModel.title.asc())
        )
    concepts = (await db.execute(stmt)).scalars().all()

    # 2. 카테고리(process_category)별 그룹화하여 트리 구성
    categories: Dict[str, List[ConceptModel]] = {}
    for c in concepts:
        cat = c.process_category or "기타 공정"
        categories.setdefault(cat, []).append(c)

    tree_nodes: List[ConceptTreeNode] = []
    for cat_name, cat_concepts in sorted(categories.items()):
        cat_slug = re.sub(r'[^a-zA-Z0-9가-힣]+', '-', cat_name.lower()).strip('-')
        cat_hash = hashlib.md5(cat_name.encode('utf-8')).hexdigest()[:8]
        cat_id = f"cat-{cat_slug}-{cat_hash}" if cat_slug else f"cat-{cat_hash}"
        children_nodes: List[ConceptTreeNode] = []

        for c in cat_concepts:
            children_nodes.append(
                ConceptTreeNode(
                    id=c.id,
                    title=c.title,
                    eng_name=c.eng_name,
                    aliases=c.aliases if isinstance(c.aliases, list) else [],
                    type="concept",
                    scale_level=c.scale_level,
                    badge=f"L{c.scale_level} {c.scale_name or '공정'}",
                    status=c.status or "adopted",
                    has_perspectives=bool(c.perspectives and len(c.perspectives) > 0),
                    children=[]
                )
            )

        tree_nodes.append(
            ConceptTreeNode(
                id=cat_id,
                title=cat_name,
                type="category",
                children=children_nodes
            )
        )

    response_dto = ConceptTreeResponse(
        current_facet=target_facet,
        total_nodes=len(concepts),
        tree=tree_nodes
    )

    await cache_manager.set(cache_key, response_dto.model_dump(by_alias=True), ttl_seconds=300)
    return response_dto


@router.get(
    "/{concept_id}",
    response_model=ConceptDetailResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="개념 상세 및 실무 사례 조회 API",
    description="개념 본문, 물리 원리, 한계점 및 레벨 3 적응형 실무 사례(Perspective Cases)를 일괄 서빙합니다."
)
async def get_concept_detail(
    concept_id: str,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    return await concept_service.get_enriched_concept_detail(
        concept_id=concept_id,
        current_user=current_user,
        session=db
    )


@router.post("/{concept_id}/perspectives/{case_id}/context-explanation",
             response_model=PerspectiveCaseDTO, response_model_by_alias=True, response_model_exclude_none=True)
async def generate_case_context_explanation(
    concept_id: str, case_id: str,
    current_user: UserModel = Depends(require_min_level(3)),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    await db.rollback()
    try:
        await case_explanation_service.generate(concept_id, case_id, gemini_key=x_gemini_key, openai_key=x_openai_key)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    except CaseExplanationChanged as error:
        raise HTTPException(409, str(error)) from error
    except CaseExplanationUnavailable as error:
        raise HTTPException(502, str(error)) from error
    detail = await concept_service.get_enriched_concept_detail(concept_id, None, db)
    return next(case for case in detail.perspectives if case.id == case_id)


@router.get(
    "/{concept_id}/causal-subgraph",
    response_model=CausalSubgraphResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="1~2 hop 인과 서브그래프 및 보상 파라미터 조회 API",
    description="0.65ms Recursive CTE를 통해 중심 개념의 1~2 hop 인과 네트워크와 '보상 파라미터(Compensating Parameters)'를 반환합니다."
)
async def get_causal_subgraph(
    concept_id: str,
    depth: int = Query(default=2, ge=1, le=3, description="인과 탐색 깊이 (1~3 hop)"),
    direction: Literal["out", "in", "both"] = Query(default="both", description="인과 탐색 방향 (out: 결과, in: 원인, both: 양방향)"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    center_check = await concept_repo.get_by_id(db, concept_id)
    if not center_check:
        raise HTTPException(status_code=404, detail=f"Central concept '{concept_id}' not found.")
    concept_id = center_check.id
    cache_key = f"concept:subgraph:{concept_id}:{depth}:{direction}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return await concept_service.mask_subgraph_response(CausalSubgraphResponse(**cached), current_user, db)

    # 2. SQLite / PostgreSQL 공용 Recursive CTE 쿼리 실행
    # 방향에 따른 anchor 및 recursive 조건 세팅
    cte_sql = text("""
    WITH RECURSIVE causal_network AS (
        -- Anchor Member (Hop 1)
        SELECT 
            ce.id,
            ce.source_concept_id,
            ce.target_concept_id,
            ce.relation_type,
            ce.polarity,
            ce.weight,
            ce.mechanism_label,
            ce.compensating_params,
            ce.evidence_id,
            1 AS hop
        FROM causal_edges ce
        WHERE (:dir IN ('out', 'both') AND ce.source_concept_id = :center_id)
           OR (:dir IN ('in', 'both') AND ce.target_concept_id = :center_id)

        UNION ALL

        -- Recursive Member (Hop 2+)
        SELECT 
            ce.id,
            ce.source_concept_id,
            ce.target_concept_id,
            ce.relation_type,
            ce.polarity,
            ce.weight,
            ce.mechanism_label,
            ce.compensating_params,
            ce.evidence_id,
            cn.hop + 1
        FROM causal_edges ce
        INNER JOIN causal_network cn ON (
            (:dir = 'out' AND ce.source_concept_id = cn.target_concept_id) OR
            (:dir = 'in' AND ce.target_concept_id = cn.source_concept_id) OR
            (:dir = 'both' AND (ce.source_concept_id IN (cn.source_concept_id, cn.target_concept_id)
                               OR ce.target_concept_id IN (cn.source_concept_id, cn.target_concept_id)))
        )
        WHERE cn.hop < :max_depth AND ce.id != cn.id
    )
    SELECT * FROM causal_network;
    """)

    result = await db.execute(
        cte_sql,
        {"center_id": concept_id, "max_depth": depth, "dir": direction}
    )
    rows = result.fetchall()

    # 3. 엣지 중복 제거 및 DTO 구성
    edge_map = {}
    node_ids = {concept_id}

    for row in rows:
        edge_id = row.id
        if edge_id in edge_map:
            continue

        s_id = row.source_concept_id
        t_id = row.target_concept_id
        node_ids.add(s_id)
        node_ids.add(t_id)

        # 🌟 도메인 필수 용어: 보상 파라미터(Compensating Parameters) 역직렬화
        comp_params = None
        raw_comp = row.compensating_params
        if raw_comp:
            if isinstance(raw_comp, str):
                try:
                    raw_comp = json.loads(raw_comp)
                except Exception:
                    raw_comp = None
            if isinstance(raw_comp, dict):
                comp_params = CompensatingParamSchema(
                    parameter=raw_comp.get("parameter", ""),
                    compensation_formula=raw_comp.get("compensation_formula", raw_comp.get("compensationFormula", "")),
                    tradeoff_cost=raw_comp.get("tradeoff_cost", raw_comp.get("tradeoffCost", ""))
                )

        subgraph_edge = SubgraphEdge(
            id=f"edge-{s_id}-{t_id}-{row.relation_type}",
            source=s_id,
            target=t_id,
            relation_type=row.relation_type,
            polarity=row.polarity,
            weight=float(row.weight or 1.0),
            mechanism_label=row.mechanism_label,
            compensating_params=comp_params,
            evidence_id=row.evidence_id
        )
        edge_map[edge_id] = subgraph_edge

    # 4. 연관 노드 메타데이터 조회
    nodes_dto: List[SubgraphNode] = []
    if node_ids:
        nodes_stmt = select(ConceptModel).where(ConceptModel.id.in_(node_ids))
        node_records = (await db.execute(nodes_stmt)).scalars().all()
        found_ids = set()

        for nr in node_records:
            found_ids.add(nr.id)
            nodes_dto.append(
                SubgraphNode(
                    id=nr.id,
                    label=nr.title,
                    category=nr.process_category,
                    scale_level=nr.scale_level,
                    is_center=(nr.id == concept_id)
                )
            )

        # concepts 테이블에 없는 파라미터/결함 노드인 경우 기본 노드 생성
        for nid in node_ids - found_ids:
            nodes_dto.append(
                SubgraphNode(
                    id=nid,
                    label=nid,
                    category="미등록 개념",
                    scale_level=None,
                    is_registered=False,
                    is_center=(nid == concept_id)
                )
            )

    response_dto = CausalSubgraphResponse(
        central_concept_id=concept_id,
        has_relations=bool(await concept_repo.get_causal_edges_for_concept(db, concept_id)),
        graph={
            "nodes": [n.model_dump(by_alias=True) for n in nodes_dto],
            "edges": [e.model_dump(by_alias=True) for e in edge_map.values()]
        }
    )

    await cache_manager.set(cache_key, response_dto.model_dump(by_alias=True), ttl_seconds=120)
    return await concept_service.mask_subgraph_response(response_dto, current_user, db)


async def _explain_selection(concept_id, term_id, selection_context, db, **keys):
    try:
        return await concept_service.get_contextual_explanation(concept_id, term_id, selection_context, db, **keys)
    except ContextualExplanationNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ContextualExplanationRestricted as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ContextualExplanationUnavailable as error:
        logger.warning("Contextual explanation generation failed: %s", type(error.__cause__).__name__)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        logger.warning("Contextual explanation request failed: %s", type(error).__name__)
        raise HTTPException(status_code=500, detail="문맥 해설 요청을 처리하지 못했습니다.") from error


@router.get(
    "/{concept_id}/contextual-explainer",
    response_model=ContextualExplanationDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="선택한 표현의 뜻과 공개 문맥 해설 조회"
)
async def get_contextual_explainer(
    concept_id: str,
    term_id: str = Query(..., description="실제 선택 문자열 또는 등록 개념 ID"),
    perspective_id: Optional[str] = Query("default", description="호환용 관점 식별자"),
    selection_context: str = Query("", max_length=600, description="선택 주변의 화면 문맥"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    return await _explain_selection(concept_id, term_id, selection_context, db,
        gemini_key=x_gemini_key, openai_key=x_openai_key)


@router.post(
    "/{concept_id}/contextual-explainer",
    response_model=ContextualExplanationDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="선택 문맥을 URL에 노출하지 않는 표현 해설"
)
async def explain_selection(
    concept_id: str,
    body: ContextualExplanationRequest,
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    return await _explain_selection(concept_id, body.term_id, body.selection_context, db,
        gemini_key=x_gemini_key, openai_key=x_openai_key)
