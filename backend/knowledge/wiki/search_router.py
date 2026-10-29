from fastapi import APIRouter, Depends, Request
from ..identity.dependencies import current_principal
from .search_dto import IndexRetry, IndexStatus, NameAlternative, SearchQuery, SearchResult, SimilarQuery

router = APIRouter(prefix='/wiki', tags=['wiki discovery'])


@router.post('/search', response_model=SearchResult)
async def search(body: SearchQuery, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki_search.search(principal, body.query,
        limit=body.limit, exclude=body.exclude_page_id)


@router.post('/similar', response_model=SearchResult)
async def similar(body: SimilarQuery, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki_search.similar(principal, body.title, body.markdown,
        exclude=body.exclude_page_id)


@router.get('/pages/{page_id}/alternatives', response_model=list[NameAlternative])
async def alternatives(page_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki_search.alternatives(principal, page_id)


@router.get('/pages/{page_id}/index', response_model=IndexStatus)
async def status(page_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki_search.status(principal, page_id)


@router.post('/pages/{page_id}/index/retry', response_model=IndexStatus, status_code=202)
async def retry(page_id: str, body: IndexRetry, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.wiki_search.retry(principal, page_id, body.base_version)
