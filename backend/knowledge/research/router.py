from fastapi import APIRouter, Depends, Request

from knowledge.identity.dependencies import current_principal
from knowledge.research.dto import FetchRequest, SearchRequest, TransferRequest
from knowledge.research.service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


def service(request):
    return ResearchService(request.app.state.session_factory, request.app.state.settings, request.app.state.generation_client)


@router.post("/search")
async def search(body: SearchRequest, request: Request, principal=Depends(current_principal)):
    return await service(request).search(principal, body)


@router.post("/fetch")
async def fetch(body: FetchRequest, request: Request, principal=Depends(current_principal)):
    return await service(request).fetch(principal, body)


@router.post("/transfer")
async def transfer(body: TransferRequest, request: Request, principal=Depends(current_principal)):
    return await service(request).transfer(principal, body)
