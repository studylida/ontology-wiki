from fastapi import APIRouter, Depends, Query, Request

from knowledge.identity.dependencies import current_principal

from .dto import OrganizeRequest, WikiPatch, WikiSettingsPatch, WikiUndo
from .service import PersonalWikiService


router = APIRouter(prefix="/personal-wiki", tags=["personal-wiki"])


def service(request):
    return PersonalWikiService(request.app.state.session_factory, request.app.state.settings)


@router.get("")
async def list_pages(request: Request, q: str | None = Query(None, max_length=300),
                     principal=Depends(current_principal)):
    return await service(request).list(principal, q)


@router.get("/settings")
async def settings(request: Request, principal=Depends(current_principal)):
    return await service(request).settings(principal)


@router.patch("/settings")
async def patch_settings(body: WikiSettingsPatch, request: Request, principal=Depends(current_principal)):
    return await service(request).patch_settings(principal, body)


@router.post("/organize", status_code=202)
async def organize(body: OrganizeRequest, request: Request, principal=Depends(current_principal)):
    return await service(request).organize(principal, body)


@router.get("/{page_id}")
async def get_page(page_id: str, request: Request, principal=Depends(current_principal)):
    return await service(request).get(principal, page_id)


@router.patch("/{page_id}")
async def patch_page(page_id: str, body: WikiPatch, request: Request, principal=Depends(current_principal)):
    return await service(request).patch(principal, page_id, body)


@router.delete("/{page_id}")
async def delete_page(page_id: str, request: Request, principal=Depends(current_principal)):
    return await service(request).delete(principal, page_id)


@router.post("/{page_id}/undo")
async def undo_page(page_id: str, body: WikiUndo, request: Request, principal=Depends(current_principal)):
    return await service(request).undo(principal, page_id, body)
