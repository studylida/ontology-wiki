"""Comparison Studio Schemas.

Covers ComparisonSession, 3-Step Snapshots, Tail-Questions (꼬리질문), and Tuning History with camelCase serialization.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TailQuestionEntry(BaseModel):
    """🌟 도메인 필수 용어: 꼬리질문 이력."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    query: str = Field(..., description="엔지니어가 던진 꼬리물기 질문")
    causalPath: List[str] = Field(..., alias="causal_path", serialization_alias="causalPath", description="인과 체인 경로 (예: ['가압력 누적', 'CTE 미스매치', '전단응력', '다이 휨'])")
    explanation: str = Field(..., description="물리 메커니즘 심층 해설")
    timestamp: str


class ParameterTuningEntry(BaseModel):
    """🌟 도메인 필수 용어: 보상 파라미터 (Compensating Parameters) 상담 이력."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    userPrompt: str = Field(..., alias="user_prompt", serialization_alias="userPrompt")
    advisorRecommendation: Dict[str, Any] = Field(..., alias="advisor_recommendation", serialization_alias="advisorRecommendation")


class ComparisonSessionCreate(BaseModel):
    """비교 세션 신규 생성 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    title: str = Field(..., description="비교 분석 세션 제목")
    userId: str = Field("EMP-CURRENT", alias="user_id", serialization_alias="userId")
    query: str = Field(..., description="분석 질의문 (예: MR-MUF vs TC-NCF)")
    contextParams: Dict[str, Any] = Field(default_factory=dict, alias="context_params", serialization_alias="contextParams")
    folderId: Optional[str] = Field(None, alias="folder_id", serialization_alias="folderId")


class ComparisonSessionDTO(BaseModel):
    """기술 대안 비교 세션 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str
    userId: str = Field(..., alias="user_id", serialization_alias="userId")
    title: str
    isPinned: bool = Field(False, alias="is_pinned", serialization_alias="isPinned")
    folderId: Optional[str] = Field(None, alias="folder_id", serialization_alias="folderId")
    query: str
    contextParams: Dict[str, Any] = Field(default_factory=dict, alias="context_params", serialization_alias="contextParams")
    snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    exportedReviewId: Optional[str] = Field(None, alias="exported_review_id", serialization_alias="exportedReviewId")
    createdAt: Optional[str] = Field(None, alias="created_at", serialization_alias="createdAt")
    updatedAt: Optional[str] = Field(None, alias="updated_at", serialization_alias="updatedAt")


class DeepDiveRequest(BaseModel):
    """엔지니어 꼬리질문 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    query: str = Field(..., description="심층 인과 꼬리질문 (예: 'TC-NCF에서 가압력 누적 시 휨이 발생하는 메커니즘은?')")
    stepIndex: int = Field(2, alias="step_index", serialization_alias="stepIndex", description="스냅샷 단계 인덱스 (기본 3단계: 2)")


class DeepDiveResponse(BaseModel):
    """엔지니어 꼬리질문 등록 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    sessionId: str = Field(..., alias="session_id", serialization_alias="sessionId")
    tailQuestion: TailQuestionEntry = Field(..., alias="tail_question", serialization_alias="tailQuestion")


class ExportReviewRequest(BaseModel):
    """비교 세션 ➔ 검토 센터 티켓 내보내기 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId", description="관련 개념 ID")
    title: str = Field(..., description="검토 티켓 제목")
    overrideReason: str = Field(..., alias="override_reason", serialization_alias="overrideReason", description="🌟 도메인 필수 사유 (공인 백서/실측 근거 강제, 금지어 '전문가 사유' 배제)")
    author: str = Field("엔지니어", description="티켓 작성자")
    reviewType: str = Field("파라미터 수정", alias="review_type", serialization_alias="reviewType")


class ExportReviewResponse(BaseModel):
    """검토 센터 티켓 내보내기 완료 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    sessionId: str = Field(..., alias="session_id", serialization_alias="sessionId")
    ticketId: str = Field(..., alias="ticket_id", serialization_alias="ticketId")
    message: str


class TuneAdvisorRequest(BaseModel):
    """AI 파라미터 튜닝 상담 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    userPrompt: str = Field(..., alias="user_prompt", serialization_alias="userPrompt", description="엔지니어 장비/라인 제약 질문")
    applyCompensation: Optional[str] = Field(None, alias="applyCompensation", serialization_alias="applyCompensation", description="선택된 보상안 ('compensationA' 또는 'compensationB')")
    manualConditions: Optional[Dict[str, Any]] = Field(None, alias="manualConditions", serialization_alias="manualConditions", description="엔지니어 직접 입력 수치")


class TuneAdvisorResponse(BaseModel):
    """AI 파라미터 튜닝 상담 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    userPrompt: str = Field(..., alias="user_prompt", serialization_alias="userPrompt")
    riskDetected: str = Field(..., alias="risk_detected", serialization_alias="riskDetected")
    advisorRecommendation: Dict[str, Any] = Field(..., alias="advisor_recommendation", serialization_alias="advisorRecommendation")
    appliedResult: Optional[Dict[str, Any]] = Field(None, alias="applied_result", serialization_alias="appliedResult")


class ClarifyBranch(BaseModel):
    """대화형 질문 구체화 공학 분기 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    branchId: str = Field(..., alias="branch_id", serialization_alias="branchId")
    title: str
    description: str
    targetA: str = Field(..., alias="target_a", serialization_alias="targetA")
    targetB: str = Field(..., alias="target_b", serialization_alias="targetB")
    domain: str


