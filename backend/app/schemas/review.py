"""Review & Approval Governance Schemas.

Covers ReviewTicket (2-Segment), overrideReason (사유), and WORM AuditLog with camelCase serialization.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.app.schemas.source_ingestion import ExtractedConceptDiffDTO, ExtractedSpecificationDTO
from backend.app.schemas.ontology import PrincipleStep, LimitationItem


class IntegrityReportSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    evidenceMatchRate: float = Field(..., alias="evidence_match_rate", serialization_alias="evidenceMatchRate")
    hasOntologyConflict: bool = Field(..., alias="has_ontology_conflict", serialization_alias="hasOntologyConflict")
    impactScopeCount: int = Field(..., alias="impact_scope_count", serialization_alias="impactScopeCount")
    validationDetails: Optional[str] = Field("", alias="validation_details", serialization_alias="validationDetails")
    conflictDetails: Optional[List[Dict[str, Any]]] = Field(default_factory=list, alias="conflict_details", serialization_alias="conflictDetails")


class DirectiveHistoryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    directiveId: Optional[str] = Field(None, alias="directive_id", serialization_alias="directiveId")
    directiveText: str = Field(..., alias="directive_text", serialization_alias="directiveText")
    targetLayer: Optional[str] = Field("hybrid", alias="target_layer", serialization_alias="targetLayer")
    previousDraft: Optional[str] = Field(None, alias="previous_draft", serialization_alias="previousDraft")
    revisedDraft: Optional[str] = Field(None, alias="revised_draft", serialization_alias="revisedDraft")
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason", description="🌟 도메인 필수: 사유 / overrideReason")
    timestamp: str


class ReviewTicketDTO(BaseModel):
    """지식 거버넌스 및 검토·승인 티켓 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str
    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId")
    conceptTitle: str = Field(..., alias="concept_title", serialization_alias="conceptTitle")
    title: str
    reviewType: str = Field(..., alias="review_type", serialization_alias="reviewType")
    author: str
    department: Optional[str] = None
    submittedAt: Optional[str] = Field(None, alias="submitted_at", serialization_alias="submittedAt")
    status: Literal["pending", "approved", "rejected"] = "pending"
    sourceSessionId: Optional[str] = Field(None, alias="source_session_id", serialization_alias="sourceSessionId")
    originType: Optional[str] = Field(None, alias="origin_type", serialization_alias="originType")
    currentVersion: str = Field("v1.2", alias="current_version", serialization_alias="currentVersion")
    targetVersion: Optional[str] = Field("v1.3", alias="target_version", serialization_alias="targetVersion")
    currentContent: str = Field(..., alias="current_content", serialization_alias="currentContent")
    aiMergedDraft: str = Field(..., alias="ai_merged_draft", serialization_alias="aiMergedDraft")
    humanEdits: Optional[str] = Field(None, alias="human_edits", serialization_alias="humanEdits")
    structuredPatches: Optional[Any] = Field(None, alias="structured_patches", serialization_alias="structuredPatches")
    integrityReport: Dict[str, Any] = Field(..., alias="integrity_report", serialization_alias="integrityReport")
    directiveHistory: List[Dict[str, Any]] = Field(default_factory=list, alias="directive_history", serialization_alias="directiveHistory")
    
    # 사유 / overrideReason (실측 근거 및 변경 사유)
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason", description="사유 / overrideReason")
    
    approvedAt: Optional[str] = Field(None, alias="approved_at", serialization_alias="approvedAt")
    approvedBy: Optional[str] = Field(None, alias="approved_by", serialization_alias="approvedBy")
    appliedConceptVersion: Optional[str] = Field(None, alias="applied_concept_version", serialization_alias="appliedConceptVersion")
    workingDraft: Optional[Dict[str, Any]] = None
    editingMode: Literal["legacy", "structured"] = "legacy"
    canUndo: bool = False
    ticketVersion: int = Field(1, alias="ticket_version", serialization_alias="ticketVersion")


