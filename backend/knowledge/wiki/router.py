from fastapi import APIRouter, Depends, Query, Request
from ..identity.dependencies import current_principal
from .dto import (MutationResult, PageCreate, PageDetail, PageEdit, PageList, PageProtection,
                  PageRestore, RevisionComparison, RevisionList, RevisionView)

router = APIRouter(prefix='/wiki/pages', tags=['shared wiki'])


@router.get('', response_model=PageList)
async def listing(request: Request, q: str = Query(default='', max_length=300),
                  limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0),
                  principal=Depends(current_principal)):
    return await request.app.state.services.wiki.list(principal, q, limit, offset)


@router.post('', response_model=MutationResult, status_code=201)
async def create(body: PageCreate, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki.mutate(principal, 'create', body)


@router.get('/{page_id}', response_model=PageDetail)
async def detail(page_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki.get(principal, page_id)


@router.get('/{page_id}/revisions', response_model=RevisionList)
async def history(page_id: str, request: Request, limit: int = Query(default=30, ge=1, le=100),
                  offset: int = Query(default=0, ge=0), principal=Depends(current_principal)):
    return await request.app.state.services.wiki.history(principal, page_id, limit, offset)


@router.post('/{page_id}/revisions', response_model=MutationResult, status_code=201)
async def edit(page_id: str, body: PageEdit, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki.mutate(principal, 'edit', body, page_id)


@router.get('/{page_id}/revisions/{revision_id}', response_model=RevisionView)
async def revision(page_id: str, revision_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki.revision(principal, page_id, revision_id)


@router.get('/{page_id}/compare', response_model=RevisionComparison)
async def compare(page_id: str, request: Request, from_revision_id: str = Query(alias='fromRevisionId', max_length=80),
                  to_revision_id: str = Query(alias='toRevisionId', max_length=80), principal=Depends(current_principal)):
    return await request.app.state.services.wiki.compare(principal, page_id, from_revision_id, to_revision_id)


@router.post('/{page_id}/restore', response_model=MutationResult, status_code=201)
async def restore(page_id: str, body: PageRestore, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki.mutate(principal, 'restore', body, page_id)


@router.patch('/{page_id}/protection', response_model=MutationResult)
async def protect(page_id: str, body: PageProtection, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki.mutate(principal, 'protect', body, page_id)
