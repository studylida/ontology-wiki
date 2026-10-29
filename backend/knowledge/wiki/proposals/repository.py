"""Proposal storage/queue only. Access and publication rules live in the service."""
import hashlib
from sqlalchemy import select, text, update, or_, and_, exists
from ...core.errors import AppError
from ...core.ids import utcnow
from ...documents.entities import Document, DocumentRevision
from ..entities import WikiPage, WikiRevision
from .entities import WikiProposal


class ProposalRepository:
    def __init__(self, session):
        self.session = session

    async def request_lock(self, owner_id, request_id):
        key = int.from_bytes(hashlib.sha256(f'proposal:{owner_id}:{request_id}'.encode()).digest()[:8], 'big', signed=True)
        await self.session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': key})
        return await self.session.scalar(select(WikiProposal).where(
            WikiProposal.owner_id == owner_id, WikiProposal.request_id == request_id))

    async def get(self, identity, *, lock=False):
        statement = select(WikiProposal).where(WikiProposal.id == identity)
        if lock:
            statement = statement.with_for_update()
        item = await self.session.scalar(statement)
        if item is None:
            raise AppError(404, 'proposal_not_found', '제안을 찾을 수 없습니다.')
        return item

    async def list(self, owner_id, *, admin=False, page_id=None):
        public_source = exists(select(DocumentRevision.id).join(Document, Document.id == DocumentRevision.document_id)
            .where(DocumentRevision.id == WikiProposal.origin_revision_id, Document.withdrawn.is_(False)))
        private_scope = WikiProposal.owner_id == owner_id
        if admin and page_id:
            private_scope = or_(private_scope, WikiProposal.page_id == page_id)
        scope = or_(and_(WikiProposal.origin_revision_id.is_(None), private_scope),
                    and_(WikiProposal.origin_revision_id.is_not(None), public_source))
        statement = select(WikiProposal).where(scope)
        if page_id:
            statement = statement.where(WikiProposal.page_id == page_id)
        else:
            statement = statement.where(WikiProposal.page_id.is_(None))
        return list(await self.session.scalars(statement.order_by(WikiProposal.created_at.desc()).limit(30)))

    async def claim(self, *, include_document=True):
        item = await self.session.scalar(select(WikiProposal).where(WikiProposal.status == 'pending',
            True if include_document else WikiProposal.origin_revision_id.is_(None))
            .order_by(WikiProposal.created_at, WikiProposal.id).with_for_update(skip_locked=True).limit(1))
        if item:
            item.status, item.updated_at = 'running', utcnow()
        return item

    async def recover(self):
        await self.session.execute(update(WikiProposal).where(WikiProposal.status == 'running').values(
            status='failed', updated_at=utcnow(), error={'code': 'worker_interrupted',
            'message': '이전 생성이 중단됐습니다. 내용을 확인하고 명시적으로 다시 요청해 주세요.'}))

    async def mentions(self, markdown, exclude=None):
        # Name matches supply candidates only; the model still verifies contextual identity.
        statement = select(WikiPage, WikiRevision).join(WikiRevision,
            and_(WikiRevision.page_id == WikiPage.id, WikiRevision.id == WikiPage.current_revision_id))
        statement = statement.where(WikiPage.withdrawn.is_(False), text(
            "EXISTS (SELECT 1 FROM jsonb_array_elements_text(wiki_revisions.name_keys) n "
            "WHERE length(n) >= 2 AND strpos(:body, n) > 0)")).params(body=markdown.casefold())
        if exclude:
            statement = statement.where(WikiPage.id != exclude)
        return (await self.session.execute(statement.order_by(WikiPage.id).limit(12))).all()
