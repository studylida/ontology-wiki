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
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.cache import cache_manager
from backend.app.core.security import mask_tier3_perspective, get_current_user_role
from backend.app.agents import explainer_agent
from backend.app.models.entities import (
    ConceptModel,
    CausalEdgeModel,
    PerspectiveCaseModel
)
from backend.app.schemas.ontology import (
    ConceptDetailResponse,
    PerspectiveCaseDTO,
    CausalSubgraphResponse,
    SubgraphNode,
    SubgraphEdge,
    CompensatingParamSchema,
    ContextualExplanationDTO,
    ConceptTreeNode,
    ConceptTreeResponse
)

logger = logging.getLogger("ontology_wiki.concepts")

router = APIRouter(prefix="/concepts", tags=["Concepts & Causal Ontology"])


@router.get(
    "/tree",
    response_model=ConceptTreeResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="좌측 사이드바 4축 계층형 온톨로지 네비게이션 트리 조회 API",
    description="4대 업무 분류(소자, 공정, 운영, 소재) 및 단위 공정 카테고리별 계층형 온톨로지 트리를 서빙합니다."
)
async def get_concept_tree(
    facet: Optional[Literal["device", "unit_process", "operations", "materials_infra"]] = Query(
        default="unit_process",
        description="4대 업무 분야 분류 필터"
    ),
    expanded_id: Optional[str] = Query(default=None, alias="expandedId", description="기본 활성화할 개념 ID"),
    db: AsyncSession = Depends(get_db)
):
    target_facet = facet or "unit_process"
    cache_key = f"concept:tree:{target_facet}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return ConceptTreeResponse(**cached)

    # 1. 대상 패싯의 개념 전체 조회
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
        cat_id = f"cat-{re.sub(r'[^a-zA-Z0-9]+', '-', cat_name.lower()).strip('-')}"
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
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    db: AsyncSession = Depends(get_db)
):
    role = get_current_user_role(x_user_role)
    cache_key = f"concept:detail:{concept_id}:{role}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return ConceptDetailResponse(**cached)

    # 1. Concept 및 연관 Perspectives Eager Loading
    stmt = (
        select(ConceptModel)
        .options(selectinload(ConceptModel.perspectives))
        .where(ConceptModel.id == concept_id)
    )
    res = await db.execute(stmt)
    concept = res.scalar_one_or_none()

    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept '{concept_id}' not found in ontology knowledge base."
        )

    # 2. 실무 사례 DTO 매핑 및 5.4절 Tier 3 마스킹 엔진 적용
    perspectives_dto = []
    for p in concept.perspectives:
        raw_dict = {
            "id": p.id,
            "concept_id": p.concept_id,
            "perspective_id": p.perspective_id,
            "perspective_title": p.perspective_title,
            "perspective_badge": p.perspective_badge,
            "management_code": p.management_code,
            "context_narrative": p.context_narrative,
            "specifications": p.specifications if isinstance(p.specifications, list) else [],
            "caution": p.caution,
            "evidence_id": p.evidence_id,
            "is_masked": False
        }
        processed = mask_tier3_perspective(raw_dict, role)
        perspectives_dto.append(PerspectiveCaseDTO(**processed))

    # 3. 0ms 팝오버를 위한 연관 개념 사전 적재 (Preloaded Explainers)
    preloaded_explainers: Dict[str, ContextualExplanationDTO] = {}
    rel_ids = set()
    edge_mechanisms: Dict[str, str] = {}

    # (1) relations JSON 필드 기반 연관 개념 수집 (전공정/후공정/소자 공통)
    if isinstance(concept.relations, dict):
        for key in ["causes", "causedBy", "competing", "children", "parents", "alternative_to"]:
            items = concept.relations.get(key, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        cid = item.get("id") or item.get("targetId")
                        if cid:
                            rel_ids.add(cid)
                    elif isinstance(item, str):
                        rel_ids.add(item)

    # (2) causal_edges 물리 테이블 기반 1-hop 연관 개념 및 메커니즘 수집
    edge_stmt = select(CausalEdgeModel).where(
        (CausalEdgeModel.source_concept_id == concept_id) |
        (CausalEdgeModel.target_concept_id == concept_id)
    )
    edge_rows = (await db.execute(edge_stmt)).scalars().all()
    for e in edge_rows:
        other_id = e.target_concept_id if e.source_concept_id == concept_id else e.source_concept_id
        rel_ids.add(other_id)
        if e.mechanism_label:
            edge_mechanisms[other_id] = e.mechanism_label

    if rel_ids:
        rel_stmt = select(ConceptModel).where(ConceptModel.id.in_(rel_ids))
        rel_res = await db.execute(rel_stmt)
        for rc in rel_res.scalars().all():
            mech = edge_mechanisms.get(rc.id)
            context_sentence = (
                f"[{concept.title} ➔ {rc.title} 인과 메커니즘] {mech}"
                if mech else f"{concept.title} 본문에서 참조되는 연관 개념 ({rc.process_category})."
            )
            preloaded_explainers[rc.id] = ContextualExplanationDTO(
                child_concept_id=rc.id,
                parent_concept_id=concept.id,
                title=rc.title,
                definition=rc.summary,
                context_sentence=context_sentence,
                cached=True,
                source_evidence=None,
                deep_link=f"/wiki?concept={rc.id}"
            )

    response_dto = ConceptDetailResponse(
        id=concept.id,
        title=concept.title,
        eng_name=concept.eng_name,
        aliases=concept.aliases if isinstance(concept.aliases, list) else [],
        domain_facet=concept.domain_facet,
        process_category=concept.process_category,
        scale_level=concept.scale_level,
        scale_name=concept.scale_name,
        version=concept.version,
        status=concept.status,
        last_reviewed_at=concept.last_reviewed_at.isoformat() if concept.last_reviewed_at else None,
        last_reviewed_by=concept.last_reviewed_by,
        summary=concept.summary,
        purpose=concept.purpose,
        principles=concept.principles if isinstance(concept.principles, list) else [],
        limitations=concept.limitations if isinstance(concept.limitations, list) else [],
        relations=concept.relations if isinstance(concept.relations, dict) else {},
        perspectives=perspectives_dto,
        preloaded_explainers=preloaded_explainers
    )

    await cache_manager.set(cache_key, response_dto.model_dump(by_alias=True), ttl_seconds=120)
    return response_dto


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
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"concept:subgraph:{concept_id}:{depth}:{direction}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return CausalSubgraphResponse(**cached)

    # 1. 중심 개념 존재 여부 확인
    center_check = await db.get(ConceptModel, concept_id)
    if not center_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Central concept '{concept_id}' not found."
        )

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
            (:dir = 'both' AND (ce.source_concept_id = cn.target_concept_id OR ce.target_concept_id = cn.source_concept_id))
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
            polarity=row.polarity or "+",
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
                    category="인과 파라미터/결함",
                    scale_level=3,
                    is_center=(nid == concept_id)
                )
            )

    response_dto = CausalSubgraphResponse(
        central_concept_id=concept_id,
        graph={
            "nodes": [n.model_dump(by_alias=True) for n in nodes_dto],
            "edges": [e.model_dump(by_alias=True) for e in edge_map.values()]
        }
    )

    await cache_manager.set(cache_key, response_dto.model_dump(by_alias=True), ttl_seconds=120)
    return response_dto


