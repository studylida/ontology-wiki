"""[계층 1] Admin Source Document Knowledge Ingestion Router.

Strict Level 4 System Admin Only Endpoint for:
- Listing sources with SHA-256 change detection and separated success/attempt timestamps
- Executing single-process sequential extraction with real-time SSE streaming
- Wiki DTO conversion preview
- Idempotent Wiki database application
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import require_min_level
from backend.app.models.entities import UserModel
from backend.app.repositories.source_repo import source_repo
from backend.app.services.source_service import source_service
from backend.app.services.case_explanation_service import case_explanation_service
from backend.app.schemas.source_ingestion import (
    SourceDocumentItemDTO,
    SourceDocumentListResponse,
    ExtractionRequestDTO, ExtractionStateDTO,
    ApplyExtractionRequestDTO,
    ApplyExtractionResponseDTO
)

logger = logging.getLogger("admin_sources_api")

router = APIRouter(prefix="/admin/sources", tags=["Admin Source Ingestion"])


@router.get(
    "",
    response_model=SourceDocumentListResponse,
    response_model_by_alias=True,
    summary="[Admin] sources/ 디렉터리 원천 기술 백서 목록 및 추출 상태 조회"
)
async def list_source_documents(
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    """Scan sources/ on disk, sync with database, and return status and timestamp metrics."""
    docs = await source_repo.sync_and_list_documents(db)

    items: List[SourceDocumentItemDTO] = []
    succeeded_count = 0
    pending_count = 0
    modified_count = 0

    for d in docs:
        is_succ = d.last_succeeded_at is not None
        is_mod = bool(d.last_succeeded_hash and d.file_hash != d.last_succeeded_hash)

        if is_succ:
            succeeded_count += 1
        else:
            pending_count += 1

        if is_mod:
            modified_count += 1

        items.append(
            SourceDocumentItemDTO(
                docId=d.doc_id,
                filePath=d.file_path,
                publisher=d.publisher,
                title=d.title,
                fileHash=d.file_hash,
                lastSucceededHash=d.last_succeeded_hash,
                lastSucceededAt=d.last_succeeded_at.strftime("%Y-%m-%d %H:%M:%S") if d.last_succeeded_at else None,
                lastAttemptedAt=d.last_attempted_at.strftime("%Y-%m-%d %H:%M:%S") if d.last_attempted_at else None,
                attemptStatus=d.attempt_status,
                isModified=is_mod,
                isApplied=bool(d.is_applied),
                lastAppliedAt=d.last_applied_at.strftime("%Y-%m-%d %H:%M:%S") if d.last_applied_at else None,
                extractedConceptsCount=d.extracted_concepts_count or 0,
                extractedRelationsCount=d.extracted_relations_count or 0,
                lastErrorMessage=d.last_error_message
            )
        )

    return SourceDocumentListResponse(
        documents=items,
        totalCount=len(items),
        succeededCount=succeeded_count,
        pendingCount=pending_count,
        modifiedCount=modified_count
    )


@router.post(
    "/extract",
    summary="[Admin] 선택된 원천 백서 단일 프로세스 순차 추출 실행 (SSE 실시간 스트림)"
)
async def extract_sources_stream(
    body: ExtractionRequestDTO,
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    """Execute knowledge extraction sequentially and stream progress/log/finished events via SSE."""
    if not body.doc_ids:
        raise HTTPException(status_code=400, detail="추출할 문서가 선택되지 않았습니다.")

    # Validate doc_ids existence in database
    valid_doc_ids: List[str] = []
    for did in dict.fromkeys(body.doc_ids):
        doc = await source_repo.get_by_doc_id(db, did)
        if not doc:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 문서 ID입니다: {did}")
        valid_doc_ids.append(did)

    run_id = await source_service.start_extraction(
        session=db,
        doc_ids=valid_doc_ids,
        force_reextract=body.force_reextract,
        resume_interrupted=body.resume_interrupted,
        openai_key=x_openai_key,
        gemini_key=x_gemini_key
    )

    await db.rollback()
    return StreamingResponse(
        source_service.extraction_events(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/extraction-state", response_model=ExtractionStateDTO, response_model_by_alias=True)
async def get_extraction_state(
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    return await source_service.get_extraction_state(db)


@router.get("/extract")
async def reconnect_extraction(
    run_id: str = Query(..., alias="runId"),
    current_user: UserModel = Depends(require_min_level(4))
):
    return StreamingResponse(source_service.extraction_events(run_id), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get(
    "/{doc_id}/preview",
    summary="[Admin] 특정 문서의 최근 추출된 위키 DTO 미리보기 데이터 조회"
)
async def get_document_preview(
    doc_id: str,
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    return await source_service.get_document_preview(db, doc_id)


@router.post(
    "/apply",
    response_model=ApplyExtractionResponseDTO,
    response_model_by_alias=True,
    summary="[Admin] 관리자 확인 완료된 추출 결과를 위키 DB에 최종 원자적 적용"
)
async def apply_extractions_to_wiki(
    body: ApplyExtractionRequestDTO,
    background_tasks: BackgroundTasks,
    x_gemini_key: Optional[str] = Header(None, alias="X-Gemini-Key"),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    current_user: UserModel = Depends(require_min_level(4)),
    db: AsyncSession = Depends(get_db)
):
    """Atomically commit approved extractions to concepts, causal_edges, and evidence_sources."""
    if not body.doc_ids:
        raise HTTPException(status_code=400, detail="적용할 문서 목록이 비어 있습니다.")

    res = await source_service.apply_extractions_to_wiki(
        session=db,
        doc_ids=body.doc_ids,
        expected_versions=body.expected_versions,
        reviewed_by=current_user.name,
        concept_metadata=body.concept_metadata
    )
    case_explanation_service.schedule(background_tasks, res.updated_concepts, gemini_key=x_gemini_key, openai_key=x_openai_key)
    return res
