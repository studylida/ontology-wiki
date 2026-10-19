"""Comparison Studio Schemas.

Covers ComparisonSession, 3-Step Snapshots, Tail-Questions (꼬리질문), and Tuning History.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TailQuestionEntry(BaseModel):
    """🌟 도메인 필수 용어: 꼬리질문 이력."""
    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., description="엔지니어가 던진 꼬리물기 질문")
    causalPath: List[str] = Field(..., alias="causal_path", description="인과 체인 경로 (예: ['가압력 누적', 'CTE 미스매치', '전단응력', '다이 휨'])")
    explanation: str = Field(..., description="물리 메커니즘 심층 해설")
    timestamp: str


class ParameterTuningEntry(BaseModel):
    """🌟 도메인 필수 용어: 보상 파라미터 (Compensating Parameters) 상담 이력."""
    model_config = ConfigDict(populate_by_name=True)

    userPrompt: str = Field(..., alias="user_prompt")
    advisorRecommendation: Dict[str, Any] = Field(..., alias="advisor_recommendation")


class ComparisonSessionDTO(BaseModel):
    """기술 대안 비교 세션 엔티티 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    userId: str = Field(..., alias="user_id")
    title: str
    isPinned: bool = Field(False, alias="is_pinned")
    folderId: Optional[str] = Field(None, alias="folder_id")
    query: str
    contextParams: Dict[str, Any] = Field(default_factory=dict, alias="context_params")
    snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    exportedReviewId: Optional[str] = Field(None, alias="exported_review_id")
    createdAt: Optional[str] = Field(None, alias="created_at")
    updatedAt: Optional[str] = Field(None, alias="updated_at")
