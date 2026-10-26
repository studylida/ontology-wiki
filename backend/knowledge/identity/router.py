from fastapi import APIRouter, Depends, Request
from .dto import LoginRequest, Principal
from .dependencies import current_principal

router = APIRouter(prefix="/auth", tags=["identity"])


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    return await request.app.state.services.identity.login(body.username, body.password)


@router.get("/me", response_model=Principal)
async def me(principal: Principal = Depends(current_principal)):
    return principal
