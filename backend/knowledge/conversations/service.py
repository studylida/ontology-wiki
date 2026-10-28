from ..core.ids import utcnow
from .dto import ConversationDetail, ConversationList, ConversationView, MessageView
from .repository import ConversationRepository


class ConversationService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def list(self, principal):
        principal.require("conversations:read")
        async with self.session_factory() as session:
            rows = await ConversationRepository(session).list(principal.id)
            return ConversationList(items=[ConversationView.model_validate(row) for row in rows])

    async def create(self, principal, body):
        principal.require("conversations:write")
        async with self.session_factory() as session, session.begin():
            row = await ConversationRepository(session).create(principal.id, body.title or "새 대화")
            return ConversationView.model_validate(row)

    async def get(self, principal, conversation_id):
        principal.require("conversations:read")
        async with self.session_factory() as session:
            repository = ConversationRepository(session)
            row = await repository.owned(conversation_id, principal.id)
            messages = await repository.messages(row.id)
            return ConversationDetail(**ConversationView.model_validate(row).model_dump(),
                messages=[MessageView.model_validate(message) for message in messages])

    async def patch(self, principal, conversation_id, body):
        principal.require("conversations:write")
        async with self.session_factory() as session, session.begin():
            row = await ConversationRepository(session).owned(conversation_id, principal.id, lock=True)
            row.title, row.updated_at = body.title, utcnow()
            await session.flush()
            return ConversationView.model_validate(row)

    async def add_message(self, principal, conversation_id, body):
        principal.require("conversations:write")
        async with self.session_factory() as session, session.begin():
            repository = ConversationRepository(session)
            row = await repository.owned(conversation_id, principal.id, lock=True)
            message = await repository.append_user_message(row, body.content, utcnow())
            return MessageView.model_validate(message)
