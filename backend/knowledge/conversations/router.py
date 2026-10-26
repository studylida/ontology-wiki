from fastapi import APIRouter, Depends, Request
from .dto import ConversationCreate, ConversationPatch
from ..identity.dependencies import current_principal
from ..identity.dto import Principal

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.conversations.list(principal)


@router.post("", status_code=201)
async def create(body: ConversationCreate, request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.conversations.create(principal, body.title)


@router.get("/{conversation_id}")
async def get(conversation_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.conversations.get(principal, conversation_id)


@router.patch("/{conversation_id}")
async def patch(conversation_id: str, body: ConversationPatch, request: Request,
                principal: Principal = Depends(current_principal)):
    return await request.app.state.services.conversations.patch(principal, conversation_id, body)
