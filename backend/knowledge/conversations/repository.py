from sqlalchemy import select
from .entities import Conversation, Message
from ..core.errors import AppError


class ConversationRepository:
    def __init__(self, session):
        self.session = session

    async def owned(self, conversation_id, owner_id, *, lock=False):
        statement = select(Conversation).where(Conversation.id == conversation_id,
                                              Conversation.owner_id == owner_id)
        if lock:
            statement = statement.with_for_update()
        row = await self.session.scalar(statement)
        if row is None:
            raise AppError(404, "CONVERSATION_NOT_FOUND", "대화를 찾을 수 없습니다.")
        return row

    async def list(self, owner_id):
        return list(await self.session.scalars(select(Conversation).where(Conversation.owner_id == owner_id)
                                              .order_by(Conversation.updated_at.desc(), Conversation.id).limit(100)))

    async def messages(self, conversation_id):
        return list(await self.session.scalars(select(Message).where(Message.conversation_id == conversation_id)
                                              .order_by(Message.created_at, Message.id)))
