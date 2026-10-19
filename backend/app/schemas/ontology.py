"""Ontology Core Pydantic v2 Schemas.

Covers Concept, PerspectiveCase, CausalEdge, EvidenceSource and Subgraph DTOs.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class EvidenceSourceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(..., description="출처 식별자 (예: 'E-01')")
    sourceName: str = Field(..., alias="source_name")
    sourceType: str = Field(..., alias="source_type")
    publisher: str
    publishedDate: Optional[str] = Field(None, alias="published_date")
    quote: str
    sectionContext: Optional[str] = Field(None, alias="section_context")
    relevanceScore: Optional[float] = Field(1.0, alias="relevance_score")
    externalUrl: str = Field(..., alias="external_url")
    urlLabel: str = Field(..., alias="url_label")
    credibilityTier: str = Field(..., alias="credibility_tier")
    referencedConcepts: Optional[List[Dict[str, Any]]] = Field(default_factory=list, alias="referenced_concepts")


class CompensatingParamSchema(BaseModel):
    """🌟 도메인 필수 용어: 보상 파라미터 (Compensating Parameters)."""
    model_config = ConfigDict(populate_by_name=True)

    parameter: str = Field(..., description="보상 대상 파라미터 (예: '초음파 인가 시간')")
    compensationFormula: str = Field(..., alias="compensation_formula", description="보상 수식 (예: 'Δt = +120ms / -15N')")
    tradeoffCost: str = Field(..., alias="tradeoff_cost", description="트레이드오프 비용 (예: '택트타임 8.5% 증가')")


class CausalEdgeDTO(BaseModel):
    """온톨로지 인과 엣지 DTO (PostgreSQL 16 causal_edges 매핑)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[int] = None
    sourceConceptId: str = Field(..., alias="source_concept_id")
    targetConceptId: str = Field(..., alias="target_concept_id")
    relationType: str = Field(..., alias="relation_type")
    polarity: Optional[str] = "+"
    weight: float = 1.00
    mechanismLabel: str = Field(..., alias="mechanism_label")
    compensatingParams: Optional[CompensatingParamSchema] = Field(None, alias="compensating_params")
    evidenceId: Optional[str] = Field(None, alias="evidence_id")


class PerspectiveCaseDTO(BaseModel):
    """적응형 Level 3 실무 사례 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    conceptId: str = Field(..., alias="concept_id")
    perspectiveId: str = Field(..., alias="perspective_id")
    perspectiveTitle: str = Field(..., alias="perspective_title")
    perspectiveBadge: str = Field(..., alias="perspective_badge")
    managementCode: Optional[str] = Field(None, alias="management_code")
    contextNarrative: str = Field(..., alias="context_narrative")
    specifications: List[Dict[str, Any]] = Field(default_factory=list)
    caution: str
    evidenceId: Optional[str] = Field(None, alias="evidence_id")


class PrincipleStep(BaseModel):
    step: int
    title: str
    content: str
    formula: Optional[str] = None


class LimitationItem(BaseModel):
    title: str
    description: str
    evidenceIds: List[str] = Field(default_factory=list, alias="evidence_ids")


class ConceptDTO(BaseModel):
    """온톨로지 핵심 개념 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    engName: str = Field(..., alias="eng_name")
    aliases: List[str] = Field(default_factory=list)
    domainFacet: Literal["device", "unit_process", "operations", "materials_infra"] = Field(..., alias="domain_facet")
    processCategory: str = Field(..., alias="process_category")
    scaleLevel: int = Field(..., alias="scale_level", ge=1, le=5)
    scaleName: Optional[str] = Field(None, alias="scale_name")
    version: str = "v1.2"
    status: Literal["adopted", "in_review", "deprecated"] = "adopted"
    lastReviewedAt: Optional[str] = Field(None, alias="last_reviewed_at")
    lastReviewedBy: Optional[str] = Field(None, alias="last_reviewed_by")
    summary: str
    purpose: str
    principles: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[Dict[str, Any]] = Field(default_factory=list)
    relations: Dict[str, Any] = Field(default_factory=dict)


class ContextualExplanationDTO(BaseModel):
    """0ms 용어 호버 인라인 문맥 해설 DTO."""
    model_config = ConfigDict(populate_by_name=True)

    childConceptId: str = Field(..., alias="child_concept_id")
    parentConceptId: str = Field(..., alias="parent_concept_id")
    title: str
    definition: str
    contextSentence: str = Field(..., alias="context_sentence")
    cached: bool = True
    sourceEvidence: Optional[Dict[str, Any]] = Field(None, alias="source_evidence")
    deepLink: str = Field(..., alias="deep_link")


class ConceptDetailResponse(ConceptDTO):
    """위키 본문 상세 조회 통합 응답 DTO."""
    perspectives: List[PerspectiveCaseDTO] = Field(default_factory=list)
    preloadedExplainers: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="preloaded_explainers")


class SubgraphNode(BaseModel):
    id: str
    label: str
    category: str
    scaleLevel: Optional[int] = Field(3, alias="scale_level")
    isCenter: bool = Field(False, alias="is_center")


class SubgraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationType: str = Field(..., alias="relation_type")
    polarity: Optional[str] = "+"
    weight: float = 1.00
    mechanismLabel: str = Field(..., alias="mechanism_label")
    compensatingParams: Optional[CompensatingParamSchema] = Field(None, alias="compensating_params")
    evidenceId: Optional[str] = Field(None, alias="evidence_id")


class CausalSubgraphResponse(BaseModel):
    """Cytoscape 캔버스 렌더링용 1~2 hop 인과 서브그래프 DTO."""
    model_config = ConfigDict(populate_by_name=True)

    centralConceptId: str = Field(..., alias="central_concept_id")
    graph: Dict[str, Any]  # { "nodes": List[SubgraphNode], "edges": List[SubgraphEdge] }
