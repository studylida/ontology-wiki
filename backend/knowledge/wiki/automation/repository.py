"""Durable, revision-keyed change queue. No source writes or provider calls."""
from sqlalchemy import select, text, update, func, exists
from sqlalchemy.dialects.postgresql import insert
from ...core.ids import new_id, utcnow
from ...documents.entities import Document, DocumentRevision
from ..proposals.entities import WikiProposal
from .entities import DocumentWikiJob

MIGRATION = '008_wiki_document_proposals.sql'


def current_source():
    return (Document.withdrawn.is_(False), Document.active_revision_id == DocumentRevision.id,
            Document.current_revision_id == DocumentRevision.id, DocumentRevision.index_status == 'ready')


class DocumentWikiRepository:
    def __init__(self, session):
        self.session = session

    async def cutoff(self):
        # The migration boundary prevents a surprise paid backfill of old corpora.
        cutoff = await self.session.scalar(text(
            'SELECT applied_at FROM knowledge_schema_migrations WHERE version=:version'), {'version': MIGRATION})
        if cutoff is None:
            raise RuntimeError('Document suggestion migration missing')
        return cutoff

    async def reconcile(self):
        cutoff = await self.cutoff()
        ids = await self.session.scalars(select(DocumentRevision.id).join(Document,
            Document.id == DocumentRevision.document_id).where(*current_source(),
            DocumentRevision.created_at >= cutoff,
            ~exists(select(DocumentWikiJob.id).where(DocumentWikiJob.source_revision_id == DocumentRevision.id)))
            .order_by(DocumentRevision.created_at, DocumentRevision.id).limit(20))
        for revision_id in ids:
            await self.session.execute(insert(DocumentWikiJob).values(id=new_id('wdj'),
                source_revision_id=revision_id, status='pending', result={}, usage={},
                created_at=utcnow(), updated_at=utcnow()).on_conflict_do_nothing(index_elements=['source_revision_id']))
        usable = select(DocumentRevision.id).join(Document, Document.id == DocumentRevision.document_id).where(*current_source())
        await self.session.execute(update(DocumentWikiJob).where(DocumentWikiJob.status == 'pending',
            DocumentWikiJob.source_revision_id.not_in(usable)).values(status='superseded', updated_at=utcnow()))

    async def daily_used(self):
        start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.session.scalar(select(func.count()).select_from(DocumentWikiJob)
            .where(DocumentWikiJob.started_at >= start))

    async def claim(self, daily_limit):
        # The existing exclusive worker lock serializes reservations across restarts.
        if await self.daily_used() >= daily_limit:
            return None
        item = await self.session.scalar(select(DocumentWikiJob).where(DocumentWikiJob.status == 'pending')
            .order_by(DocumentWikiJob.created_at, DocumentWikiJob.id).with_for_update(skip_locked=True).limit(1))
        if item:
            item.status, item.started_at, item.updated_at = 'running', utcnow(), utcnow()
        return item

    async def get(self, identity, *, lock=False):
        stmt = select(DocumentWikiJob).where(DocumentWikiJob.id == identity)
        return await self.session.scalar(stmt.with_for_update() if lock else stmt)

    async def for_revision(self, revision_id):
        return await self.session.scalar(select(DocumentWikiJob).where(DocumentWikiJob.source_revision_id == revision_id))

    async def proposals(self, revision_id):
        return list(await self.session.scalars(select(WikiProposal).where(WikiProposal.origin_revision_id == revision_id)
            .order_by(WikiProposal.created_at, WikiProposal.id).limit(10)))

    async def recover(self):
        await self.session.execute(update(DocumentWikiJob).where(DocumentWikiJob.status == 'running').values(
            status='failed', updated_at=utcnow(), error={'code': 'worker_interrupted',
            'message': '자동 검토가 중단됐습니다. 중복 비용 방지를 위해 자동으로 다시 호출하지 않습니다.'}))
