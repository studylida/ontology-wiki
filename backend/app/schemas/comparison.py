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