class AuditLogDTO(BaseModel):
    """WORM 불변 감사 로그 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    auditId: str = Field(..., alias="audit_id", serialization_alias="auditId")
    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId")
    actionType: str = Field(..., alias="action_type", serialization_alias="actionType")
    actor: Dict[str, Any]
    governanceSnapshot: Dict[str, Any] = Field(..., alias="governance_snapshot", serialization_alias="governanceSnapshot")
    previousLogHash: str = Field(..., alias="previous_log_hash", serialization_alias="previousLogHash")
    entryHash: str = Field(..., alias="entry_hash", serialization_alias="entryHash")
    digitalSignature: Optional[str] = Field(None, alias="digital_signature", serialization_alias="digitalSignature")
    timestamp: Optional[str] = None


class ReviewTicketDetailDTO(ReviewTicketDTO):
    """검토 티켓 상세 조회 DTO (동시 편집 락 상태 포함)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    currentEditor: Optional[str] = Field(None, alias="current_editor", serialization_alias="currentEditor")
    isLocked: bool = Field(False, alias="is_locked", serialization_alias="isLocked")


class PresenceLockRequest(BaseModel):
    """동시 편집 사전 차단 Presence Lock 요청."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    userId: Optional[str] = Field(None, alias="user_id", serialization_alias="userId", description="요청 엔지니어 ID (토큰 인증 시 자동 주입)")
    action: Literal["acquire", "renew", "release", "status", "steal"] = Field("acquire", description="락 제어 액션")
    ttlSeconds: int = Field(30, alias="ttl_seconds", serialization_alias="ttlSeconds", ge=5, le=300, description="락 유효 시간(초)")


class PresenceLockResponse(BaseModel):
    """Presence Lock 결과 응답."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    acquired: bool
    holder: Optional[str] = None
    isLocked: bool = Field(..., alias="is_locked", serialization_alias="isLocked")
    message: str


class ReviewConceptPlacement(BaseModel):
    domainFacet: Literal["device", "unit_process", "operations", "materials_infra"]
    scaleLevel: int = Field(..., ge=1, le=5, strict=True)
    processCategory: str = Field(..., min_length=1, max_length=64, pattern=r".*\S.*")


class ReviewTicketApproveRequest(BaseModel):
    previewSignature: Optional[str] = None
    """지식 거버넌스 승인 집행 요청."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True, extra="forbid")

    ticketVersion: Optional[int] = None
    approvedBy: Optional[str] = Field(None, alias="approved_by", serialization_alias="approvedBy", description="승인자 ID 또는 서명자 (토큰 인증 시 자동 주입)")
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason", description="🌟 표준 사유 / overrideReason")
    targetVersion: Optional[str] = Field(None, alias="target_version", serialization_alias="targetVersion", description="반영할 온톨로지 개념 버전 (미지정 시 티켓의 target_version)")
    conceptPlacement: Optional[ReviewConceptPlacement] = None
    humanEdits: Optional[str] = Field(None, alias="human_edits", serialization_alias="humanEdits", description="승인 시 최종 수정한 본문 내용 (미지정 시 기존 초안 유지)")
    allowCitationDeletion: bool = Field(False, alias="allow_citation_deletion", serialization_alias="allowCitationDeletion", description="공인 출처 공식 폐기 명시적 인가 플래그")
    deprecatedCitations: Optional[List[str]] = Field(None, alias="deprecated_citations", serialization_alias="deprecatedCitations", description="공식 폐기할 공인 출처 태그 목록 (예: ['E-01'])")


class ReviewTicketRejectRequest(BaseModel):
    """지식 거버넌스 반려 요청."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    rejectedBy: Optional[str] = Field(None, alias="rejected_by", serialization_alias="rejectedBy", description="반려 검토자 ID (토큰 인증 시 자동 주입)")
    rejectReason: str = Field(..., alias="reject_reason", serialization_alias="rejectReason", description="반려 사유 상세")


