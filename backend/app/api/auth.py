"""Section 7.5: Authentication & RBAC API Router.

16 Master Endpoints:
- Public: Register, Login
- Authenticated Engineer: Refresh, Me, Change Password, Deactivate Self, Create Access Request, My Requests, Cancel Request
- Level >= 3 (Chief Reviewer): List Access Requests Queue, Approve Request, Reject Request, Revoke Approval
- Level >= 4 (Admin): List All Users, Update User Level, Deactivate User
"""
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.entities import UserModel, AccessRequestModel
from backend.app.core.security import (
    get_current_active_user,
    require_min_level
)
from backend.app.services.auth_service import (
    AuthService,
    AccessControlService,
    UserAdminService
)
from backend.app.schemas.auth import (
    UserRegisterDTO,
    UserLoginDTO,
    UserDTO,
    TokenResponseDTO,
    PasswordChangeDTO,
    AccessRequestCreateDTO,
    AccessRequestDTO,
    AccessReviewDTO,
    UserLevelUpdateDTO
)

logger = logging.getLogger("auth_api")

router = APIRouter(prefix="/auth", tags=["Auth & RBAC"])


def _to_request_dto(req: AccessRequestModel) -> AccessRequestDTO:
    """AccessRequestModel ➔ AccessRequestDTO 변환 (user 관계 필드 안전 매핑)."""
    return AccessRequestDTO(
        id=req.id,
        user_id=req.user_id,
        user_name=req.user.name if req.user else None,
        user_department=req.user.department if req.user else None,
        concept_id=req.concept_id,
        concept_title=req.concept_title,
        reason=req.reason,
        status=req.status,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        review_comment=req.review_comment,
        created_at=req.created_at
    )


# ---------------------------------------------------------------------------
# 1. 공개 인증 엔드포인트 (Public)
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="사내 엔지니어 자체 회원가입 API",
    description="사내 엔지니어 계정을 생성하고 24시간 유효 JWT 토큰을 발급합니다 (기본 Level 2 현장 엔지니어 부여)."
)
async def register_user(
    body: UserRegisterDTO,
    db: AsyncSession = Depends(get_db)
):
    user, token = await AuthService.register(db, body)
    return TokenResponseDTO(
        access_token=token,
        token_type="Bearer",
        expires_in=86400,
        user=UserDTO.model_validate(user)
    )


@router.post(
    "/login",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="사내 로그인 API",
    description="사내 계정 자격증명을 검증하고 24시간 유효 JWT 토큰 및 사용자 프로필을 반환합니다."
)
async def login_user(
    body: UserLoginDTO,
    db: AsyncSession = Depends(get_db)
):
    user, token = await AuthService.authenticate(db, body)
    return TokenResponseDTO(
        access_token=token,
        token_type="Bearer",
        expires_in=86400,
        user=UserDTO.model_validate(user)
    )


# ---------------------------------------------------------------------------
# 2. 인증된 엔지니어 전용 엔드포인트 (Authenticated Engineer)
# ---------------------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="JWT 토큰 무중단 갱신 API",
    description="만료 직전의 활성 토큰을 소지한 사용자의 토큰을 무중단 갱신합니다."
)
async def refresh_access_token(
    current_user: UserModel = Depends(get_current_active_user)
):
    new_token = await AuthService.refresh_token(current_user)
    return TokenResponseDTO(
        access_token=new_token,
        token_type="Bearer",
        expires_in=86400,
        user=UserDTO.model_validate(current_user)
    )


