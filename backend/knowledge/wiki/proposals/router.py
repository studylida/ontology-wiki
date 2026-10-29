from fastapi import APIRouter, Depends, Query, Request
from ...identity.dependencies import current_principal
from .dto import ProposalApply, ProposalRequest
from ..dto import MutationResult

router = APIRouter(prefix='/wiki/proposals', tags=['wiki proposals'])


@router.post('', status_code=202)
async def submit(body: ProposalRequest, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.proposals.submit(principal, body)


@router.get('')
async def listing(request: Request, page_id: str | None = Query(default=None, alias='pageId', max_length=80),
                  principal=Depends(current_principal)):
    return await request.app.state.services.proposals.list(principal, page_id)


@router.get('/{proposal_id}')
async def get(proposal_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.proposals.get(principal, proposal_id)


@router.post('/{proposal_id}/dismiss')
async def dismiss(proposal_id: str, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.proposals.dismiss(principal, proposal_id)


@router.post('/{proposal_id}/apply', response_model=MutationResult)
async def apply(proposal_id: str, body: ProposalApply, request: Request, principal=Depends(current_principal)):
    return await request.app.state.services.proposals.apply(principal, proposal_id, body)
