"""Small serial worker. A PostgreSQL advisory lock prevents duplicate consumers.

Document/wiki indexing and requested wiki drafts share this bounded serial executor. No automatic proposals or ontology extraction. A crashed
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


async def run_worker(*, once=False, settings=None, embedding_client=None, generation_client=None):
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
                from ..wiki.proposals.repository import ProposalRepository
                from ..wiki.proposals.generation import process_proposal_job
                async with sessions() as session, session.begin():
                    await ProposalRepository(session).recover()
                processed, cursor = 0, 0
                while True:
                    async with sessions() as session, session.begin():
                        queues = [('document_index', JobRepository(session)), ('wiki_index', WikiIndexRepository(session)),
                                  ('wiki_proposal', ProposalRepository(session))]
                        queues = queues[cursor:] + queues[:cursor]
                        job, kind = None, None
                        for kind, repository in queues:
                            job = await repository.claim()
                            if job is not None:
                                break
                        job_id = job.id if job else None
                    if job_id:
                        cursor = ({'document_index': 0, 'wiki_index': 1, 'wiki_proposal': 2}[kind] + 1) % 3
                        if kind == 'wiki_proposal':
                            result = await process_proposal_job(sessions, settings, job_id, embedding_client, generation_client)
                        else:
                            processor = process_wiki_index_job if kind == 'wiki_index' else process_index_job
                            result = await processor(sessions, settings, job_id, embedding_client)
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
