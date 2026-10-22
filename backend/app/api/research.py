"""Literature research controllers; keep acquisition and synthesis in their own layers."""
from fastapi import APIRouter, Depends, Query
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_optional
from backend.app.schemas.research import (
    ResearchSessionListResponse, ResearchClarifyRequest, ResearchClarifyResponse,
    ResearchDiscoverRequest, ResearchDiscoverResponse, ResearchSynthesizeRequest,
    ResearchSynthesizeResponse, ResearchSessionDetail,
    ExportCandidateTicketRequest, ExportCandidateTicketResponse,
)
from backend.app.api.knowledge_dependencies import knowledge_errors, llm_keys
from backend.app.services.research_service import research_service

router = APIRouter(prefix="/research", tags=["Deep Research"], dependencies=[Depends(knowledge_errors)])


@router.get("/sessions", response_model=ResearchSessionListResponse)
async def list_sessions(limit: int = Query(15, ge=1, le=50), db=Depends(get_db)):
    return await research_service.list(db, limit)


@router.post("/clarify", response_model=ResearchClarifyResponse)
async def clarify(body: ResearchClarifyRequest):
    return research_service.clarify(body)


@router.post("/discover", response_model=ResearchDiscoverResponse)
async def discover(body: ResearchDiscoverRequest, db=Depends(get_db)):
    return await research_service.discover(db, body)


@router.get("/sessions/{session_id}", response_model=ResearchSessionDetail)
async def get_session(session_id: str, db=Depends(get_db)):
    return research_service.detail(await research_service.get(db, session_id))


@router.post("/sessions/{session_id}/synthesize", response_model=ResearchSynthesizeResponse)
async def synthesize(session_id: str, body: ResearchSynthesizeRequest, db=Depends(get_db), keys=Depends(llm_keys)):
    return await research_service.synthesize(db, session_id, body, **keys)


@router.post("/candidates/{candidate_id}/export-ticket", response_model=ExportCandidateTicketResponse)
async def export_ticket(candidate_id: str, body: ExportCandidateTicketRequest,
                        db=Depends(get_db), user=Depends(get_current_user_optional)):
    return await research_service.export(db, candidate_id, body, user)
