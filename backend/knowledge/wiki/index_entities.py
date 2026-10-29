"""Derived wiki passages/jobs reuse the common embedding cache, not source ownership."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base
from ..core.ids import new_id, utcnow


class WikiIndexJob(Base):
    __tablename__ = 'wiki_index_jobs'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('wjob'))
    page_id: Mapped[str] = mapped_column(ForeignKey('wiki_pages.id'))
    revision_id: Mapped[str] = mapped_column(String(80), unique=True)
    status: Mapped[str] = mapped_column(String(24), default='pending')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    profile_id: Mapped[str | None] = mapped_column(String(240))
    progress: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[dict | None] = mapped_column(JSONB)
    usage: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (ForeignKeyConstraint(['page_id','revision_id'], ['wiki_revisions.page_id','wiki_revisions.id']),)


class WikiPassage(Base):
    __tablename__ = 'wiki_passages'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('wpsg'))
    revision_id: Mapped[str] = mapped_column(ForeignKey('wiki_revisions.id'))
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    locator: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[int] = mapped_column(Integer)
    end_offset: Mapped[int] = mapped_column(Integer)
    embedding_text: Mapped[str] = mapped_column(Text)
    input_hash: Mapped[str] = mapped_column(String(64))
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint('revision_id','ordinal'),)


class WikiPassageEmbedding(Base):
    __tablename__ = 'wiki_passage_embeddings'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('wpe'))
    passage_id: Mapped[str] = mapped_column(ForeignKey('wiki_passages.id'))
    profile_id: Mapped[str] = mapped_column(String(240))
    embedding_id: Mapped[str] = mapped_column(ForeignKey('embedding_records.id'))
    __table_args__ = (UniqueConstraint('passage_id','profile_id'),)
