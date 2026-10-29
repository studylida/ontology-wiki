"""Wiki indexing persistence; all work validates the immutable revision under the page lock."""
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from ..core.errors import AppError
from ..core.ids import utcnow
from .entities import WikiPage, WikiRevision
from .index_entities import WikiIndexJob, WikiPassage, WikiPassageEmbedding
from .repository import WikiRepository


class WikiIndexRepository:
    def __init__(self, session):
        self.session = session

    async def enqueue(self, page):
        await self.session.execute(update(WikiIndexJob).where(WikiIndexJob.page_id == page.id,
            WikiIndexJob.revision_id != page.current_revision_id, WikiIndexJob.status == 'pending')
            .values(status='superseded', updated_at=utcnow()))
        job = await self.for_revision(page.current_revision_id)
        if job is None:
            job = WikiIndexJob(page_id=page.id, revision_id=page.current_revision_id)
            self.session.add(job)
            await self.session.flush()
        return job

    async def for_revision(self, revision_id):
        return await self.session.scalar(select(WikiIndexJob).where(WikiIndexJob.revision_id == revision_id))

    async def claim(self):
        job = await self.session.scalar(select(WikiIndexJob).where(WikiIndexJob.status == 'pending')
            .order_by(WikiIndexJob.created_at, WikiIndexJob.id).with_for_update(skip_locked=True).limit(1))
        if job:
            job.status, job.attempts, job.updated_at = 'running', job.attempts + 1, utcnow()
            job.error, job.progress = None, {'phase': 'starting'}
        return job

    async def locked(self, job_id):
        snapshot = await self.session.get(WikiIndexJob, job_id)
        if not snapshot:
            raise AppError(404, 'wiki_job_missing', '위키 색인 작업을 찾을 수 없습니다.')
        page = await WikiRepository(self.session).get(snapshot.page_id, lock=True, include_withdrawn=True)
        job = await self.session.get(WikiIndexJob, job_id, with_for_update=True, populate_existing=True)
        revision = await self.session.get(WikiRevision, job.revision_id)
        return page, revision, job

    @staticmethod
    def valid(page, revision, job):
        if job.status != 'running':
            return False
        if page.withdrawn or page.current_revision_id != revision.id:
            job.status, job.updated_at = 'superseded', utcnow()
            return False
        return True

    async def passages(self, revision_id, *, all_passages=False):
        stmt = select(WikiPassage).where(WikiPassage.revision_id == revision_id).order_by(WikiPassage.ordinal)
        if not all_passages:
            stmt = stmt.where(WikiPassage.excluded.is_(False))
        return list(await self.session.scalars(stmt))

    async def has_passages(self, revision_id):
        return bool(await self.session.scalar(select(WikiPassage.id).where(WikiPassage.revision_id == revision_id).limit(1)))

    async def store_passages(self, revision_id, records):
        for p in records:
            self.session.add(WikiPassage(revision_id=revision_id, **p))
        await self.session.flush()

    async def attach(self, profile, units, cached):
        for unit in units:
            await self.session.execute(insert(WikiPassageEmbedding).values(passage_id=unit.passage_id,
                profile_id=profile, embedding_id=cached[unit.input_hash])
                .on_conflict_do_nothing(index_elements=['passage_id', 'profile_id']))

    async def indexed_count(self, profile, units):
        return await self.session.scalar(select(func.count()).select_from(WikiPassageEmbedding).where(
            WikiPassageEmbedding.passage_id.in_([u.passage_id for u in units]), WikiPassageEmbedding.profile_id == profile))

    async def running_ids(self):
        return list(await self.session.scalars(select(WikiIndexJob.id).where(WikiIndexJob.status == 'running')))

    async def retry(self, page, profile):
        job = await self.enqueue(page)
        if job.status == 'failed' or (job.status == 'succeeded' and job.profile_id != profile):
            job.status, job.error, job.progress, job.updated_at = 'pending', None, {'phase': 'queued'}, utcnow()
        return job


    async def cancel(self, page_id):
        await self.session.execute(update(WikiIndexJob).where(WikiIndexJob.page_id == page_id,
            WikiIndexJob.status.in_(['pending', 'running'])).values(status='cancelled', updated_at=utcnow(),
            error={'code': 'wiki_withdrawn', 'message': '위키가 비활성화되었습니다.', 'retryable': False}))
