"""Review & Approval Governance Schemas.

Covers ReviewTicket (2-Segment), overrideReason (사유), and WORM AuditLog.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class IntegrityReportSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    evidenceMatchRate: float = Field(..., alias="evidence_match_rate")
    hasOntologyConflict: bool = Field(..., alias="has_ontology_conflict")
    impactScopeCount: int = Field(..., alias="impact_scope_count")
    validationDetails: Optional[str] = Field("", alias="validation_details")
    conflictDetails: Optional[List[Dict[str, Any]]] = Field(default_factory=list, alias="conflict_details")


class DirectiveHistoryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    directiveId: Optional[str] = Field(None, alias="directive_id")
    directiveText: str = Field(..., alias="directive_text")
    targetLayer: Optional[str] = Field("hybrid", alias="target_layer")
    previousDraft: Optional[str] = Field(None, alias="previous_draft")
    revisedDraft: Optional[str] = Field(None, alias="revised_draft")
    overrideReason: Optional[str] = Field(None, alias="override_reason", description="🌟 도메인 필수: 사유 / overrideReason")
    timestamp: str


class ReviewTicketDTO(BaseModel):
    """지식 거버넌스 및 검토·승인 티켓 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    conceptId: str = Field(..., alias="concept_id")
    conceptTitle: str = Field(..., alias="concept_title")
    title: str
    reviewType: str = Field(..., alias="review_type")
    author: str
    department: Optional[str] = None
    submittedAt: Optional[str] = Field(None, alias="submitted_at")
    status: Literal["pending", "approved", "rejected"] = "pending"
    sourceSessionId: Optional[str] = Field(None, alias="source_session_id")
    originType: Optional[str] = Field(None, alias="origin_type")
    currentVersion: str = Field("v1.2", alias="current_version")
    targetVersion: Optional[str] = Field("v1.3", alias="target_version")
    currentContent: str = Field(..., alias="current_content")
    aiMergedDraft: str = Field(..., alias="ai_merged_draft")
    humanEdits: Optional[str] = Field(None, alias="human_edits")
    structuredPatches: Optional[Dict[str, Any]] = Field(None, alias="structured_patches")
    integrityReport: Dict[str, Any] = Field(..., alias="integrity_report")
    directiveHistory: List[Dict[str, Any]] = Field(default_factory=list, alias="directive_history")
    
    # 🌟 도메인 필수 용어: 사유 / overrideReason (금지어 "전문가 사유" 절대 사용 금지)
    overrideReason: Optional[str] = Field(None, alias="override_reason", description="사유 / overrideReason")
    
    approvedAt: Optional[str] = Field(None, alias="approved_at")
    approvedBy: Optional[str] = Field(None, alias="approved_by")
    appliedConceptVersion: Optional[str] = Field(None, alias="applied_concept_version")
    ticketVersion: int = Field(1, alias="ticket_version")


class AuditLogDTO(BaseModel):
    """WORM 불변 감사 로그 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    auditId: str = Field(..., alias="audit_id")
    ticketId: str = Field(..., alias="ticket_id")
    conceptId: str = Field(..., alias="concept_id")
    actionType: str = Field(..., alias="action_type")
    actor: Dict[str, Any]
    governanceSnapshot: Dict[str, Any] = Field(..., alias="governance_snapshot")
    previousLogHash: str = Field(..., alias="previous_log_hash")
    entryHash: str = Field(..., alias="entry_hash")
    digitalSignature: Optional[str] = Field(None, alias="digital_signature")
    timestamp: Optional[str] = None
