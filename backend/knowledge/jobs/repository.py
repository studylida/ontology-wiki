"""Queue state and explicit retries. Processing logic lives in Indexing."""
from sqlalchemy import select
from ..core.ids import utcnow
from .entities import Job


class JobRepository:
    def __init__(self, session):
        self.session = session

    async def for_revision(self, revision_id, *, lock=False):
        stmt = select(Job).where(Job.source_revision_id == revision_id)
        if lock:
            stmt = stmt.with_for_update()
        return await self.session.scalar(stmt)

    async def enqueue(self, document_id, revision_id):
        existing = await self.for_revision(revision_id)
        if existing:
            return existing
        job = Job(document_id=document_id, source_revision_id=revision_id)
        self.session.add(job)
        await self.session.flush()
        return job

    async def claim(self):
        job = await self.session.scalar(select(Job).where(Job.status == 'pending')
            .order_by(Job.created_at, Job.id).with_for_update(skip_locked=True).limit(1))
        if job:
            job.status, job.attempts, job.updated_at = 'running', job.attempts + 1, utcnow()
            job.error, job.progress = None, {'phase': 'starting'}
        return job

    @staticmethod
    def restart(job):
        # Caller holds the document lock. Pending/running/succeeded are no-ops.
        if job.status == 'failed':
            job.status, job.error, job.progress = 'pending', None, {'phase': 'queued'}
            job.updated_at = utcnow()

    @staticmethod
    def public(job):
        if job is None:
            return None
        return {'id': job.id, 'kind': job.kind, 'status': job.status, 'attempts': job.attempts,
                'progress': job.progress, 'error': job.error, 'usage': job.usage,
                'updatedAt': job.updated_at.isoformat()}
