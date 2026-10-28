"""Only document processing jobs are enabled in Stage 2."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base
from ..core.ids import new_id, utcnow


class Job(Base):
    __tablename__ = 'processing_jobs'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('job'))
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'))
    source_revision_id: Mapped[str] = mapped_column(String(80), unique=True)
    kind: Mapped[str] = mapped_column(String(32), default='document_index')
    status: Mapped[str] = mapped_column(String(24), default='pending')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[dict | None] = mapped_column(JSONB)
    usage: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (ForeignKeyConstraint(['document_id','source_revision_id'], ['document_revisions.document_id','document_revisions.id']),)
