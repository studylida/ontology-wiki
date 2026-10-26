from copy import deepcopy

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from knowledge.conversations.entities import Conversation, Message
from knowledge.core.errors import AppError
from knowledge.core.ids import utcnow
from knowledge.identity.entities import User
from knowledge.jobs.entities import Job

from .entities import PersonalWikiMessageState, PersonalWikiPage, PersonalWikiRevision


SNAPSHOT_FIELDS = ("title", "topic", "topic_key", "summary", "content", "conditions", "limitations",
                   "citations", "source_revision_ids", "origin_messages", "user_edited")


class PersonalWikiRepository:
    def __init__(self, session):
        self.session = session

    async def user(self, owner_id, *, lock=False):
        stmt = select(User).where(User.id == owner_id)
        return await self.session.scalar(stmt.with_for_update() if lock else stmt)

    async def message_context(self, owner_id, message_id, *, lock=False):
        stmt = select(Message, Conversation).join(Conversation).where(
            Message.id == message_id, Conversation.owner_id == owner_id)
        if lock:
            stmt = stmt.with_for_update(of=(Message, Conversation))
        row = (await self.session.execute(stmt)).first()
        if row is None:
            raise AppError(404, "WIKI_MESSAGE_NOT_FOUND", "정리할 대화 메시지를 찾을 수 없습니다.")
        return row

    async def question_before(self, message):
        return await self.session.scalar(select(Message.content).where(
            Message.conversation_id == message.conversation_id, Message.role == "user",
            Message.created_at <= message.created_at).order_by(Message.created_at.desc(), Message.id.desc()).limit(1))

    async def job(self, job_id, *, lock=False):
        stmt = select(Job).where(Job.id == job_id, Job.kind == "personal_wiki")
        return await self.session.scalar(stmt.with_for_update().execution_options(populate_existing=True) if lock else stmt)

    async def state(self, owner_id, message_id, conversation_id, *, create=False):
        if create:
            await self.session.execute(insert(PersonalWikiMessageState).values(
                owner_id=owner_id, message_id=message_id, conversation_id=conversation_id,
                generation=0, is_suppressed=False, updated_at=utcnow(),
            ).on_conflict_do_nothing(index_elements=["owner_id", "message_id"]))
        return await self.session.get(PersonalWikiMessageState, (owner_id, message_id))

    async def page(self, owner_id, page_id, *, lock=False, include_deleted=False):
        stmt = select(PersonalWikiPage).where(PersonalWikiPage.id == page_id,
                                               PersonalWikiPage.owner_id == owner_id)
        if not include_deleted:
            stmt = stmt.where(PersonalWikiPage.deleted_at.is_(None))
        row = await self.session.scalar(stmt.with_for_update() if lock else stmt)
        if row is None:
            raise AppError(404, "WIKI_PAGE_NOT_FOUND", "개인 위키 페이지를 찾을 수 없습니다.")
        return row

    async def by_topic(self, owner_id, topic_key):
        return await self.session.scalar(select(PersonalWikiPage).where(
            PersonalWikiPage.owner_id == owner_id, PersonalWikiPage.topic_key == topic_key,
            PersonalWikiPage.deleted_at.is_(None)))

    async def pages(self, owner_id):
        return list(await self.session.scalars(select(PersonalWikiPage).where(
            PersonalWikiPage.owner_id == owner_id, PersonalWikiPage.deleted_at.is_(None))
            .order_by(PersonalWikiPage.updated_at.desc(), PersonalWikiPage.id)))

    async def revisions(self, page_id):
        return list(await self.session.scalars(select(PersonalWikiRevision).where(
            PersonalWikiRevision.page_id == page_id).order_by(PersonalWikiRevision.version.desc())))

    async def revision(self, page_id, version):
        return await self.session.scalar(select(PersonalWikiRevision).where(
            PersonalWikiRevision.page_id == page_id, PersonalWikiRevision.version == version))

    def add_revision(self, page, operation, *, parent_version, job_id=None, restored_from_version=None):
        self.session.add(PersonalWikiRevision(
            page_id=page.id, version=page.version, operation=operation, parent_version=parent_version,
            restored_from_version=restored_from_version, job_id=job_id,
            snapshot={name: deepcopy(getattr(page, name)) for name in SNAPSHOT_FIELDS},
        ))

    async def suppress(self, owner_id, origins, reason):
        for origin in origins:
            state = await self.state(owner_id, origin["messageId"], origin["conversationId"], create=True)
            state.is_suppressed = True
            state.suppression_reason, state.suppressed_at = reason, utcnow()
            state.generation += 1
            state.last_outcome, state.updated_at = "suppressed", utcnow()
        await self.cancel_jobs(owner_id, [item["messageId"] for item in origins], reason)

    async def cancel_jobs(self, owner_id, message_ids=None, reason="automatic_organization_disabled", *, automatic_only=False):
        stmt = update(Job).where(Job.owner_id == owner_id, Job.kind == "personal_wiki",
                                 Job.status.in_(("pending", "running")))
        if message_ids is not None:
            if not message_ids:
                return
            stmt = stmt.where(Job.payload["messageId"].astext.in_(message_ids))
        if automatic_only:
            stmt = stmt.where(Job.payload["explicit"].as_boolean().is_(False))
        await self.session.execute(stmt.values(status="cancelled", finished_at=utcnow(),
            result={"action": "skipped", "reason": reason}))

    async def conversation_origins(self, owner_id, conversation_id):
        ids = await self.session.scalars(select(Message.id).join(Conversation).where(
            Conversation.id == conversation_id, Conversation.owner_id == owner_id))
        return [{"messageId": value, "conversationId": conversation_id} for value in ids]
