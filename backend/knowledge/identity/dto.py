from typing import Literal
from pydantic import Field

from ..core.dto import DTO
from ..core.errors import AppError


class Principal(DTO):
    id: str
    username: str
    role: str
    kind: Literal["user", "service"] = "user"
    permissions: set[str] = Field(default_factory=set)

    def can(self, permission: str) -> bool:
        return permission in self.permissions

    def require(self, permission: str):
        if not self.can(permission):
            raise AppError(403, "PERMISSION_DENIED", "이 작업에 필요한 권한이 없습니다.")


class LoginRequest(DTO):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)
