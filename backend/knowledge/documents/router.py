from fastapi import APIRouter, Depends, Request

from knowledge.identity.dependencies import current_principal
from knowledge.documents.dto import AttachRequest, MetadataPatch, NewDocument, NewRevision, ReviewRequest
from knowledge.documents.service import DocumentService

router = APIRouter(tags=["documents"])


def service(request: Request):
    return DocumentService(request.app.state.session_factory, request.app.state.settings)


@router.get("/documents")
async def list_documents(request: Request, reviewStatus: str | None = None, principal=Depends(current_principal)):
    return await service(request).list(principal, reviewStatus)


@router.post("/documents", status_code=201)
async def create_document(body: NewDocument, request: Request, principal=Depends(current_principal)):
    return await service(request).create(principal, body)


@router.post("/documents/{document_id}/revisions", status_code=201)
async def create_revision(document_id: str, body: NewRevision, request: Request, principal=Depends(current_principal)):
    return await service(request).add_revision(principal, document_id, body)


@router.get("/documents/revisions/{revision_id}")
async def revision(revision_id: str, request: Request, principal=Depends(current_principal)):
    return await service(request).detail(principal, revision_id)


@router.post("/documents/revisions/{revision_id}/review")
async def review(revision_id: str, body: ReviewRequest, request: Request, principal=Depends(current_principal)):
    return await service(request).review(principal, revision_id, body)


@router.patch("/documents/revisions/{revision_id}/metadata")
async def metadata(revision_id: str, body: MetadataPatch, request: Request, principal=Depends(current_principal)):
    return await service(request).patch_metadata(principal, revision_id, body)


@router.post("/documents/revisions/{revision_id}/attach")
async def attach(revision_id: str, body: AttachRequest, request: Request, principal=Depends(current_principal)):
    return {"attachmentId": await service(request).attach(principal, revision_id, body.conversation_id)}
