from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base
from ..core.ids import new_id, utcnow


ACTIVE_STATUSES = ("queued", "running", "cancel_requested")
TERMINAL_STATUSES = ("completed", "failed", "cancelled", "interrupted")


class AnswerRun(Base):
    __tablename__ = "answer_runs"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("run"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    user_message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"))
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"))
    client_request_id: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    request: Mapped[dict] = mapped_column(JSONB)
    retry_of_run_id: Mapped[str | None] = mapped_column(ForeignKey("answer_runs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    last_seq: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    generation_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    retrieval_run_id: Mapped[str | None] = mapped_column(ForeignKey("retrieval_runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint("owner_id", "client_request_id", name="uq_answer_owner_request"),)


class AnswerEventBatch(Base):
    """One batched write, retaining original provider delta boundaries for replay."""
    __tablename__ = "answer_event_batches"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("evt"))
    run_id: Mapped[str] = mapped_column(ForeignKey("answer_runs.id"), index=True)
    first_seq: Mapped[int] = mapped_column(Integer)
    last_seq: Mapped[int] = mapped_column(Integer)
    events: Mapped[list] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("run_id", "first_seq", name="uq_answer_event_start"),
                     Index("ix_answer_event_replay", "run_id", "last_seq"))
