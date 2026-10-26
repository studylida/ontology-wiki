"""One durable DB worker. No Redis/Celery requirement and no silent replay on restart."""
from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from knowledge.core.config import get_settings
from knowledge.core.errors import AppError
from knowledge.core.ids import utcnow
from knowledge.documents.entities import DocumentRevision
from knowledge.integrations.providers import get_embedding_client, get_generation_client
from knowledge.jobs.entities import Job
from knowledge.jobs.indexing import process_index_job, schedule_daily
from knowledge.jobs.repository import JobRepository

logger = logging.getLogger(__name__)


async def recover_interrupted_jobs(sessions):
    """Recover job and publication-progress state in the same transaction."""
    async with sessions() as session, session.begin():
        jobs = list((await session.scalars(select(Job).where(Job.status == "running")
            .order_by(Job.id).with_for_update())).all())
        for job in jobs:
            job.status, job.finished_at = "failed", utcnow()
            job.error = {"code": "worker_interrupted", "message": "이전 작업 실행이 중단되었습니다. 명시적으로 재시도하세요.", "retryable": True}
            if job.kind == "index":
                revision = await session.get(DocumentRevision, job.payload["sourceRevisionId"], with_for_update=True)
                if revision and revision.index_status == "indexing":
                    revision.index_status = "failed"
        return len(jobs)


def preserve_attempt_usage(job, attempt, usage, error=None):
    current_attempt = job.attempts == attempt and job.status != "pending"
    if current_attempt:
        if usage is not None:
            job.usage = usage
        return True
    # Cancel→retry may occur before the old provider call returns. Its measured
    # usage belongs to the old attempt, not the newly queued/running attempt.
    history = [dict(entry) for entry in (job.result or {}).get("attemptHistory", [])]
    previous = next((entry for entry in reversed(history) if entry.get("attempt") == attempt), None)
    if previous is not None:
        if usage is not None:
            previous["usage"] = usage
        if error is not None:
            previous["error"] = error
        job.result = {**(job.result or {}), "attemptHistory": history}
    return False


async def process_one(sessions, embedding_client, generation_client, settings):
    async with sessions() as session, session.begin():
        job = await JobRepository(session).claim()
        if job is None:
            return False
        job_id, kind, attempt = job.id, job.kind, job.attempts
    try:
        if kind == "index":
            result = await process_index_job(sessions, embedding_client, job_id)
        elif kind == "ontology_extract":
            from knowledge.ontology.extraction import process_ontology_job
            result = await process_ontology_job(sessions, generation_client, job_id, settings)
        elif kind == "source_view":
            from knowledge.ontology.extraction import process_source_view_job
            result = await process_source_view_job(sessions, generation_client, job_id, settings)
        elif kind == "personal_wiki":
            from knowledge.personal_wiki.service import process_job
            result = await process_job(sessions, generation_client, job_id, settings)
        else:
            raise AppError(422, "unknown_job", "지원하지 않는 작업 유형입니다.")
        async with sessions() as session, session.begin():
            job = await session.get(Job, job_id, with_for_update=True)
            current_attempt = preserve_attempt_usage(job, attempt, result.get("usage"))
            if current_attempt and job.status == "running":
                job.status = result.get("status", "succeeded")
                history = (job.result or {}).get("attemptHistory", [])
                job.result = {k: v for k, v in result.items() if k != "usage"}
                if history:
                    job.result["attemptHistory"] = history
                job.finished_at = utcnow()
    except Exception as exc:
        error = exc.public() if isinstance(exc, AppError) else {
            "code": "job_failed", "message": "작업 결과를 처리하지 못했습니다.", "type": type(exc).__name__, "retryable": False}
        logger.warning("job_failed job_id=%s kind=%s error_code=%s", job_id, kind, error["code"])
        async with sessions() as session, session.begin():
            job = await session.get(Job, job_id, with_for_update=True)
            current_attempt = preserve_attempt_usage(job, attempt, getattr(exc, "usage", None), error)
            if current_attempt and job.status == "running":
                job.status, job.error, job.finished_at = "failed", error, utcnow()
                if kind == "index":
                    revision = await session.get(DocumentRevision, job.payload["sourceRevisionId"])
                    if revision.index_status == "indexing":
                        revision.index_status = "failed"
    return True


async def run_worker(*, once=False):
    from knowledge.registry import load_entities
    load_entities()
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    embedding, generation = get_embedding_client(settings), get_generation_client(settings)
    # Session-level lock on an autocommit connection: no transaction spans API calls.
    async with engine.connect() as lock_connection:
        lock_connection = await lock_connection.execution_options(isolation_level="AUTOCOMMIT")
        acquired = await lock_connection.scalar(text("SELECT pg_try_advisory_lock(720261026)"))
        if not acquired:
            raise RuntimeError("A knowledge worker is already running for this database")
        try:
            await recover_interrupted_jobs(sessions)
            while True:
                await schedule_daily(sessions, settings, embedding.profile_id)
                worked = await process_one(sessions, embedding, generation, settings)
                if once:
                    break
                if not worked:
                    await asyncio.sleep(settings.worker_poll_seconds)
        finally:
            await lock_connection.execute(text("SELECT pg_advisory_unlock(720261026)"))
    await engine.dispose()
