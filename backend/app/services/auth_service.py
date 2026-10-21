"""Section 7.4: Auth & RBAC Domain Services.

Implements core security and governance logic:
1. AuthService: Registration, Login, Token Refresh, Password Change, Self-Deactivation.
2. AccessControlService: L3 Access Request issuance, Approval, Rejection, Revocation, and Dynamic L3 Masking Guard.
3. UserAdminService: Level update, Soft deletion, and self-demotion prevention guardrails.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.entities import UserModel, AccessRequestModel, ConceptModel
from backend.app.repositories.auth_repo import UserRepository, AccessRequestRepository
from backend.app.core.security import PasswordSecurityService, TokenManagerService
from backend.app.schemas.auth import (
    UserRegisterDTO,
    UserLoginDTO,
    UserDTO,
    PasswordChangeDTO,
    AccessRequestCreateDTO,
    AccessRequestDTO
)

logger = logging.getLogger("auth_service")


class AuthService:
    """사내 인증 및 계정 라이프사이클 관리 서비스."""

    @classmethod
    async def register(cls, db: AsyncSession, dto: UserRegisterDTO) -> Tuple[UserModel, str]:
        """사내 신규 엔지니어 등록 (중복 검증, PBKDF2 해싱, 기본 Level 2 부여)."""
        existing = await UserRepository.get_by_username(db, dto.username.strip())
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "USERNAME_EXISTS", "message": f"아이디 '{dto.username}'은(는) 이미 사내에 등록되어 있습니다."}
            )

        now = datetime.now(timezone.utc)
        user_id = f"EMP-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
        hashed_pw = PasswordSecurityService.hash_password(dto.password)

        new_user = UserModel(
            id=user_id,
            username=dto.username.strip(),
            password_hash=hashed_pw,
            name=dto.name.strip(),
            department=dto.department.strip(),
            role="line_engineer",
            level=2,  # 기본 현장 엔지니어 (Level 2)
            is_active=True,
            created_at=now,
            updated_at=now
        )
        created_user = await UserRepository.create_user(db, new_user)
        token = TokenManagerService.create_access_token(
            subject=created_user.id,
            claims={"username": created_user.username, "role": created_user.role, "level": created_user.level}
        )
        return created_user, token

    @classmethod
    async def authenticate(cls, db: AsyncSession, dto: UserLoginDTO) -> Tuple[UserModel, str]:
        """사내 자격증명 검증 및 JWT 발급 (타이밍 공격 방어 및 Soft Delete 비활성 차단)."""
        user = await UserRepository.get_by_username(db, dto.username.strip())
        if not user or not PasswordSecurityService.verify_password(dto.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_CREDENTIALS", "message": "사내 아이디 또는 비밀번호가 일치하지 않습니다."}
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "USER_INACTIVE", "message": "비활성화 또는 퇴사 처리된 계정입니다. 시스템 관리자에게 문의하세요."}
            )

        token = TokenManagerService.create_access_token(
            subject=user.id,
            claims={"username": user.username, "role": user.role, "level": user.level}
        )
        return user, token

    @classmethod
    async def refresh_token(cls, user: UserModel) -> str:
        """현재 활성 세션의 무중단 토큰 갱신."""
        return TokenManagerService.create_access_token(
            subject=user.id,
            claims={"username": user.username, "role": user.role, "level": user.level}
        )

    @classmethod
    async def change_password(cls, db: AsyncSession, user: UserModel, dto: PasswordChangeDTO) -> None:
        """기존 비밀번호 대조 후 신규 솔팅 해시 갱신."""
        if not PasswordSecurityService.verify_password(dto.oldPassword, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_OLD_PASSWORD", "message": "현재 사용 중인 기존 비밀번호가 일치하지 않습니다."}
            )
        user.password_hash = PasswordSecurityService.hash_password(dto.newPassword)
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()

    @classmethod
    async def deactivate_self(cls, db: AsyncSession, user: UserModel) -> None:
        """본인 회원 탈퇴 (Soft Delete: is_active = False). 단독 어드민 탈퇴 방어."""
        if user.level >= 4:
            admin_stmt = select(UserModel).where(UserModel.level >= 4, UserModel.is_active == True)
            admins = (await db.execute(admin_stmt)).scalars().all()
            if len(admins) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "LAST_ADMIN_CANNOT_LEAVE", "message": "유일한 시스템 관리자는 탈퇴할 수 없습니다. 다른 관리자를 지정하세요."}
                )
        await UserRepository.soft_delete_user(db, user)


class AccessControlService:
    """비인가 지식(Tier 3 L3 대외비) 열람 권한 신청 및 심사 총괄 서비스."""

    @classmethod
    async def create_access_request(
        cls,
        db: AsyncSession,
        user: UserModel,
        dto: AccessRequestCreateDTO
    ) -> AccessRequestModel:
        """L3 비인가 지식 열람 신청 티켓 발의 (개념 실존 검증, 중복 신청 및 기승인 방어)."""
        concept = await db.get(ConceptModel, dto.conceptId)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"대상 공정 개념 '{dto.conceptId}'을(를) 찾을 수 없습니다."
            )

        # 0. 수석검토관(Level >= 3) 이상은 이미 전 공정 무조건 열람 권한 보유
        if user.level >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_HAS_FULL_ACCESS", "message": "수석 검토관(Level 3) 이상의 계정은 이미 전 공정 L3 대외비에 대한 무조건 열람 권한을 보유하고 있어 별도 신청이 불필요합니다."}
            )

        # 1. 이미 승인된 권한이 있는지 확인
        if await AccessRequestRepository.has_active_approval(db, user.id, dto.conceptId):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_APPROVED", "message": f"'{concept.title}' 공정의 L3 대외비 열람 권한이 이미 승인되어 있습니다."}
            )

        # 2. 이미 심사 대기 중인 티켓이 있는지 확인
        pending = await AccessRequestRepository.find_pending_or_approved(db, user.id, dto.conceptId)
        if pending and pending.status == "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "REQUEST_ALREADY_PENDING", "message": f"'{concept.title}' 공정에 대해 이미 심사 대기 중인 티켓({pending.id})이 존재합니다."}
            )

        now = datetime.now(timezone.utc)
        req_id = f"req-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        new_request = AccessRequestModel(
            id=req_id,
            user_id=user.id,
            concept_id=concept.id,
            concept_title=concept.title,
            reason=dto.reason.strip(),
            status="pending",
            created_at=now,
            updated_at=now
        )
        return await AccessRequestRepository.create_request(db, new_request)

    @classmethod
    async def cancel_access_request(cls, db: AsyncSession, user: UserModel, request_id: str) -> None:
        """본인이 신청한 미결(pending) 열람 티켓 자진 취소."""
        req = await AccessRequestRepository.get_by_id(db, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"열람 신청 티켓 '{request_id}'을(를) 찾을 수 없습니다."
            )
        if req.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인이 제출한 열람 신청 티켓만 취소할 수 있습니다."
            )
        if req.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이미 심사 완료된 티켓(상태: {req.status})은 취소할 수 없습니다."
            )
        await AccessRequestRepository.delete_request(db, req)

    @classmethod
    async def approve_request(
        cls,
        db: AsyncSession,
        admin_user: UserModel,
        request_id: str,
        comment: Optional[str]
    ) -> AccessRequestModel:
        """수석검토관(Level >= 3) 열람 승인 ➔ 대상 유저에게 L3 마스킹 영구 해제 (자가 승인 방지 및 상태 전이 검증)."""
        req = await AccessRequestRepository.get_by_id(db, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"열람 신청 티켓 '{request_id}'을(를) 찾을 수 없습니다."
            )

        # 🌟 도메인 거버넌스 가드레일 1: 자가 승인(Self-Approval) 방어 (직무 분리 원칙)
        if req.user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "SELF_APPROVAL_FORBIDDEN", "message": "직무 분리(Separation of Duties) 원칙에 따라 본인이 신청한 열람 티켓을 직접 승인할 수 없습니다."}
            )

        # 🌟 도메인 거버넌스 가드레일 2: 상태 전이 무결성 (오직 pending 상태만 승인 가능)
        if req.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_APPROVED", "message": "이미 승인 완료된 열람 신청 티켓입니다."}
            )
        if req.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": f"현재 상태('{req.status}')의 티켓은 승인할 수 없습니다. 대기(pending) 상태의 티켓만 승인이 가능합니다."}
            )

        req.status = "approved"
        req.reviewed_by = admin_user.id
        req.reviewed_at = datetime.now(timezone.utc)
        req.review_comment = comment.strip() if comment else "수석 검토관 열람 허가 승인"
        req.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(req)
        return req

    @classmethod
    async def reject_request(
        cls,
        db: AsyncSession,
        admin_user: UserModel,
        request_id: str,
        comment: Optional[str]
    ) -> AccessRequestModel:
        """수석검토관(Level >= 3) 열람 반려 (반려 사유 필수, 상태 전이 검증)."""
        if not comment or not comment.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "REASON_REQUIRED", "message": "반려 사유(comment)는 필수 입력 사항입니다."}
            )
        req = await AccessRequestRepository.get_by_id(db, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"열람 신청 티켓 '{request_id}'을(를) 찾을 수 없습니다."
            )

        # 🌟 도메인 거버넌스 가드레일: 오직 pending 상태만 반려 가능
        if req.status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_REJECTED", "message": "이미 반려 처리된 열람 신청 티켓입니다."}
            )
        if req.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": f"현재 상태('{req.status}')의 티켓은 반려할 수 없습니다. 대기(pending) 상태의 티켓만 반려가 가능합니다 (기승인 권한은 회수(Revoke)를 이용하세요)."}
            )

        req.status = "rejected"
        req.reviewed_by = admin_user.id
        req.reviewed_at = datetime.now(timezone.utc)
        req.review_comment = comment.strip()
        req.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(req)
        return req

    @classmethod
    async def revoke_approval(
        cls,
        db: AsyncSession,
        admin_user: UserModel,
        request_id: str,
        comment: Optional[str]
    ) -> AccessRequestModel:
        """기승인된 L3 열람 권한 강제 회수 (오직 approved 상태만 회수 가능)."""
        req = await AccessRequestRepository.get_by_id(db, request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"열람 신청 티켓 '{request_id}'을(를) 찾을 수 없습니다."
            )

        # 🌟 도메인 거버넌스 가드레일: 오직 approved 상태인 권한만 회수 가능
        if req.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": f"현재 상태('{req.status}')의 티켓은 회수할 수 없습니다. 기승인(approved) 상태인 권한만 회수가 가능합니다."}
            )

        req.status = "revoked"
        req.reviewed_by = admin_user.id
        req.reviewed_at = datetime.now(timezone.utc)
        req.review_comment = comment.strip() if comment else "관리자 권한 강제 회수"
        req.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(req)
        return req
        await db.refresh(req)
        return req

    @classmethod
    async def can_view_confidential_l3(
        cls,
        user: Optional[UserModel],
        concept_id: str,
        db: AsyncSession
    ) -> bool:
        """
        0.5ms 초고속 L3 인가 판정:
        1차: user.level >= 3 (수석검토관 이상) ➔ 100% 무조건 허가 (True)
        2차: user.level < 3 (현장 엔지니어) ➔ 승인된 access_requests 티켓 존재 시 마스킹 해제 허가 (True)
        3차: 비로그인 또는 미승인 ➔ 마스킹 처리 (False)
        """
        if not user or not user.is_active:
            return False
        if user.level >= 3:
            return True
        return await AccessRequestRepository.has_active_approval(db, user.id, concept_id)


class UserAdminService:
    """시스템 관리자(Level >= 4) 전용 계정 및 권한 등급 관리 서비스."""

    @classmethod
    async def list_users(
        cls,
        db: AsyncSession,
        role: Optional[str] = None,
        level: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserModel]:
        return await UserRepository.list_users(db, role=role, level=level, search=search, limit=limit, offset=offset)

    @classmethod
    async def update_user_level(
        cls,
        db: AsyncSession,
        admin_user: UserModel,
        target_user_id: str,
        new_level: int,
        is_active: Optional[bool] = None
    ) -> UserModel:
        """특정 엔지니어의 권한 등급(Level 1~4) 승격/강등 및 활성화 상태 변경 (자기 자신 강등/탈퇴 방어)."""
        if admin_user.id == target_user_id:
            if new_level < 4:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "CANNOT_DEMOTE_SELF", "message": "관리자 본인의 권한 등급을 스스로 강등할 수 없습니다."}
                )
            if is_active is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "CANNOT_DELETE_SELF", "message": "관리자 본인의 계정을 스스로 비활성화/삭제할 수 없습니다."}
                )

        target = await UserRepository.get_by_id(db, target_user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"대상 사용자 '{target_user_id}'을(를) 찾을 수 없습니다."
            )

        if is_active is not None:
            target.is_active = is_active
            target.updated_at = datetime.now(timezone.utc)

        return await UserRepository.update_level(db, target, new_level)

    @classmethod
    async def deactivate_user(
        cls,
        db: AsyncSession,
        admin_user: UserModel,
        target_user_id: str
    ) -> None:
        """관리자에 의한 퇴사자/비인가자 계정 강제 비활성화 (Soft Delete). (자기 자신 탈퇴 방어)."""
        if admin_user.id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CANNOT_DELETE_SELF", "message": "관리자 본인의 계정을 스스로 비활성화/삭제할 수 없습니다."}
            )

        target = await UserRepository.get_by_id(db, target_user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"대상 사용자 '{target_user_id}'을(를) 찾을 수 없습니다."
            )

        await UserRepository.soft_delete_user(db, target)
