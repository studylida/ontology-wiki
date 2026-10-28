from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base
from ..core.ids import new_id, utcnow


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("conv"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300), default="새 대화")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (CheckConstraint("length(btrim(title)) > 0", name="ck_conversation_title"),)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("msg"))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_message_role"),
        CheckConstraint("length(btrim(content)) > 0", name="ck_message_content"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at", "id"),
    )
