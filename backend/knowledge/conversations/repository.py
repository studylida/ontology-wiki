from sqlalchemy import select

from ..core.errors import AppError
from .entities import Conversation, Message


class ConversationRepository:
    def __init__(self, session):
        self.session = session

    async def owned(self, conversation_id: str, owner_id: str, *, lock=False):
        statement = select(Conversation).where(
            Conversation.id == conversation_id, Conversation.owner_id == owner_id)
        if lock:
            statement = statement.with_for_update()
        conversation = await self.session.scalar(statement)
        if conversation is None:
            # Do not disclose whether another user's conversation exists.
            raise AppError(404, "CONVERSATION_NOT_FOUND", "대화가 없거나 접근할 수 없습니다.")
        return conversation

    async def list(self, owner_id: str):
        return list((await self.session.scalars(
            select(Conversation).where(Conversation.owner_id == owner_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id).limit(100)
        )).all())

    async def create(self, owner_id: str, title: str):
        conversation = Conversation(owner_id=owner_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def messages(self, conversation_id: str):
        # Caller must first obtain the conversation through owned().
        return list((await self.session.scalars(
            select(Message).where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at, Message.id)
        )).all())

    async def append_user_message(self, conversation, content: str, timestamp):
        message = Message(conversation_id=conversation.id, role="user", content=content,
                          created_at=timestamp)
        conversation.updated_at = timestamp
        self.session.add(message)
        await self.session.flush()
        return message
