"""Comparison controllers. Interpretation and persistence live below the HTTP layer."""
from fastapi import APIRouter, Depends, Query
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_optional
from backend.app.schemas.comparison import (
    ClarifyRequest, ClarifyResponse, ComparisonSessionCreate, ComparisonSessionDTO,
    SessionPatchRequest, SessionPatchResponse, MatrixRecalculateRequest, MatrixRecalculateResponse,
    DeepDiveRequest, DeepDiveResponse, TuneAdvisorRequest, TuneAdvisorResponse,
    ExportReviewRequest, ExportReviewResponse, ResearchEnrichmentRequest, ComparisonConceptOption,
)
from backend.app.api.knowledge_dependencies import knowledge_errors, llm_keys
from backend.app.services.comparison_service import comparison_service

router = APIRouter(tags=["Comparison Studio"], dependencies=[Depends(knowledge_errors)])


@router.get("/comparison/concepts", response_model=list[ComparisonConceptOption])
async def list_comparison_concepts(db=Depends(get_db)):
    return await comparison_service.concepts(db)


@router.post("/comparison/clarify", response_model=ClarifyResponse)
async def clarify(body: ClarifyRequest, db=Depends(get_db), keys=Depends(llm_keys)):
    return await comparison_service.clarify(db, body, **keys)


@router.get("/comparison-sessions", response_model=list[ComparisonSessionDTO])
async def list_sessions(limit: int = Query(20, ge=1, le=50), db=Depends(get_db)):
    return await comparison_service.list(db, limit)


@router.post("/comparison-sessions", response_model=ComparisonSessionDTO, status_code=201)
async def create_session(body: ComparisonSessionCreate, db=Depends(get_db),
                         user=Depends(get_current_user_optional), keys=Depends(llm_keys)):
    return await comparison_service.create(db, body, user, **keys)


@router.get("/comparison-sessions/{session_id}", response_model=ComparisonSessionDTO)
async def get_session(session_id: str, db=Depends(get_db)):
    return comparison_service.dto(await comparison_service.get(db, session_id))


@router.patch("/comparison-sessions/{session_id}", response_model=SessionPatchResponse)
async def patch_session(session_id: str, body: SessionPatchRequest, db=Depends(get_db)):
    return await comparison_service.patch(db, session_id, body)


@router.post("/comparison-sessions/{session_id}/matrix", response_model=MatrixRecalculateResponse)
async def matrix(session_id: str, body: MatrixRecalculateRequest, db=Depends(get_db), keys=Depends(llm_keys)):
    return await comparison_service.update_matrix(db, session_id, body, **keys)


@router.post("/comparison-sessions/{session_id}/deep-dive", response_model=DeepDiveResponse)
async def deep_dive(session_id: str, body: DeepDiveRequest, db=Depends(get_db), keys=Depends(llm_keys)):
    entry, _ = await comparison_service.question(db, session_id, body.query, **keys)
    return {"sessionId": session_id, "tailQuestion": entry}


@router.post("/comparison-sessions/{session_id}/tune-advisor", response_model=TuneAdvisorResponse)
async def tune_advisor(session_id: str, body: TuneAdvisorRequest, db=Depends(get_db), keys=Depends(llm_keys)):
    if body.applyCompensation:
        from fastapi import HTTPException
        raise HTTPException(422, "저장된 근거 없이 보상안을 자동 적용할 수 없습니다. 추가 조건을 질문으로 입력해 주세요.")
    entry, session = await comparison_service.question(db, session_id, body.userPrompt, body.manualConditions, **keys)
    return {"userPrompt": entry["query"], "riskDetected": "", "advisorRecommendation": {},
            "advice": entry["explanation"], "session": session}


@router.post("/comparison-sessions/{session_id}/research-evidence", response_model=ComparisonSessionDTO)
async def research_evidence(session_id: str, body: ResearchEnrichmentRequest,
                            db=Depends(get_db), keys=Depends(llm_keys)):
    return await comparison_service.enrich(db, session_id, body, **keys)


@router.post("/comparison-sessions/{session_id}/export-review", response_model=ExportReviewResponse)
async def export_review(session_id: str, body: ExportReviewRequest,
                        db=Depends(get_db), user=Depends(get_current_user_optional)):
    return await comparison_service.export(db, session_id, body, user)
