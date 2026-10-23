"""Deep Research Schemas for [Tab 4] External Literature and Whitepapers.

Covers session management, clarification, evidence feed discovery, synthesis, and review queue export.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ResearchSessionSummary(BaseModel):
    """외부 문헌 조사 세션 요약 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    searchTopic: str = Field(..., alias="search_topic", serialization_alias="searchTopic")
    evidenceCount: int = Field(0, alias="evidence_count", serialization_alias="evidenceCount")
    candidateCount: int = Field(0, alias="candidate_count", serialization_alias="candidateCount")
    createdAt: str = Field(..., alias="created_at", serialization_alias="createdAt")


class ResearchSessionListResponse(BaseModel):
    """사이드바 문헌 조사 로그 목록 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    totalSessions: int = Field(..., alias="total_sessions", serialization_alias="totalSessions")
    sessions: List[ResearchSessionSummary]


class ScopeFilter(BaseModel):
    """조사 범위 추천 필터 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    filterId: str = Field(..., alias="filter_id", serialization_alias="filterId")
    label: str
    selected: bool = True


class ResearchSearchPlan(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    originalQuestion: str = Field(..., min_length=2, max_length=4000)
    interpretedQuestion: str = Field(..., min_length=2, max_length=4000)
    assumptions: List[str] = Field(default_factory=list)
    searchQueries: List[str] = Field(default_factory=list, max_length=4)
    clarificationQuestion: Optional[str] = None
    status: Literal["ready", "needs_clarification", "source_only"] = "ready"


class ResearchReadSegment(BaseModel):
    id: str
    text: str
    sectionContext: Optional[str] = None
    sourceUrl: Optional[str] = None
    contentKind: Optional[str] = None


class ResearchEvidenceAssessment(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    decision: Literal["included", "deferred", "excluded"]
    documentSummary: str = Field(..., min_length=1)
    inclusionReason: str = Field(..., min_length=1)
    usefulness: str
    limitations: List[str] = Field(default_factory=list)
    evidenceReferences: List[str] = Field(default_factory=list)


class ResearchAssessmentEntry(BaseModel):
    id: str
    assessment: ResearchEvidenceAssessment


class ResearchScreeningEntry(BaseModel):
    id: str
    priority: Literal["high", "normal", "low"] = "normal"
    reason: str = ""


class ResearchScreeningDraft(BaseModel):
    candidates: List[ResearchScreeningEntry] = Field(default_factory=list)


class ResearchAssessmentDraft(BaseModel):
    assessments: List[ResearchAssessmentEntry] = Field(default_factory=list)
    followUpQueries: List[str] = Field(default_factory=list, max_length=4)
    remainingQuestions: List[str] = Field(default_factory=list)


class ResearchDiscoveryContext(BaseModel):
    plan: ResearchSearchPlan
    queriesExecuted: List[str] = Field(default_factory=list)
    generationStatus: Literal["complete", "partial", "source_only"]
    remainingQuestions: List[str] = Field(default_factory=list)
    stopReason: str
    pendingQueries: List[str] = Field(default_factory=list)
    searchRounds: List[Dict[str, Any]] = Field(default_factory=list)
    canContinue: bool = False
    schemaVersion: int = 1


class ResearchContinueRequest(BaseModel):
    expectedUpdatedAt: str


class ResearchClarifyRequest(BaseModel):
    """문헌 발굴 전 주제 구체화 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    searchTopic: str = Field(..., min_length=2, alias="search_topic", serialization_alias="searchTopic", description="조사 기술 주제")
    preferredTier: Optional[List[str]] = Field(default_factory=list, alias="preferred_tier", serialization_alias="preferredTier")
    targetInstitutions: List[str] = Field(default_factory=list)
    comparisonContext: Optional["ComparisonResearchContext"] = None
    clarificationAnswer: str = Field("", max_length=4000)


class ResearchClarifyResponse(BaseModel):
    """문헌 발굴 전 주제 구체화 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    searchTopic: str = Field(..., alias="search_topic", serialization_alias="searchTopic")
    trustPoolNotice: str = Field(..., alias="trust_pool_notice", serialization_alias="trustPoolNotice")
    scopeFilters: List[ScopeFilter] = Field(..., alias="scope_filters", serialization_alias="scopeFilters")
    targetInstitutions: List[str] = Field(..., alias="target_institutions", serialization_alias="targetInstitutions")
    negativeKeywords: List[str] = Field(..., alias="negative_keywords", serialization_alias="negativeKeywords")
    suggestedChips: List[str] = Field(..., alias="suggested_chips", serialization_alias="suggestedChips")
    searchPlan: Optional[ResearchSearchPlan] = None


class ComparisonResearchContext(BaseModel):
    comparisonSessionId: str
    originalQuestion: str = ""
    targetA: str = ""
    targetB: str = ""
    targetAName: str = ""
    targetBName: str = ""
    gapAxis: str = ""
    targetSide: str = ""
    conditions: List[str] = Field(default_factory=list)


class ResearchDiscoverRequest(BaseModel):
    """공인 문헌 발굴 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    searchTopic: str = Field(..., min_length=2, alias="search_topic", serialization_alias="searchTopic")
    targetInstitutions: Optional[List[str]] = Field(default_factory=list, alias="target_institutions", serialization_alias="targetInstitutions")
    preferredTier: Optional[List[str]] = Field(default_factory=list, alias="preferred_tier", serialization_alias="preferredTier")
    comparisonContext: Optional[ComparisonResearchContext] = None
    searchPlan: Optional[ResearchSearchPlan] = None
    clarificationAnswer: str = Field("", max_length=4000)


class ResearchEvidenceFeedItem(BaseModel):
    """발굴된 공인 문헌 피드 카드 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    sourceName: str = Field(..., alias="source_name", serialization_alias="sourceName")
    sourceType: str = Field(..., alias="source_type", serialization_alias="sourceType")
    publisher: str
    publishedDate: Optional[str] = Field(None, alias="published_date", serialization_alias="publishedDate")
    quote: str
    sectionContext: Optional[str] = Field(None, alias="section_context", serialization_alias="sectionContext")
    relevanceScore: Optional[float] = Field(None, alias="relevance_score", serialization_alias="relevanceScore")
    externalUrl: str = Field(..., alias="external_url", serialization_alias="externalUrl")
    urlLabel: str = Field(..., alias="url_label", serialization_alias="urlLabel")
    credibilityTier: str = Field(..., alias="credibility_tier", serialization_alias="credibilityTier")
    retrievalStatus: str = "legacy_unverified"
    readSegments: List[ResearchReadSegment] = Field(default_factory=list)
    assessment: Optional[ResearchEvidenceAssessment] = None
    deferReason: Optional[Literal["content_unavailable", "insufficient_content", "not_assessed", "assessment_failed"]] = None
    contentLinks: List[str] = Field(default_factory=list)
    acquisitionAttempts: List[Dict[str, Any]] = Field(default_factory=list)
    screening: Optional[ResearchScreeningEntry] = None
    assessmentInputHash: Optional[str] = None
    assessmentCurrent: bool = True


class ResearchDiscoverResponse(BaseModel):
    """공인 문헌 발굴 피드 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    sessionId: str = Field(..., alias="session_id", serialization_alias="sessionId")
    searchTopic: str = Field(..., alias="search_topic", serialization_alias="searchTopic")
    totalEvidencesFound: int = Field(..., alias="total_evidences_found", serialization_alias="totalEvidencesFound")
    evidenceFeed: List[ResearchEvidenceFeedItem] = Field(..., alias="evidence_feed", serialization_alias="evidenceFeed")
    synthesisReady: bool = Field(True, alias="synthesis_ready", serialization_alias="synthesisReady")
    ctaButtonLabel: str = Field("📊 이 문헌들로 종합 분석 리포트 생성 (리포트 보기 ➔)", alias="cta_button_label", serialization_alias="ctaButtonLabel")
    comparisonContext: Optional[Dict[str, Any]] = None
    notice: str = ""
    discoveryContext: Optional[ResearchDiscoveryContext] = None
    updatedAt: Optional[str] = None


class ResearchSynthesizeRequest(BaseModel):
    """종합 분석 리포트 생성 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    selectedEvidenceIds: List[str] = Field(..., min_length=1, alias="selected_evidence_ids", serialization_alias="selectedEvidenceIds")


class SynthesisReport(BaseModel):
    """교차 분석 종합 리포트 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    title: str
    narrativeMarkdown: str = Field(..., alias="narrative_markdown", serialization_alias="narrativeMarkdown")
    consensusFacts: List[str] = Field(..., alias="consensus_facts", serialization_alias="consensusFacts")
    tensionGaps: List[str] = Field(..., alias="tension_gaps", serialization_alias="tensionGaps")
    comparisonContext: Optional[Dict[str, Any]] = None
    generationStatus: Literal["ai_generated", "source_only", "legacy_unverified"] = "legacy_unverified"
    evidenceSignature: Optional[str] = None
    evidenceIds: List[str] = Field(default_factory=list)
    needsRefresh: bool = False


class KnowledgeCandidate(BaseModel):
    """도출된 신규 온톨로지 지식 후보 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    candidateId: str = Field(..., alias="candidate_id", serialization_alias="candidateId")
    candidateType: str = Field(..., alias="candidate_type", serialization_alias="candidateType")
    title: str
    summary: str
    draftPayload: Dict[str, Any] = Field(..., alias="draft_payload", serialization_alias="draftPayload")
    evidenceIds: List[str] = Field(default_factory=list, alias="evidence_ids", serialization_alias="evidenceIds")


class ResearchNewConceptDraft(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=1)
    engName: Optional[str] = None
    content: str = Field(..., min_length=1)
    purpose: str = ""
    domainFacet: Optional[Literal["device", "unit_process", "operations", "materials_infra"]] = None
    scaleLevel: Optional[int] = Field(None, ge=1, le=5)
    processCategory: str = ""


class ResearchSynthesizeResponse(BaseModel):
    """종합 분석 리포트 및 지식 후보 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    sessionId: str = Field(..., alias="session_id", serialization_alias="sessionId")
    searchTopic: str = Field(..., alias="search_topic", serialization_alias="searchTopic")
    synthesisReport: SynthesisReport = Field(..., alias="synthesis_report", serialization_alias="synthesisReport")
    candidates: List[KnowledgeCandidate]
    comparisonContext: Optional[Dict[str, Any]] = None
    updatedAt: Optional[str] = None


class ResearchSynthesisDraft(BaseModel):
    report: SynthesisReport
    candidates: List[KnowledgeCandidate] = Field(default_factory=list)


class ResearchSessionDetail(BaseModel):
    sessionId: str
    searchTopic: str
    evidenceFeed: List[ResearchEvidenceFeedItem] = Field(default_factory=list)
    synthesisReport: Optional[SynthesisReport] = None
    candidates: List[KnowledgeCandidate] = Field(default_factory=list)
    comparisonContext: Optional[Dict[str, Any]] = None
    notice: Optional[str] = None
    targetInstitutions: List[str] = Field(default_factory=list)
    discoveryContext: Optional[ResearchDiscoveryContext] = None
    updatedAt: Optional[str] = None


class ExportCandidateTicketRequest(BaseModel):
    """지식 후보 ➔ 검토 센터 큐 등록 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    sessionId: str = Field(..., alias="session_id", serialization_alias="sessionId")
    author: Optional[str] = None
    department: Optional[str] = None
    userNote: str = Field(..., alias="user_note", serialization_alias="userNote", description="검토 제안 사유 및 설명")


class ExportCandidateTicketResponse(BaseModel):
    """지식 후보 ➔ 검토 센터 큐 등록 완료 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    candidateId: str = Field(..., alias="candidate_id", serialization_alias="candidateId")
    status: str = "pending"
    conceptTitle: str = Field(..., alias="concept_title", serialization_alias="conceptTitle")
    message: str