@router.get(
    "/me",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    summary="내 프로필 및 권한 등급 조회 API",
    description="현재 로그인된 엔지니어의 프로필과 권한 레벨(Level 1~4)을 반환합니다 (SPA 새로고침 시 세션 복원)."
)
async def get_my_profile(
    current_user: UserModel = Depends(get_current_active_user)
):
    return UserDTO.model_validate(current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="비밀번호 변경 API",
    description="기존 비밀번호를 확인한 후 새로운 비밀번호로 솔팅 해시를 갱신합니다."
)
async def change_password(
    body: PasswordChangeDTO,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.change_password(db, current_user, body)
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="본인 회원 탈퇴 (Soft Delete) API",
    description="WORM 감사 무결성 보존을 위해 계정을 물리 삭제하지 않고 비활성화(is_active = False)합니다."
)
async def deactivate_my_account(
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.deactivate_self(db, current_user)
    return {"message": "회원 탈퇴 및 계정 비활성화가 완료되었습니다."}


# ---------------------------------------------------------------------------
# 3. 비인가 지식(Tier 3 L3) 열람 권한 신청 엔드포인트
# ---------------------------------------------------------------------------

@router.post(
    "/access-requests",
    response_model=AccessRequestDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Tier 3 대외비 지식 열람 권한 신청 API",
    description="특정 공정 개념의 마스킹된 L3 절대 수치 열람 권한을 신청합니다 (대기 pending 티켓 생성)."
)
async def create_access_request(
    body: AccessRequestCreateDTO,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    req = await AccessControlService.create_access_request(db, current_user, body)
    return _to_request_dto(req)


@router.get(
    "/access-requests/my",
    response_model=List[AccessRequestDTO],
    status_code=status.HTTP_200_OK,
    summary="내가 신청한 열람 권한 내역 조회 API",
    description="현재 로그인된 엔지니어가 신청한 L3 열람 티켓 목록과 승인/반려 상태를 반환합니다."
)
async def get_my_access_requests(
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from backend.app.repositories.auth_repo import AccessRequestRepository
    requests = await AccessRequestRepository.list_by_user(db, current_user.id)
    return [_to_request_dto(r) for r in requests]


@router.delete(
    "/access-requests/{request_id}",
    status_code=status.HTTP_200_OK,
    summary="대기 중인 본인 열람 신청 자진 취소 API",
    description="아직 심사되지 않은 대기(pending) 상태의 본인 신청 티켓을 자진 취소(삭제)합니다."
)
async def cancel_my_access_request(
    request_id: str = Path(..., description="열람 신청 티켓 ID"),
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await AccessControlService.cancel_access_request(db, current_user, request_id)
    return {"message": f"열람 신청 티켓 '{request_id}'이(가) 취소되었습니다."}


# ---------------------------------------------------------------------------
# 4. 수석 검토관(Level >= 3) 전용 거버넌스 심사 엔드포인트
# ---------------------------------------------------------------------------

@router.get(
    "/access-requests",
    response_model=List[AccessRequestDTO],
    status_code=status.HTTP_200_OK,
    summary="관리자 열람 신청 심사 큐 조회 API",
    description="수석 검토관(Level >= 3) 전용: 미결(pending) 또는 전체 열람 신청 큐를 페이징 조회합니다."
)
async def list_access_requests_for_admin(
    status: Optional[str] = Query(None, description="상태 필터 (pending | approved | rejected | revoked)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_min_level(3)),
    db: AsyncSession = Depends(get_db)
):
    from backend.app.repositories.auth_repo import AccessRequestRepository
    requests = await AccessRequestRepository.list_for_admin(db, status=status, limit=limit, offset=offset)
    return [_to_request_dto(r) for r in requests]


@router.post(
    "/access-requests/{request_id}/approve",
    response_model=AccessRequestDTO,
    status_code=status.HTTP_200_OK,
    summary="L3 열람 권한 승인 API",
    description="수석 검토관(Level >= 3) 전용: 신청을 승인하고 해당 엔지니어에게 대상 공정의 L3 마스킹을 즉시 해제합니다."
)
async def approve_access_request(
    request_id: str = Path(..., description="열람 신청 티켓 ID"),
    body: Optional[AccessReviewDTO] = None,
    current_user: UserModel = Depends(require_min_level(3)),
    db: AsyncSession = Depends(get_db)
):
    comment = body.comment if body else None
    req = await AccessControlService.approve_request(db, current_user, request_id, comment)
    return _to_request_dto(req)


@router.post(
    "/access-requests/{request_id}/reject",
    response_model=AccessRequestDTO,
    status_code=status.HTTP_200_OK,
    summary="L3 열람 권한 반려 API",
    description="수석 검토관(Level >= 3) 전용: 신청을 반려 처리합니다 (반려 사유 comment 필수)."
)
async def reject_access_request(
    request_id: str = Path(..., description="열람 신청 티켓 ID"),
    body: AccessReviewDTO = ...,
    current_user: UserModel = Depends(require_min_level(3)),
    db: AsyncSession = Depends(get_db)
):
    req = await AccessControlService.reject_request(db, current_user, request_id, body.comment)
    return _to_request_dto(req)


@router.post(
    "/access-requests/{request_id}/revoke",
    response_model=AccessRequestDTO,
    status_code=status.HTTP_200_OK,
    summary="기승인된 L3 열람 권한 강제 회수 API",
    description="수석 검토관(Level >= 3) 전용: 이전에 승인된 권한을 회수하여 L3 마스킹을 재적용합니다."
)
async def revoke_access_request(
    request_id: str = Path(..., description="열람 신청 티켓 ID"),
    body: Optional[AccessReviewDTO] = None,
    current_user: UserModel = Depends(require_min_level(3)),
    db: AsyncSession = Depends(get_db)
):
    comment = body.comment if body else None
    req = await AccessControlService.revoke_approval(db, current_user, request_id, comment)
    return _to_request_dto(req)


# ---------------------------------------------------------------------------
# 5. 시스템 관리자(Level >= 4) 전용 계정 관리 엔드포인트
# ---------------------------------------------------------------------------

@router.get(
    "/users",
    response_model=List[UserDTO],
    status_code=status.HTTP_200_OK,
    summary="사내 전체 엔지니어 계정 목록 조회 API",
    description="시스템 관리자(Level >= 4) 전용: 사내 전체 계정 현황 및 권한 레벨을 조회합니다."
)
async def list_all_users(
    role: Optional[str] = Query(None, description="역할 필터"),
    level: Optional[int] = Query(None, ge=1, le=4, description="권한 레벨 필터"),
    search: Optional[str] = Query(None, description="검색어 (아이디, 성명, 부서)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    users = await UserAdminService.list_users(db, role=role, level=level, search=search, limit=limit, offset=offset)
    return [UserDTO.model_validate(u) for u in users]


@router.patch(
    "/users/{user_id}/level",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    summary="엔지니어 권한 레벨 승격/강등 API",
    description="시스템 관리자(Level >= 4) 전용: 특정 엔지니어의 권한 등급을 조정합니다 (자기 자신 강등 방어)."
)
async def update_user_level(
    user_id: str = Path(..., description="대상 사용자 사번/ID"),
    body: UserLevelUpdateDTO = ...,
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    updated = await UserAdminService.update_user_level(db, current_user, user_id, body.level)
    return UserDTO.model_validate(updated)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="퇴사자/비인가자 계정 강제 비활성화 API",
    description="시스템 관리자(Level >= 4) 전용: 계정을 강제 비활성화(Soft Delete)합니다 (자기 자신 탈퇴 방어)."
)
async def deactivate_user_by_admin(
    user_id: str = Path(..., description="대상 사용자 사번/ID"),
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    await UserAdminService.deactivate_user(db, current_user, user_id)
    return {"message": f"사용자 '{user_id}' 계정이 성공적으로 비활성화되었습니다."}
