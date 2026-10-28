from knowledge.core.errors import AppError
from knowledge.core.ids import utcnow
from .dto import ConversationDetail, ConversationList, ConversationView, MessageView
from .protection import visible_message
from .repository import ConversationRepository


class ConversationService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def list(self, principal):
        principal.require('conversations:read')
        async with self.session_factory() as session:
            rows = await ConversationRepository(session).list(principal.id)
            return ConversationList(items=[ConversationView.model_validate(row) for row in rows])

    async def create(self, principal, body):
        principal.require('conversations:write')
        async with self.session_factory() as session, session.begin():
            row = await ConversationRepository(session).create(principal.id, body.title)
            return ConversationView.model_validate(row)

    async def get(self, principal, conversation_id):
        principal.require('conversations:read')
        async with self.session_factory() as session:
            repository = ConversationRepository(session)
            row = await repository.owned(conversation_id, principal.id)
            messages = await repository.messages(row.id)
            views = [await visible_message(session, principal, message) for message in messages]
            return ConversationDetail(**ConversationView.model_validate(row).model_dump(), messages=views)

    async def patch(self, principal, conversation_id, body):
        principal.require('conversations:write')
        async with self.session_factory() as session, session.begin():
            row = await ConversationRepository(session).owned(conversation_id, principal.id, lock=True)
            row.title, row.updated_at = body.title, utcnow()
            await session.flush()
            return ConversationView.model_validate(row)

    async def add_message(self, principal, conversation_id, body):
        from knowledge.answers.repository import AnswerRepository
        principal.require('conversations:write')
        async with self.session_factory() as session, session.begin():
            repository = ConversationRepository(session)
            row = await repository.owned(conversation_id, principal.id, lock=True)
            if await AnswerRepository(session).active(row.id) is not None:
                raise AppError(409, 'conversation_busy', '답변이 진행 중입니다. 완료하거나 취소한 뒤 메시지를 추가해 주세요.')
            message = await repository.append_user_message(row, body.content, utcnow())
            return MessageView.model_validate(message)
