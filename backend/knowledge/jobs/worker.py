"""Small serial worker. A PostgreSQL advisory lock prevents duplicate consumers.

Document and wiki index queues share this serial executor; no generation or ontology extraction. A crashed
running job is recorded as interrupted on next start and can be explicitly retried.
"""
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from ..core.config import get_settings
from ..core.ids import utcnow
from ..documents.entities import DocumentRevision
from ..documents.repository import DocumentRepository
from ..migration.schema import assert_current_schema
from ..registry import load_entities
from .entities import Job
from .repository import JobRepository

WORKER_LOCK = 820261029


async def recover_interrupted(sessions):
    async with sessions() as session:
        jobs = list((await session.execute(select(Job.id,Job.document_id).where(Job.status == 'running'))).all())
    for job_id,document_id in jobs:
        async with sessions() as session, session.begin():
            document = await DocumentRepository(session).get(document_id,lock=True)
            job = await session.get(Job,job_id,with_for_update=True)
            if job.status != 'running':
                continue
            revision = await session.get(DocumentRevision,job.source_revision_id)
            if document.withdrawn or document.current_revision_id != revision.id:
                job.status = 'superseded'
            else:
                job.status = 'failed'
                job.error = {'code':'worker_interrupted','message':'이전 작업자가 종료되었습니다. 재처리를 요청해 주세요.','retryable':True}
                revision.index_status = 'failed'
            job.updated_at = utcnow()


async def run_worker(*, once=False, settings=None, embedding_client=None):
    settings = settings or get_settings()
    load_entities()
    engine = create_async_engine(settings.database_url,pool_pre_ping=True)
    sessions = async_sessionmaker(engine,expire_on_commit=False,autoflush=False)
    try:
        async with engine.connect() as lock_connection:
            await assert_current_schema(lock_connection)
            acquired = await lock_connection.scalar(text('SELECT pg_try_advisory_lock(:key)'),{'key':WORKER_LOCK})
            await lock_connection.commit()
            if not acquired:
                return {'status':'busy','processed':0}
            try:
                await recover_interrupted(sessions)
                from ..wiki.indexing import recover_wiki_jobs, process_wiki_index_job
                from ..wiki.index_repository import WikiIndexRepository
                await recover_wiki_jobs(sessions)
                from ..indexing.service import process_index_job
                processed = 0
                wiki_first = False
                while True:
                    async with sessions() as session, session.begin():
                        queues = [('wiki_index', WikiIndexRepository(session)), ('document_index', JobRepository(session))]
                        if not wiki_first:
                            queues.reverse()
                        job, kind = None, None
                        for kind, repository in queues:
                            job = await repository.claim()
                            if job is not None:
                                break
                        job_id = job.id if job else None
                    if job_id:
                        wiki_first = kind != 'wiki_index'
                        processor = process_wiki_index_job if kind == 'wiki_index' else process_index_job
                        result = await processor(sessions,settings,job_id,embedding_client)
                        processed += 1
                        if once:
                            return {**result,'processed':processed}
                    elif once:
                        return {'status':'idle','processed':0}
                    else:
                        await asyncio.sleep(settings.worker_poll_seconds)
            finally:
                await lock_connection.execute(text('SELECT pg_advisory_unlock(:key)'),{'key':WORKER_LOCK})
                await lock_connection.commit()
    finally:
        await engine.dispose()