@router.get(
    "/{concept_id}/contextual-explainer",
    response_model=ContextualExplanationDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="용어 호버 시 0ms 인라인 문맥 해설 조회 API",
    description="위키 본문 용어에 마우스를 올렸을 때 인라인으로 띄워줄 공학적 정의와 부모 문맥 문장을 서빙합니다."
)
@router.get(
    "/{concept_id}/contextual-explain",
    response_model=ContextualExplanationDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    include_in_schema=False
)
async def get_contextual_explainer(
    concept_id: str,
    term_id: str = Query(..., description="마우스오버된 용어/하위 개념 식별자"),
    perspective_id: Optional[str] = Query("default", description="현재 활성 관점"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    db: AsyncSession = Depends(get_db)
):
    # 3.6절 Explainer Agent 호출 (가드레일 '현재 공정 맥락({parentName}):' 보장)
    try:
        explainer_resp = await explainer_agent.get_explanation(
            child_id=term_id,
            parent_id=concept_id,
            perspective_id=perspective_id,
            db=db,
            gemini_key=x_gemini_key,
            openai_key=x_openai_key
        )
        return ContextualExplanationDTO(
            child_concept_id=explainer_resp.childConceptId,
            parent_concept_id=explainer_resp.parentConceptId,
            title=explainer_resp.childConceptName,
            definition=explainer_resp.fallbackDefinition,
            context_sentence=explainer_resp.contextualExplanation,
            cached=True,
            source_evidence={"evidenceIds": explainer_resp.evidenceIds},
            deep_link=f"/wiki?concept={explainer_resp.childConceptId}"
        )
    except Exception as e:
        logger.warning(f"Explainer agent error, falling back to deterministic: {e}")
        child_concept = await db.get(ConceptModel, term_id)
        parent_concept = await db.get(ConceptModel, concept_id)
        p_name = parent_concept.title if parent_concept else concept_id
        c_title = child_concept.title if child_concept else term_id
        c_def = child_concept.summary if child_concept else f"{term_id} 정의"

        return ContextualExplanationDTO(
            child_concept_id=term_id,
            parent_concept_id=concept_id,
            title=c_title,
            definition=c_def,
            context_sentence=f"현재 공정 맥락({p_name}): {p_name}의 신뢰성 및 수율 안정성을 확보하기 위해 직접적으로 연계되는 핵심 구성 요소입니다.",
            cached=True,
            source_evidence=None,
            deep_link=f"/wiki?concept={term_id}"
        )
