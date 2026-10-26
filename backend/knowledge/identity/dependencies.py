from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.errors import AppError
from .dto import Principal

bearer = HTTPBearer(auto_error=False)


async def current_principal(request: Request,
                            credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
    if credentials is None:
        raise AppError(401, "MISSING_TOKEN", "로그인이 필요합니다.")
    return await request.app.state.services.identity.authenticate(credentials.credentials)
