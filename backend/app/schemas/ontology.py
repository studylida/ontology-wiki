"""Ontology Core Pydantic v2 Schemas.

Covers Concept, PerspectiveCase, CausalEdge, EvidenceSource and Subgraph DTOs with camelCase serialization.
"""
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EvidenceSourceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str = Field(..., description="출처 식별자 (예: 'E-01')")
    sourceName: str = Field(..., alias="source_name", serialization_alias="sourceName")
    sourceType: str = Field(..., alias="source_type", serialization_alias="sourceType")
    publisher: str
    publishedDate: Optional[str] = Field(None, alias="published_date", serialization_alias="publishedDate")
    quote: str
    sectionContext: Optional[str] = Field(None, alias="section_context", serialization_alias="sectionContext")
    relevanceScore: Optional[float] = Field(1.0, alias="relevance_score", serialization_alias="relevanceScore")
    externalUrl: str = Field(..., alias="external_url", serialization_alias="externalUrl")
    urlLabel: str = Field(..., alias="url_label", serialization_alias="urlLabel")
    credibilityTier: str = Field(..., alias="credibility_tier", serialization_alias="credibilityTier")
    referencedConcepts: Optional[List[Dict[str, Any]]] = Field(default_factory=list, alias="referenced_concepts", serialization_alias="referencedConcepts")


class CompensatingParamSchema(BaseModel):
    """🌟 도메인 필수 용어: 보상 파라미터 (Compensating Parameters)."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    parameter: str = Field(..., description="보상 대상 파라미터 (예: '초음파 인가 시간')")
    compensationFormula: str = Field(..., alias="compensation_formula", serialization_alias="compensationFormula", description="보상 수식 (예: 'Δt = +120ms / -15N')")
    tradeoffCost: str = Field(..., alias="tradeoff_cost", serialization_alias="tradeoffCost", description="트레이드오프 비용 (예: '택트타임 8.5% 증가')")


class CausalEdgeDTO(BaseModel):
    """온톨로지 인과 엣지 DTO (PostgreSQL 16 causal_edges 매핑)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: Optional[int] = None
    sourceConceptId: str = Field(..., alias="source_concept_id", serialization_alias="sourceConceptId")
    targetConceptId: str = Field(..., alias="target_concept_id", serialization_alias="targetConceptId")
    relationType: str = Field(..., alias="relation_type", serialization_alias="relationType")
    polarity: Optional[str] = "+"
    weight: float = 1.00
    mechanismLabel: str = Field(..., alias="mechanism_label", serialization_alias="mechanismLabel")
    compensatingParams: Optional[CompensatingParamSchema] = Field(None, alias="compensating_params", serialization_alias="compensatingParams")

    evidenceId: Optional[str] = Field(None, alias="evidence_id", serialization_alias="evidenceId")


