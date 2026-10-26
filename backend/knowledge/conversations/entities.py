from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base
from ..core.ids import new_id, utcnow


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("conv"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), index=True)
    title: Mapped[str] = mapped_column(String(300), default="새 대화")
    auto_wiki: Mapped[bool] = mapped_column(Boolean, default=True)
    next_settings: Mapped[dict] = mapped_column(JSONB, default=lambda: {"responseMode": "wiki", "extended": False})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("msg"))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text, default="")
    response_mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    extended: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    relations: Mapped[list] = mapped_column(JSONB, default=list)
    source_views: Mapped[list] = mapped_column(JSONB, default=list)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)
    usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("ix_messages_conversation_order", "conversation_id", "created_at", "id"),)