class ReviewTicketActionResponse(BaseModel):
    """승인 / 반려 처리 결과 응답."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ticket: ReviewTicketDTO
    auditLog: Optional[AuditLogDTO] = Field(None, alias="audit_log", serialization_alias="auditLog")
    conceptUpdated: bool = Field(False, alias="concept_updated", serialization_alias="conceptUpdated")
    conceptVersion: Optional[str] = Field(None, alias="concept_version", serialization_alias="conceptVersion")
    guideTip: Optional[str] = Field(None, alias="guide_tip", serialization_alias="guideTip")
    message: str


class ReviewTicketCreate(BaseModel):
    """위키 본문 간이 제안 모달 및 신규 문서 추가 발의 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    conceptId: Optional[str] = Field(None, alias="concept_id", serialization_alias="conceptId")
    isNewConcept: bool = Field(False, alias="is_new_concept", serialization_alias="isNewConcept")
    title: str
    engName: Optional[str] = Field(None, alias="eng_name", serialization_alias="engName")
    author: Optional[str] = Field("익명 엔지니어", description="발의자 (로그인 시 토큰 실명 자동 주입)")
    department: Optional[str] = "도메인개발팀"
    reviewType: str = Field("파라미터 수정", alias="review_type", serialization_alias="reviewType")
    originType: Optional[str] = Field("manual_expert", alias="origin_type", serialization_alias="originType")
    targetSection: Optional[str] = Field("limitations", alias="target_section", serialization_alias="targetSection")
    userNote: Optional[str] = Field(None, alias="user_note", serialization_alias="userNote")
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason")
    evidencePayload: Optional[Dict[str, Any]] = Field(None, alias="evidence_payload", serialization_alias="evidencePayload")

    # 🌟 온톨로지 편입 위치 지정 메타데이터 (신규 개념 등록 시 사용)
    domainFacet: Optional[str] = Field("unit_process", alias="domain_facet", serialization_alias="domainFacet")
    scaleLevel: Optional[int] = Field(3, alias="scale_level", serialization_alias="scaleLevel")
    scaleName: Optional[str] = Field("Scale 3: 단위 공정", alias="scale_name", serialization_alias="scaleName")
    processCategory: Optional[str] = Field("첨단 패키징", alias="process_category", serialization_alias="processCategory")
    parentConceptId: Optional[str] = Field(None, alias="parent_concept_id", serialization_alias="parentConceptId")

    @model_validator(mode="after")
    def validate_ticket_payload(self) -> "ReviewTicketCreate":
        if not self.isNewConcept and not self.conceptId:
            raise ValueError("기존 문서 개정 발의 시 conceptId는 필수입니다.")
        if self.isNewConcept and not self.title.strip():
            raise ValueError("신규 문서 발의 시 기술명(title)은 필수입니다.")
        return self


class ConceptPlacementRecommendRequest(BaseModel):
    """신규 개념 온톨로지 편입 위치 AI 추천 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True, str_strip_whitespace=True)

    title: str = Field(..., min_length=1, description="신규 기술/개념명")
    summary: Optional[str] = Field("", description="핵심 기술 정의 및 도입 목적")


class ConceptPlacementRecommendResponse(BaseModel):
    """신규 개념 온톨로지 편입 위치 AI 추천 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True, str_strip_whitespace=True)

    domainFacet: Literal["device", "unit_process", "operations", "materials_infra"] = Field(..., alias="domain_facet", serialization_alias="domainFacet")
    scaleLevel: int = Field(..., ge=1, le=5, strict=True, alias="scale_level", serialization_alias="scaleLevel")
    scaleName: str = Field(..., alias="scale_name", serialization_alias="scaleName")
    processCategory: str = Field(..., min_length=1, max_length=64, alias="process_category", serialization_alias="processCategory")
    parentConceptId: Optional[str] = Field(None, alias="parent_concept_id", serialization_alias="parentConceptId")
    parentConceptTitle: Optional[str] = Field(None, alias="parent_concept_title", serialization_alias="parentConceptTitle")
    reasoning: str = Field(..., min_length=1, description="분류 추천 사유 및 추천 방식")


class DirectiveKnowledgeItem(BaseModel):
    sourceId: str
    content: ExtractedConceptDiffDTO


class DirectiveSummaryEvidence(BaseModel):
    sourceId: str
    quote: str


class DirectivePrinciple(PrincipleStep):
    content: str = Field(..., description="현재 대상 자체의 작동 메커니즘. 다른 인접 공정의 설명이나 단순 정의는 제외")
    evidenceQuote: str


class DirectiveLimitation(LimitationItem):
    evidenceQuote: str


class DirectiveSpecification(ExtractedSpecificationDTO):
    evidenceQuote: str


class DirectiveCase(BaseModel):
    perspectiveTitle: str = Field(..., description="원문에서 구별되는 회사·제품·도메인·운영 조건. 일반 중요성 설명은 사례가 아님")
    perspectiveBadge: str = ""
    narrative: str
    caution: str = ""
    specifications: List[DirectiveSpecification] = Field(default_factory=list)
    evidenceQuote: str