class CaseContextContentDTO(BaseModel):
    explanation: str
    background: Optional[str] = None

    @field_validator("explanation")
    @classmethod
    def nonempty_explanation(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("explanation must not be empty")
        return value


class CaseContextExplanationDTO(BaseModel):
    basisHash: str
    generatorVersion: str
    generatedAt: str
    content: CaseContextContentDTO


class PerspectiveCaseDTO(BaseModel):
    """적응형 Level 3 실무 사례 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str
    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId")
    perspectiveId: str = Field(..., alias="perspective_id", serialization_alias="perspectiveId")
    perspectiveTitle: str = Field(..., alias="perspective_title", serialization_alias="perspectiveTitle")
    perspectiveBadge: str = Field(..., alias="perspective_badge", serialization_alias="perspectiveBadge")
    managementCode: Optional[str] = Field(None, alias="management_code", serialization_alias="managementCode")
    contextNarrative: str = Field(..., alias="context_narrative", serialization_alias="contextNarrative")
    specifications: List[Dict[str, Any]] = Field(default_factory=list)
    caution: str
    evidenceId: Optional[str] = Field(None, alias="evidence_id", serialization_alias="evidenceId")
    isMasked: bool = Field(False, alias="is_masked", serialization_alias="isMasked")
    maskReason: Optional[str] = Field(None, alias="mask_reason", serialization_alias="maskReason")
    relativeTrend: Optional[str] = Field(None, alias="relative_trend", serialization_alias="relativeTrend")
    accessRequestCTA: Optional[str] = Field(None, alias="access_request_cta", serialization_alias="accessRequestCTA")
    contextExplanation: Optional[CaseContextExplanationDTO] = Field(None, alias="context_explanation", serialization_alias="contextExplanation")
    contextExplanationState: Literal["ready", "missing", "stale", "generating", "restricted"] = "missing"
    contextExplanationBasisHash: Optional[str] = None


class PrincipleStep(BaseModel):
    step: int
    title: str
    content: str
    formula: Optional[str] = None


class LimitationItem(BaseModel):
    title: str
    description: str
    evidenceIds: List[str] = Field(default_factory=list, alias="evidence_ids", serialization_alias="evidenceIds")


class ConceptDTO(BaseModel):
    """온톨로지 핵심 개념 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str
    title: str
    engName: str = Field(..., alias="eng_name", serialization_alias="engName")
    aliases: List[str] = Field(default_factory=list)
    domainFacet: Literal["device", "unit_process", "operations", "materials_infra"] = Field(..., alias="domain_facet", serialization_alias="domainFacet")
    processCategory: str = Field(..., alias="process_category", serialization_alias="processCategory")
    scaleLevel: int = Field(..., alias="scale_level", serialization_alias="scaleLevel", ge=1, le=5)
    scaleName: Optional[str] = Field(None, alias="scale_name", serialization_alias="scaleName")
    version: str = "v1.2"
    status: Literal["adopted", "in_review", "deprecated"] = "adopted"
    lastReviewedAt: Optional[str] = Field(None, alias="last_reviewed_at", serialization_alias="lastReviewedAt")
    lastReviewedBy: Optional[str] = Field(None, alias="last_reviewed_by", serialization_alias="lastReviewedBy")
    summary: str
    purpose: str
    principles: List[Union[Dict[str, Any], str]] = Field(default_factory=list)
    limitations: List[Union[Dict[str, Any], str]] = Field(default_factory=list)
    relations: Dict[str, Any] = Field(default_factory=dict)


class ContextualExplanationDTO(BaseModel):
    """0ms 용어 호버 인라인 문맥 해설 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    childConceptId: Optional[str] = Field(None, alias="child_concept_id", serialization_alias="childConceptId")
    parentConceptId: str = Field(..., alias="parent_concept_id", serialization_alias="parentConceptId")
    title: str
    definition: str
    contextSentence: str = Field(..., alias="context_sentence", serialization_alias="contextSentence")
    cached: bool = True
    sourceEvidence: Optional[Dict[str, Any]] = Field(None, alias="source_evidence", serialization_alias="sourceEvidence")
    deepLink: Optional[str] = Field(None, alias="deep_link", serialization_alias="deepLink")


class ContextualExplanationRequest(BaseModel):
    term_id: str = Field(..., min_length=1, max_length=60)
    selection_context: str = Field("", max_length=600)
    perspective_id: str = "default"


class ContextualExplanationContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    definition: str = Field(..., min_length=1, max_length=800)
    contextSentence: str = Field(..., min_length=1, max_length=1600)


class ConceptDetailResponse(ConceptDTO):
    """위키 본문 상세 조회 통합 응답 DTO."""
    perspectives: List[PerspectiveCaseDTO] = Field(default_factory=list)
    evidenceIds: List[str] = Field(default_factory=list, alias="evidence_ids", serialization_alias="evidenceIds")
    selectionTerms: List[str] = Field(default_factory=list, alias="selection_terms", serialization_alias="selectionTerms")
    preloadedExplainers: Optional[Dict[str, ContextualExplanationDTO]] = Field(
        default_factory=dict, alias="preloaded_explainers", serialization_alias="preloadedExplainers"
    )
    enrichedRelations: Optional["EnrichedRelationsDTO"] = Field(
        None, alias="enriched_relations", serialization_alias="enrichedRelations"
    )
    scaleLadder: List["ScaleLadderStepDTO"] = Field(
        default_factory=list, alias="scale_ladder", serialization_alias="scaleLadder"
    )


class EnrichedRelationItemDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    name: str
    relationType: Optional[str] = Field(None, alias="relation_type", serialization_alias="relationType")
    reason: Optional[str] = None
    mechanism: Optional[str] = None
    scaleLevel: Optional[int] = Field(None, alias="scale_level", serialization_alias="scaleLevel")
    isRegistered: bool = Field(True, alias="is_registered", serialization_alias="isRegistered")
    commonGoal: Optional[str] = Field(None, alias="common_goal", serialization_alias="commonGoal")
    tradeoff: Optional[str] = None
    evidenceIds: List[str] = Field(default_factory=list, alias="evidence_ids", serialization_alias="evidenceIds")
    evidenceQuote: Optional[str] = Field(None, alias="evidence_quote", serialization_alias="evidenceQuote")
    compensatingParams: Optional[CompensatingParamSchema] = Field(None, alias="compensating_params", serialization_alias="compensatingParams")


class EnrichedRelationsDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    previousSteps: List[EnrichedRelationItemDTO] = Field(default_factory=list, alias="previous_steps", serialization_alias="previousSteps")
    nextSteps: List[EnrichedRelationItemDTO] = Field(default_factory=list, alias="next_steps", serialization_alias="nextSteps")
    alternatives: List[EnrichedRelationItemDTO] = Field(default_factory=list)
    partOf: List[EnrichedRelationItemDTO] = Field(default_factory=list, alias="part_of", serialization_alias="partOf")
    isA: List[EnrichedRelationItemDTO] = Field(default_factory=list, alias="is_a", serialization_alias="isA")
    hasParts: List[EnrichedRelationItemDTO] = Field(default_factory=list)
    subtypes: List[EnrichedRelationItemDTO] = Field(default_factory=list)


class ScaleLadderStepDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    scaleLevel: int = Field(..., alias="scale_level", serialization_alias="scaleLevel")
    scaleName: str = Field(..., alias="scale_name", serialization_alias="scaleName")
    title: str
    description: str
    governingPhysics: Optional[str] = Field(None, alias="governing_physics", serialization_alias="governingPhysics")
    connections: List["SubgraphEdge"] = Field(default_factory=list)
    hops: int = Field(0, ge=0, le=2)
    isCurrent: bool = Field(False, alias="is_current", serialization_alias="isCurrent")
    entityId: Optional[str] = Field(None, alias="entity_id", serialization_alias="entityId")
    entityName: Optional[str] = Field(None, alias="entity_name", serialization_alias="entityName")


class SubgraphNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    label: str
    category: str
    scaleLevel: Optional[int] = Field(3, alias="scale_level", serialization_alias="scaleLevel")
    isCenter: bool = Field(False, alias="is_center", serialization_alias="isCenter")
    isRegistered: bool = Field(True, alias="is_registered", serialization_alias="isRegistered")


class SubgraphEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    source: str
    target: str
    relationType: str = Field(..., alias="relation_type", serialization_alias="relationType")
    polarity: Optional[str] = "+"
    weight: float = 1.00
    mechanismLabel: str = Field(..., alias="mechanism_label", serialization_alias="mechanismLabel")
    compensatingParams: Optional[CompensatingParamSchema] = Field(None, alias="compensating_params", serialization_alias="compensatingParams")
    evidenceId: Optional[str] = Field(None, alias="evidence_id", serialization_alias="evidenceId")


class CausalSubgraphResponse(BaseModel):
    """Cytoscape 캔버스 렌더링용 1~2 hop 인과 서브그래프 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    centralConceptId: str = Field(..., alias="central_concept_id", serialization_alias="centralConceptId")
    graph: Dict[str, Any]  # { "nodes": List[SubgraphNode], "edges": List[SubgraphEdge] }
    hasRelations: bool = Field(False, alias="has_relations", serialization_alias="hasRelations")


class ConceptTreeNode(BaseModel):
    """좌측 사이드바 온톨로지 네비게이션 트리 노드 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    title: str
    engName: Optional[str] = Field(None, alias="eng_name", serialization_alias="engName")
    aliases: List[str] = Field(default_factory=list)
    type: Literal["category", "concept"] = "concept"
    scaleLevel: Optional[int] = Field(None, alias="scale_level", serialization_alias="scaleLevel")
    badge: Optional[str] = None
    status: Optional[str] = "adopted"
    hasPerspectives: bool = Field(False, alias="has_perspectives", serialization_alias="hasPerspectives")
    children: List["ConceptTreeNode"] = Field(default_factory=list)


class ConceptTreeResponse(BaseModel):
    """좌측 사이드바 4축 계층형 온톨로지 네비게이션 트리 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    currentFacet: str = Field(..., alias="current_facet", serialization_alias="currentFacet")
    totalNodes: int = Field(..., alias="total_nodes", serialization_alias="totalNodes")
    tree: List[ConceptTreeNode]

