"""Wiki persistence and serialization locks. No role or model policy here."""
import hashlib
from sqlalchemy import func, select, text
from sqlalchemy.orm import aliased
from ..core.errors import AppError
from ..core.ids import new_id, utcnow
from ..identity.entities import User
from .entities import WikiMutation, WikiPage, WikiRevision


class WikiRepository:
    def __init__(self, session):
        self.session = session

    async def mutation(self, actor_id, request_id):
        # A repeated create has no page row yet. Serialize by actor + request first.
        key = int.from_bytes(hashlib.sha256(f'wiki:{actor_id}:{request_id}'.encode()).digest()[:8], 'big', signed=True)
        await self.session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': key})
        return await self.session.get(WikiMutation, (actor_id, request_id))

    async def get(self, page_id, *, lock=False):
        stmt = select(WikiPage).where(WikiPage.id == page_id)
        if lock:
            stmt = stmt.with_for_update()
        page = await self.session.scalar(stmt)
        if page is None:
            raise AppError(404, 'wiki_not_found', '위키 문서를 찾을 수 없습니다.')
        return page

    def _page_query(self):
        creator, editor = aliased(User), aliased(User)
        return select(WikiPage, WikiRevision, creator, editor).join(
            WikiRevision, (WikiRevision.page_id == WikiPage.id) & (WikiRevision.id == WikiPage.current_revision_id)
        ).join(creator, creator.id == WikiPage.creator_id).join(editor, editor.id == WikiRevision.editor_id)

    async def detail(self, page_id):
        row = (await self.session.execute(self._page_query().where(WikiPage.id == page_id))).first()
        if row is None:
            raise AppError(404, 'wiki_not_found', '위키 문서를 찾을 수 없습니다.')
        return row

    async def list(self, query, limit, offset):
        predicate = func.lower(WikiRevision.title).contains(query.casefold(), autoescape=True)
        stmt = self._page_query().where(predicate)
        rows = (await self.session.execute(stmt.order_by(WikiPage.updated_at.desc(), WikiPage.id).offset(offset).limit(limit))).all()
        total = await self.session.scalar(select(func.count()).select_from(WikiPage).join(
            WikiRevision, WikiRevision.id == WikiPage.current_revision_id).where(predicate))
        return rows, total

    async def revision(self, page_id, revision_id):
        row = (await self.session.execute(select(WikiRevision, User).join(User, User.id == WikiRevision.editor_id)
            .where(WikiRevision.page_id == page_id, WikiRevision.id == revision_id))).first()
        if row is None:
            raise AppError(404, 'wiki_revision_not_found', '이 문서의 판본을 찾을 수 없습니다.')
        return row

    async def history(self, page_id, limit, offset):
        await self.get(page_id)
        rows = (await self.session.execute(select(WikiRevision, User).join(User, User.id == WikiRevision.editor_id)
            .where(WikiRevision.page_id == page_id).order_by(WikiRevision.number.desc()).offset(offset).limit(limit))).all()
        total = await self.session.scalar(select(func.count()).select_from(WikiRevision).where(WikiRevision.page_id == page_id))
        return rows, total

    async def create(self, actor_id, body):
        now, page_id, revision_id = utcnow(), new_id('wpg'), new_id('wrv')
        page = WikiPage(id=page_id, creator_id=actor_id, current_revision_id=revision_id,
            version=1, is_locked=False, created_at=now, updated_at=now)
        self.session.add(page)
        await self.session.flush()  # Current-revision FK is deferred until commit.
        revision = WikiRevision(id=revision_id, page_id=page_id, number=1, title=body.title,
            markdown=body.markdown, source_note=body.source_note, change_summary=body.change_summary,
            editor_id=actor_id, created_at=now)
        self.session.add(revision)
        await self.session.flush()
        return page

    async def append(self, page, actor_id, *, title, markdown, source_note, summary, restored_from=None):
        previous, _ = await self.revision(page.id, page.current_revision_id)
        now = utcnow()
        revision = WikiRevision(id=new_id('wrv'), page_id=page.id, number=previous.number + 1,
            title=title, markdown=markdown, source_note=source_note, change_summary=summary,
            editor_id=actor_id, restored_from_id=restored_from, created_at=now)
        self.session.add(revision)
        await self.session.flush()
        page.current_revision_id, page.updated_at = revision.id, now
        page.version += 1
        await self.session.flush()

    async def protect(self, page, actor_id, locked):
        if page.is_locked != locked:
            page.is_locked = locked
            page.protection_updated_by = actor_id
            page.protection_updated_at = page.updated_at = utcnow()
            # Even lock -> unlock invalidates a form opened before protection changed.
            page.version += 1
        await self.session.flush()

    async def remember(self, actor_id, request_id, digest, page, result):
        self.session.add(WikiMutation(actor_id=actor_id, request_id=request_id, payload_hash=digest,
            page_id=page.id, result=result, created_at=utcnow()))
        await self.session.flush()
