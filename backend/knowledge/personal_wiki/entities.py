from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class PersonalWikiPage(Base):
    __tablename__ = "personal_wiki_pages"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("pw"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(200))
    topic_key: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text)
    conditions: Mapped[list] = mapped_column(JSONB, default=list)
    limitations: Mapped[list] = mapped_column(JSONB, default=list)
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    source_revision_ids: Mapped[list] = mapped_column(JSONB, default=list)
    origin_messages: Mapped[list] = mapped_column(JSONB, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    __table_args__ = (Index("uq_personal_wiki_active_topic", "owner_id", "topic_key", unique=True,
                           postgresql_where=deleted_at.is_(None)),)


class PersonalWikiRevision(Base):
    __tablename__ = "personal_wiki_revisions"
    __table_args__ = (UniqueConstraint("page_id", "version"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("pwr"))
    page_id: Mapped[str] = mapped_column(ForeignKey("personal_wiki_pages.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restored_from_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operation: Mapped[str] = mapped_column(String(32))
    job_id: Mapped[str | None] = mapped_column(ForeignKey("knowledge_jobs.id"), nullable=True)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PersonalWikiMessageState(Base):
    """Cross-policy idempotency and exclusion ledger, retained after page deletion."""
    __tablename__ = "personal_wiki_message_states"
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), primary_key=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    page_id: Mapped[str | None] = mapped_column(ForeignKey("personal_wiki_pages.id"), nullable=True)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    is_suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    suppression_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    suppressed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_job_id: Mapped[str | None] = mapped_column(ForeignKey("knowledge_jobs.id"), nullable=True)
    last_policy: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
