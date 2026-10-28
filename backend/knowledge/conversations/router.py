from fastapi import APIRouter, Depends, Request

from ..identity.dependencies import current_principal
from .dto import (ConversationCreate, ConversationDetail, ConversationList,
                  ConversationPatch, ConversationView, MessageCreate, MessageView)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationList)
async def list_conversations(request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.conversations.list(principal)


@router.post("", status_code=201, response_model=ConversationView)
async def create(body: ConversationCreate, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.conversations.create(principal, body)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get(conversation_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.conversations.get(principal, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationView)
async def patch(conversation_id: str, body: ConversationPatch, request: Request,
                principal=Depends(current_principal)):
    return await request.app.state.services.conversations.patch(principal, conversation_id, body)


@router.post("/{conversation_id}/messages", status_code=201, response_model=MessageView)
async def add_message(conversation_id: str, body: MessageCreate, request: Request,
                      principal=Depends(current_principal)):
    """Persist a user message only; generation is implemented in Stage 3."""
    return await request.app.state.services.conversations.add_message(principal, conversation_id, body)