class DirectiveLink(BaseModel):
    id: str
    name: str
    reason: Optional[str] = None
    evidenceQuote: str


class DirectiveAlternative(BaseModel):
    targetId: str
    targetName: str
    commonGoal: Optional[str] = None
    tradeoff: Optional[str] = None
    evidenceQuote: str


class DirectiveContent(BaseModel):
    summary: str = ""
    purpose: str = ""
    summaryEvidenceQuote: Optional[str] = None
    purposeEvidenceQuote: Optional[str] = None
    principles: List[DirectivePrinciple] = Field(default_factory=list)
    limitations: List[DirectiveLimitation] = Field(default_factory=list)
    perspectiveCases: List[DirectiveCase] = Field(default_factory=list)
    previousSteps: List[DirectiveLink] = Field(default_factory=list)
    nextSteps: List[DirectiveLink] = Field(default_factory=list)
    alternatives: List[DirectiveAlternative] = Field(default_factory=list)
    partOf: List[DirectiveLink] = Field(default_factory=list)
    isA: List[DirectiveLink] = Field(default_factory=list)


class DirectiveModelContribution(BaseModel):
    sourceId: str
    content: DirectiveContent


class DirectiveReplacement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceId: str
    editorId: str
    field: Literal["principles", "limitations", "perspectiveCases", "previousSteps", "nextSteps", "alternatives", "partOf", "isA"]
    content: DirectiveContent


class DirectiveModelProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contributions: List[DirectiveModelContribution]
    replacements: List[DirectiveReplacement] = Field(default_factory=list)
    summaryDraft: Optional[str] = None
    summaryEvidence: List[DirectiveSummaryEvidence] = Field(default_factory=list)


class DirectiveTextDecision(BaseModel):
    candidateIndex: int = Field(..., strict=True, ge=0)
    supported: bool = Field(..., strict=True)
    reason: str = Field(..., min_length=1)


class DirectiveTextReview(BaseModel):
    decisions: List[DirectiveTextDecision]


class DirectiveKnowledgePatch(BaseModel):
    schemaVersion: Literal[1] = 1
    baseSignature: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    contributions: List[DirectiveKnowledgeItem] = Field(default_factory=list)