# 호환용 별칭
ComparisonBranchCard = ClarifyBranch


class DynamicAxisTag(BaseModel):
    """동적 후보 축 개별 태그 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    axisId: str = Field(..., alias="axis_id", serialization_alias="axisId")
    label: str
    category: str
    isSelected: bool = Field(False, alias="is_selected", serialization_alias="isSelected")


class DynamicAxesCategory(BaseModel):
    """동적 후보 축 카테고리 그룹 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    category: str
    categoryLabel: str = Field(..., alias="category_label", serialization_alias="categoryLabel")
    tags: List[DynamicAxisTag] = Field(default_factory=list)


class ClarificationQuestion(BaseModel):
    """구체화 꼬리 질문 객체 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    questionId: str = Field(..., alias="question_id", serialization_alias="questionId")
    question: str
    options: List[str] = Field(default_factory=list)


class DynamicAxisCandidate(BaseModel):
    """동적 적응형 비교 축 후보 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    axisId: str = Field(..., alias="axis_id", serialization_alias="axisId")
    label: str
    category: str
    categoryLabel: str = Field(..., alias="category_label", serialization_alias="categoryLabel")


class ClarifyRequest(BaseModel):
    """비교 분석 전 질문 구체화 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    query: str = Field(..., min_length=2, description="엔지니어 비교 질문")
    baseConceptId: Optional[str] = Field(None, alias="base_concept_id", serialization_alias="baseConceptId")
    customAxes: Optional[List[str]] = Field(default_factory=list, alias="custom_axes", serialization_alias="customAxes")


class ClarifyResponse(BaseModel):
    """비교 분석 전 질문 구체화 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    recognizedIntent: str = Field(..., alias="recognized_intent", serialization_alias="recognizedIntent")
    branches: List[ClarifyBranch]
    dynamicAxesPool: Any = Field(..., alias="dynamic_axes_pool", serialization_alias="dynamicAxesPool")
    clarificationQuestions: Any = Field(..., alias="clarification_questions", serialization_alias="clarificationQuestions")


# 호환용 별칭
ComparisonClarifyResponse = ClarifyResponse


class ComparisonMatrixRow(BaseModel):
    """다차원 기술 대안 비교 매트릭스 단일 행 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    axis: str
    axisCategory: str = Field(..., alias="axis_category", serialization_alias="axisCategory")
    categoryLabel: str = Field(..., alias="category_label", serialization_alias="categoryLabel")
    valA: str = Field(..., alias="val_a", serialization_alias="valA")
    valB: str = Field(..., alias="val_b", serialization_alias="valB")
    evidenceA: Optional[str] = Field(None, alias="evidence_a", serialization_alias="evidenceA")
    evidenceB: Optional[str] = Field(None, alias="evidence_b", serialization_alias="evidenceB")
    isGap: bool = Field(False, alias="is_gap", serialization_alias="isGap")


class CausalChainStep(BaseModel):
    """인과 사슬 단일 홉 단계 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    hop: int
    sourceNode: str = Field(..., alias="source_node", serialization_alias="sourceNode")
    targetNode: str = Field(..., alias="target_node", serialization_alias="targetNode")
    relationType: str = Field(..., alias="relation_type", serialization_alias="relationType")
    mechanism: str


class TailQuestionResponse(BaseModel):
    """심층 꼬리질문 인과 해설 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    query: str
    stepIndex: int = Field(2, alias="step_index", serialization_alias="stepIndex")
    causalPath: List[str] = Field(default_factory=list, alias="causal_path", serialization_alias="causalPath")
    chainSteps: List[CausalChainStep] = Field(default_factory=list, alias="chain_steps", serialization_alias="chainSteps")
    engineeringExplanation: str = Field(..., alias="engineering_explanation", serialization_alias="engineeringExplanation")
    evidenceReferences: List[str] = Field(default_factory=list, alias="evidence_references", serialization_alias="evidenceReferences")
    compensatingProposal: Optional[str] = Field(None, alias="compensating_proposal", serialization_alias="compensatingProposal")


class SessionPatchRequest(BaseModel):
    """비교 세션 핀 고정, 제목 수정, 폴더 이동 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    isPinned: Optional[bool] = Field(None, alias="is_pinned", serialization_alias="isPinned")
    title: Optional[str] = None
    folderId: Optional[str] = Field(None, alias="folder_id", serialization_alias="folderId")


class SessionPatchResponse(BaseModel):
    """비교 세션 패치 결과 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    title: str
    isPinned: bool = Field(..., alias="is_pinned", serialization_alias="isPinned")
    folderId: Optional[str] = Field(None, alias="folder_id", serialization_alias="folderId")
    updatedAt: str = Field(..., alias="updated_at", serialization_alias="updatedAt")


class MatrixRecalculateRequest(BaseModel):
    """스냅샷 3 매트릭스 필터링 및 커스텀 축 추가 요청 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    selectedCategories: Optional[List[str]] = Field(default_factory=list, alias="selected_categories", serialization_alias="selectedCategories")
    addedCustomAxis: Optional[Dict[str, str]] = Field(None, alias="added_custom_axis", serialization_alias="addedCustomAxis")


class MatrixRecalculateResponse(BaseModel):
    """스냅샷 3 매트릭스 재계산 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    sessionId: str = Field(..., alias="session_id", serialization_alias="sessionId")
    matrix: List[Dict[str, Any]]
    aiCausalNote: Optional[str] = Field(None, alias="ai_causal_note", serialization_alias="aiCausalNote")


