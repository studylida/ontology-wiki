from fastapi import APIRouter, Request, Depends
from .dto import RetrievalRequest
from ..identity.dependencies import current_principal
from ..identity.dto import Principal

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search")
async def search(body: RetrievalRequest, request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.rag.search(principal, body)
