from fastapi import APIRouter, Depends, Request
from ...identity.dependencies import current_principal

router = APIRouter(tags=['document wiki suggestions'])


@router.get('/documents/{document_id}/wiki-suggestions')
async def notice(document_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.document_wiki.notice(principal, document_id)
