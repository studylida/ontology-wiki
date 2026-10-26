import asyncio
from .dto import Principal
from .entities import ROLE_PERMISSIONS
from .repository import UserRepository
from .security import create_token, decode_token, verify_password
from ..core.errors import AppError


def principal_from_user(user) -> Principal:
    # Service accounts use explicitly granted scopes, never a person's role expansion.
    permissions = set(user.permissions or [])
    if user.kind == "user":
        permissions |= ROLE_PERMISSIONS.get(user.role, set())
    return Principal(id=user.id, username=user.username, role=user.role, kind=user.kind,
                     permissions=permissions)


class IdentityService:
    def __init__(self, session_factory, settings):
        self.session_factory, self.settings = session_factory, settings

    async def login(self, username, password):
        async with self.session_factory() as session:
            user = await UserRepository(session).by_username(username.strip())
        if user is None or not await asyncio.to_thread(verify_password, password, user.password_hash):
            raise AppError(401, "INVALID_CREDENTIALS", "아이디 또는 비밀번호가 일치하지 않습니다.")
        if not user.is_active:
            raise AppError(403, "USER_INACTIVE", "비활성화된 계정입니다.")
        return {"accessToken": create_token(user, self.settings), "user": principal_from_user(user).public()}

    async def authenticate(self, token):
        payload = decode_token(token, self.settings)
        async with self.session_factory() as session:
            user = await UserRepository(session).get(payload["sub"])
        if user is None or not user.is_active or user.token_version != payload["ver"]:
            raise AppError(401, "IDENTITY_REVOKED", "현재 유효한 계정 또는 토큰이 아닙니다.")
        return principal_from_user(user)

    async def refresh_principal(self, principal):
        async with self.session_factory() as session:
            user = await UserRepository(session).get(principal.id)
        if user is None or not user.is_active:
            raise AppError(403, "IDENTITY_REVOKED", "현재 계정 권한이 철회되었습니다.")
        return principal_from_user(user)
