from fastapi import APIRouter, Depends, Request
from pydantic import Field

from knowledge.core.dto import DTO
from knowledge.core.errors import AppError
from knowledge.identity.dependencies import current_principal
from knowledge.jobs.service import JobService

router = APIRouter(tags=["jobs"])


class IndexRequest(DTO):
    source_revision_ids: list[str] = Field(default_factory=list, max_length=100)
    immediate: bool = True


def service(request):
    return JobService(request.app.state.session_factory, request.app.state.embedding_client.profile_id)


@router.post("/index-jobs", status_code=202)
async def create_index_jobs(body: IndexRequest, request: Request, principal=Depends(current_principal)):
    if not body.immediate:
        raise AppError(422, "use_daily_schedule", "일일 갱신은 승인 문헌을 서버 일정에 따라 처리합니다. 이 API는 명시적 즉시 요청입니다.")
    return await service(request).enqueue_index(principal, body.source_revision_ids)


@router.get("/jobs")
async def jobs(request: Request, kind: str | None = None, principal=Depends(current_principal)):
    return await service(request).list(principal, kind)


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request, principal=Depends(current_principal)):
    return await service(request).cancel(principal, job_id)


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, request: Request, principal=Depends(current_principal)):
    return await service(request).retry(principal, job_id)
