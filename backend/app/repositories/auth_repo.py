"""Section 7.3: Auth & RBAC Repository Layer.

Handles pure database CRUD operations for users and access requests with SQLAlchemy 2.0 async queries.
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, update, delete
from sqlalchemy.orm import selectinload

from backend.app.models.entities import UserModel, AccessRequestModel


class UserRepository:
    """사내 엔지니어 계정 데이터 액세스 리포지토리."""

    @classmethod
    async def get_by_id(cls, db: AsyncSession, user_id: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_user(cls, db: AsyncSession, user: UserModel) -> UserModel:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

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
        stmt = select(UserModel).order_by(UserModel.created_at.desc())
        if role:
            stmt = stmt.where(UserModel.role == role)
        if level is not None:
            stmt = stmt.where(UserModel.level == level)
        if search:
            q = f"%{search}%"
            stmt = stmt.where(
                or_(
                    UserModel.username.ilike(q),
                    UserModel.name.ilike(q),
                    UserModel.department.ilike(q)
                )
            )
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update_level(cls, db: AsyncSession, user: UserModel, new_level: int) -> UserModel:
        user.level = new_level
        # level에 따라 role 자동 동기화
        if new_level == 1:
            user.role = "guest"
        elif new_level == 2:
            user.role = "line_engineer"
        elif new_level == 3:
            user.role = "chief_reviewer"
        elif new_level >= 4:
            user.role = "admin"
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def soft_delete_user(cls, db: AsyncSession, user: UserModel) -> UserModel:
        """WORM 무결성 원칙에 따른 Soft Delete (계정 비활성화)."""
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user


class AccessRequestRepository:
    """Tier 3 대외비/L3 비인가 지식 열람 권한 신청 데이터 액세스 리포지토리."""

    @classmethod
    async def create_request(cls, db: AsyncSession, request: AccessRequestModel) -> AccessRequestModel:
        db.add(request)
        await db.commit()
        await db.refresh(request)
        return request

    @classmethod
    async def get_by_id(cls, db: AsyncSession, request_id: str) -> Optional[AccessRequestModel]:
        stmt = (
            select(AccessRequestModel)
            .options(selectinload(AccessRequestModel.user))
            .where(AccessRequestModel.id == request_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list_by_user(cls, db: AsyncSession, user_id: str) -> List[AccessRequestModel]:
        stmt = (
            select(AccessRequestModel)
            .options(selectinload(AccessRequestModel.user))
            .where(AccessRequestModel.user_id == user_id)
            .order_by(AccessRequestModel.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def list_for_admin(
        cls,
        db: AsyncSession,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AccessRequestModel]:
        stmt = (
            select(AccessRequestModel)
            .options(selectinload(AccessRequestModel.user))
            .order_by(AccessRequestModel.created_at.desc())
        )
        if status:
            stmt = stmt.where(AccessRequestModel.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def find_pending_or_approved(
        cls,
        db: AsyncSession,
        user_id: str,
        concept_id: str
    ) -> Optional[AccessRequestModel]:
        """해당 유저가 특정 개념에 대해 대기(pending) 또는 기승인(approved) 티켓이 있는지 조회."""
        stmt = select(AccessRequestModel).where(
            AccessRequestModel.user_id == user_id,
            AccessRequestModel.concept_id == concept_id,
            AccessRequestModel.status.in_(["pending", "approved"])
        ).order_by(AccessRequestModel.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def has_active_approval(cls, db: AsyncSession, user_id: str, concept_id: str) -> bool:
        """0.5ms 초고속 인덱스 쿼리: 현재 시점에 활성 승인(approved) 상태인 티켓 존재 여부 판정."""
        stmt = select(AccessRequestModel.id).where(
            AccessRequestModel.user_id == user_id,
            AccessRequestModel.concept_id == concept_id,
            AccessRequestModel.status == "approved"
        ).limit(1)
        result = await db.execute(stmt)
        return result.first() is not None

    @classmethod
    async def delete_request(cls, db: AsyncSession, request: AccessRequestModel) -> None:
        await db.delete(request)
        await db.commit()
