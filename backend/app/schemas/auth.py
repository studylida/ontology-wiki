"""Section 7.2: Authentication & RBAC Pydantic Schemas.

Covers user registration, authentication, token management, password updates,
and Tier 3 confidential access request governance with camelCase serialization.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class UserRegisterDTO(BaseModel):
    """사내 엔지니어 회원가입 입력 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    username: str = Field(..., min_length=3, max_length=32, description="로그인 아이디")
    password: str = Field(..., min_length=6, max_length=128, description="비밀번호 (최소 6자)")
    name: str = Field(..., min_length=2, max_length=64, description="엔지니어 실명")
    department: str = Field(..., min_length=2, max_length=64, description="소속 부서 (예: HBM패키징개발팀)")


class UserLoginDTO(BaseModel):
    """사내 로그인 입력 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    username: str = Field(..., description="로그인 아이디")
    password: str = Field(..., description="비밀번호")


class UserDTO(BaseModel):
    """사내 엔지니어 계정 정보 응답 DTO (password_hash 철저 은닉)."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str
    username: str
    name: str
    department: str
    role: str
    level: int
    isActive: bool = Field(..., alias="is_active", serialization_alias="isActive")
    createdAt: Optional[datetime] = Field(None, alias="created_at", serialization_alias="createdAt")


class TokenResponseDTO(BaseModel):
    """JWT 토큰 발급 및 세션 복원 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    accessToken: str = Field(..., alias="access_token", serialization_alias="accessToken")
    tokenType: str = Field("Bearer", alias="token_type", serialization_alias="tokenType")
    expiresIn: int = Field(86400, alias="expires_in", serialization_alias="expiresIn")
    user: UserDTO


class PasswordChangeDTO(BaseModel):
    """비밀번호 변경 입력 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    oldPassword: str = Field(..., alias="old_password", serialization_alias="oldPassword")
    newPassword: str = Field(..., min_length=6, max_length=128, alias="new_password", serialization_alias="newPassword")


class AccessRequestCreateDTO(BaseModel):
    """Tier 3 대외비 지식 열람 권한 신청 입력 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId", description="대상 공정 개념 ID")
    reason: str = Field(..., min_length=5, description="열람 목적 상세 사유 (최소 5자 이상)")


class AccessRequestDTO(BaseModel):
    """비인가 지식 열람 신청 티켓 응답 DTO."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str
    userId: str = Field(..., alias="user_id", serialization_alias="userId")
    userName: Optional[str] = Field(None, alias="user_name", serialization_alias="userName")
    userDepartment: Optional[str] = Field(None, alias="user_department", serialization_alias="userDepartment")
    conceptId: str = Field(..., alias="concept_id", serialization_alias="conceptId")
    conceptTitle: str = Field(..., alias="concept_title", serialization_alias="conceptTitle")
    reason: str
    status: str = Field("pending")  # pending | approved | rejected | revoked
    reviewedBy: Optional[str] = Field(None, alias="reviewed_by", serialization_alias="reviewedBy")
    reviewedAt: Optional[datetime] = Field(None, alias="reviewed_at", serialization_alias="reviewedAt")
    reviewComment: Optional[str] = Field(None, alias="review_comment", serialization_alias="reviewComment")
    createdAt: Optional[datetime] = Field(None, alias="created_at", serialization_alias="createdAt")


class AccessReviewDTO(BaseModel):
    """관리자 열람 심사(승인/반려/회수) 입력 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    comment: Optional[str] = Field(None, description="심사관 의견 또는 반려 사유")


class UserLevelUpdateDTO(BaseModel):
    """시스템 관리자 전용 권한 레벨 변경 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    level: int = Field(..., ge=1, le=4, description="권한 등급 (1: 게스트, 2: 현장 엔지니어, 3: 수석 검토관, 4: 시스템 관리자)")
