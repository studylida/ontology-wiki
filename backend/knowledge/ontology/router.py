from fastapi import APIRouter, Depends, Query, Request

from knowledge.identity.dependencies import current_principal
from knowledge.ontology.service import OntologyService

router = APIRouter(prefix="/ontology", tags=["ontology"])


def service(request):
    return OntologyService(request.app.state.session_factory)


@router.get("/concepts")
async def concepts(request: Request, q: str = "", cursor: str | None = None, limit: int = Query(40, ge=1, le=100), principal=Depends(current_principal)):
    return await service(request).concepts(principal, q, cursor, limit)


@router.get("/concepts/{concept_id}")
async def concept(concept_id: str, request: Request, principal=Depends(current_principal)):
    return await service(request).concept(principal, concept_id)


@router.get("/concepts/{concept_id}/relations")
async def relations(concept_id: str, request: Request, principal=Depends(current_principal)):
    return await service(request).relations(principal, concept_id)


@router.get("/concepts/{concept_id}/source-views")
async def source_views(concept_id: str, request: Request, publisherId: str | None = None,
    sourceType: str | None = None, aspect: str | None = None, dateFrom: str | None = None,
    dateTo: str | None = None, cursor: str | None = None, limit: int = Query(40, ge=1, le=100),
    principal=Depends(current_principal)):
    return await service(request).source_views(principal, concept_id, publisher_id=publisherId,
        source_type=sourceType, aspect=aspect, date_from=dateFrom, date_to=dateTo, cursor=cursor, limit=limit)
