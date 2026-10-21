"""Review & Approval Governance Schemas.

Covers ReviewTicket (2-Segment), overrideReason (사유), and WORM AuditLog with camelCase serialization.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


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


class ReviewTicketApproveRequest(BaseModel):
    """지식 거버넌스 승인 집행 요청."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    approvedBy: Optional[str] = Field(None, alias="approved_by", serialization_alias="approvedBy", description="승인자 ID 또는 서명자 (토큰 인증 시 자동 주입)")
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason", description="🌟 표준 사유 / overrideReason")
    targetVersion: Optional[str] = Field(None, alias="target_version", serialization_alias="targetVersion", description="반영할 온톨로지 개념 버전 (미지정 시 티켓의 target_version)")
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
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    title: str = Field(..., description="신규 기술/개념명")
    summary: Optional[str] = Field("", description="핵심 기술 정의 및 도입 목적")


class ConceptPlacementRecommendResponse(BaseModel):
    """신규 개념 온톨로지 편입 위치 AI 추천 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    domainFacet: str = Field("unit_process", alias="domain_facet", serialization_alias="domainFacet")
    scaleLevel: int = Field(3, alias="scale_level", serialization_alias="scaleLevel")
    scaleName: str = Field("Scale 3: 단위 공정", alias="scale_name", serialization_alias="scaleName")
    processCategory: str = Field("첨단 패키징", alias="process_category", serialization_alias="processCategory")
    parentConceptId: Optional[str] = Field(None, alias="parent_concept_id", serialization_alias="parentConceptId")
    parentConceptTitle: Optional[str] = Field(None, alias="parent_concept_title", serialization_alias="parentConceptTitle")
    reasoning: str = Field("", description="에이전트 추천 사유")


class DirectiveRequest(BaseModel):
    """전문가 보완 지시문 반영 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    directiveText: str = Field(..., alias="directive_text", serialization_alias="directiveText")
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason")
    allowCitationDeletion: bool = Field(False, alias="allow_citation_deletion", serialization_alias="allowCitationDeletion", description="공인 출처 공식 폐기 명시적 인가 플래그")
    deprecatedCitations: Optional[List[str]] = Field(None, alias="deprecated_citations", serialization_alias="deprecatedCitations", description="공식 폐기할 공인 출처 태그 목록 (예: ['E-01'])")


class DirectiveResponse(BaseModel):
    """전문가 보완 지시문 반영 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    directiveText: str = Field(..., alias="directive_text", serialization_alias="directiveText")
    targetLayer: str = Field(..., alias="target_layer", serialization_alias="targetLayer")
    revisedDraft: str = Field(..., alias="revised_draft", serialization_alias="revisedDraft")
    structuredPatches: Dict[str, Any] = Field(..., alias="structured_patches", serialization_alias="structuredPatches")
    integrityReport: Dict[str, Any] = Field(..., alias="integrity_report", serialization_alias="integrityReport")
    addedDirective: DirectiveHistoryItem = Field(..., alias="added_directive", serialization_alias="addedDirective")


class HumanEditsRequest(BaseModel):
    """전문가 직접 편집 저장 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    editedContent: str = Field(..., alias="edited_content", serialization_alias="editedContent")
    ticketVersion: Optional[int] = Field(None, alias="ticket_version", serialization_alias="ticketVersion")
    overrideReason: Optional[str] = Field(None, alias="override_reason", serialization_alias="overrideReason")
    allowCitationDeletion: bool = Field(False, alias="allow_citation_deletion", serialization_alias="allowCitationDeletion", description="공인 출처 공식 폐기 명시적 인가 플래그")
    deprecatedCitations: Optional[List[str]] = Field(None, alias="deprecated_citations", serialization_alias="deprecatedCitations", description="공식 폐기할 공인 출처 태그 목록 (예: ['E-01'])")


class HumanEditsResponse(BaseModel):
    """전문가 직접 편집 저장 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    ticketVersion: int = Field(..., alias="ticket_version", serialization_alias="ticketVersion")
    humanEdits: str = Field(..., alias="human_edits", serialization_alias="humanEdits")
    integrityReport: Dict[str, Any] = Field(..., alias="integrity_report", serialization_alias="integrityReport")
    updatedAt: str = Field(..., alias="updated_at", serialization_alias="updatedAt")


class WikiPreviewResponse(BaseModel):
    """승인 전 위키 렌더링 미리보기 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId")
    targetVersion: str = Field(..., alias="target_version", serialization_alias="targetVersion")
    previewConcept: Dict[str, Any] = Field(..., alias="preview_concept", serialization_alias="previewConcept")
    diffSummary: Dict[str, Any] = Field(..., alias="diff_summary", serialization_alias="diffSummary")