class DirectiveRequest(BaseModel):
    """전문가 보완 지시문 반영 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True, extra="forbid")

    directiveText: str = Field(..., alias="directive_text", serialization_alias="directiveText")
    editedContent: Optional[str] = None
    ticketVersion: Optional[int] = None
    undoLast: bool = False
    structuredDraft: bool = False
    targetSections: Optional[List[Literal["summary", "principles", "limitations", "perspectiveCases", "relations", "evidences"]]] = None
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason")
    allowCitationDeletion: bool = Field(False, alias="allow_citation_deletion", serialization_alias="allowCitationDeletion", description="공인 출처 공식 폐기 명시적 인가 플래그")
    deprecatedCitations: Optional[List[str]] = Field(None, alias="deprecated_citations", serialization_alias="deprecatedCitations", description="공식 폐기할 공인 출처 태그 목록 (예: ['E-01'])")


class DraftItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    editorId: str = Field(min_length=1, max_length=128)

class PrincipleEdit(DraftItem):
    title: Optional[str] = None
    content: Optional[str] = None
    formula: Optional[str] = None
    evidenceIds: Optional[List[str]] = None

class LimitationEdit(DraftItem):
    title: Optional[str] = None
    description: Optional[str] = None
    evidenceIds: Optional[List[str]] = None

class SpecificationEdit(DraftItem):
    parameter: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    safetyMargin: Optional[str] = None
    role: Optional[str] = None
    tradeoff: Optional[str] = None
    rationale: Optional[str] = None
    isConfidential: Optional[bool] = None
    evidenceIds: Optional[List[str]] = None

class SpecificationChanges(BaseModel):
    model_config = ConfigDict(extra="forbid")
    upsert: List[SpecificationEdit] = Field(default_factory=list)
    remove: List[str] = Field(default_factory=list)
    order: Optional[List[str]] = None

class CaseEdit(DraftItem):
    perspectiveTitle: Optional[str] = None
    perspectiveBadge: Optional[str] = None
    narrative: Optional[str] = None
    caution: Optional[str] = None
    evidenceId: Optional[str] = None
    specifications: Optional[SpecificationChanges] = None

class RelationEdit(DraftItem):
    id: Optional[str] = None
    name: Optional[str] = None
    targetId: Optional[str] = None
    targetName: Optional[str] = None
    reason: Optional[str] = None
    commonGoal: Optional[str] = None
    tradeoff: Optional[str] = None
    evidenceIds: Optional[List[str]] = None

class EvidenceEdit(DraftItem):
    existingId: Optional[str] = None
    sourceName: Optional[str] = None
    publisher: Optional[str] = None
    quote: Optional[str] = None
    externalUrl: Optional[str] = None

class PrincipleChanges(SpecificationChanges):
    upsert: List[PrincipleEdit] = Field(default_factory=list)
class LimitationChanges(SpecificationChanges):
    upsert: List[LimitationEdit] = Field(default_factory=list)
class CaseChanges(SpecificationChanges):
    upsert: List[CaseEdit] = Field(default_factory=list)
class RelationChanges(SpecificationChanges):
    upsert: List[RelationEdit] = Field(default_factory=list)
class EvidenceChanges(SpecificationChanges):
    upsert: List[EvidenceEdit] = Field(default_factory=list)

class WorkingDraftChanges(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: Optional[str] = None
    purpose: Optional[str] = None
    principles: Optional[PrincipleChanges] = None
    limitations: Optional[LimitationChanges] = None
    perspectiveCases: Optional[CaseChanges] = None
    previousSteps: Optional[RelationChanges] = None
    nextSteps: Optional[RelationChanges] = None
    alternatives: Optional[RelationChanges] = None
    partOf: Optional[RelationChanges] = None
    isA: Optional[RelationChanges] = None
    evidences: Optional[EvidenceChanges] = None

class ReviewPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticketVersion: Optional[int] = None
    targetVersion: Optional[str] = None
    conceptPlacement: Optional[ReviewConceptPlacement] = None
    editedContent: Optional[str] = None

class HumanEditsRequest(BaseModel):
    """전문가 직접 편집 저장 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True, extra="forbid")

    editedContent: Optional[str] = Field(None, alias="edited_content", serialization_alias="editedContent")
    changes: Optional[WorkingDraftChanges] = None
    ticketVersion: Optional[int] = Field(None, alias="ticket_version", serialization_alias="ticketVersion")
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason")
    allowCitationDeletion: bool = Field(False, alias="allow_citation_deletion", serialization_alias="allowCitationDeletion", description="공인 출처 공식 폐기 명시적 인가 플래그")
    deprecatedCitations: Optional[List[str]] = Field(None, alias="deprecated_citations", serialization_alias="deprecatedCitations", description="공식 폐기할 공인 출처 태그 목록 (예: ['E-01'])")


    @model_validator(mode="after")
    def check_input(self):
        if (self.editedContent is None) == (self.changes is None):
            raise ValueError("editedContent 또는 changes 중 하나만 지정해 주세요.")
        if self.changes is not None and self.ticketVersion is None:
            raise ValueError("구조화 저장에는 ticketVersion이 필요합니다.")
        return self


class HumanEditsResponse(BaseModel):
    """전문가 직접 편집 저장 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    ticketVersion: int = Field(..., alias="ticket_version", serialization_alias="ticketVersion")
    workingDraft: Optional[Dict[str, Any]] = None
    humanEdits: str = Field(..., alias="human_edits", serialization_alias="humanEdits")
    integrityReport: Dict[str, Any] = Field(..., alias="integrity_report", serialization_alias="integrityReport")
    updatedAt: str = Field(..., alias="updated_at", serialization_alias="updatedAt")


class WikiPreviewResponse(BaseModel):
    """승인 전 위키 렌더링 미리보기 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId")
    targetVersion: str = Field(..., alias="target_version", serialization_alias="targetVersion")
    ticketVersion: int = 1
    previewSignature: Optional[str] = None
    workingDraft: Optional[Dict[str, Any]] = None
    previewConcept: Dict[str, Any] = Field(..., alias="preview_concept", serialization_alias="previewConcept")
    baselineConcept: Optional[Dict[str, Any]] = Field(None, alias="baseline_concept", serialization_alias="baselineConcept")
    diffSummary: Dict[str, Any] = Field(..., alias="diff_summary", serialization_alias="diffSummary")

