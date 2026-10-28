from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from pydantic import ValidationError
from ..core.errors import AppError
from ..identity.dependencies import current_principal
from ..identity.dto import Principal
from .dto import SourceMetadata, UploadInfo
from .service import MAX_UPLOAD_BYTES

router = APIRouter(prefix='/documents',tags=['shared_documents'])


async def receive_upload(request, principal, file, title, metadata, document_id=None):
    try:
        body = await file.read(MAX_UPLOAD_BYTES + 1)
        if not body or len(body) > MAX_UPLOAD_BYTES:
            raise AppError(413,'source_too_large','0바이트가 아닌 20MB 이하 파일을 업로드해 주세요.')
        try:
            info = UploadInfo(title=title or file.filename or '문헌',metadata=SourceMetadata.model_validate_json(metadata))
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc
        return await request.app.state.services.documents.upload(principal,body,file.filename,info,document_id)
    finally:
        await file.close()


@router.post('',status_code=202)
async def upload(request: Request, file: UploadFile = File(...), title: str | None = Form(None),
                 metadata: str = Form('{}'), principal: Principal = Depends(current_principal)):
    return await receive_upload(request,principal,file,title,metadata)


@router.post('/{document_id}/revisions',status_code=202)
async def revise(document_id: str, request: Request, file: UploadFile = File(...), title: str | None = Form(None),
                 metadata: str = Form('{}'), principal: Principal = Depends(current_principal)):
    return await receive_upload(request,principal,file,title,metadata,document_id)


@router.get('')
async def list_documents(request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.documents.list(principal)


@router.get('/{document_id}')
async def detail(document_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.documents.detail(principal,document_id)


@router.get('/{document_id}/passages')
async def passages(document_id: str, request: Request, revision_id: str | None = Query(None,alias='revisionId'),
                   principal: Principal = Depends(current_principal)):
    return await request.app.state.services.documents.source(principal,document_id,revision_id)


@router.get('/{document_id}/raw')
async def raw(document_id: str, request: Request, revision_id: str | None = Query(None,alias='revisionId'),
              principal: Principal = Depends(current_principal)):
    body,name,media_type = await request.app.state.services.documents.source(principal,document_id,revision_id,raw=True)
    return Response(body,media_type=media_type,headers={
        'Content-Disposition':"attachment; filename*=UTF-8''" + quote(name,safe=''),
        'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})


@router.post('/{document_id}/reprocess',status_code=202)
async def reprocess(document_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.documents.reprocess(principal,document_id)


@router.post('/{document_id}/deactivate')
async def deactivate(document_id: str, request: Request, principal: Principal = Depends(current_principal)):
    return await request.app.state.services.documents.deactivate(principal,document_id)
