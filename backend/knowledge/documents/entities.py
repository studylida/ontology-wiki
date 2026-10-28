"""Shared source records. Raw revisions are immutable and activation is explicit."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from ..core.database import Base
from ..core.ids import new_id, utcnow


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('doc'))
    owner_id: Mapped[str] = mapped_column(ForeignKey('knowledge_users.id'))
    title: Mapped[str] = mapped_column(String(500))
    origin_key: Mapped[str] = mapped_column(String(64), unique=True)
    current_revision_id: Mapped[str | None] = mapped_column(String(80))
    active_revision_id: Mapped[str | None] = mapped_column(String(80))
    withdrawn: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        ForeignKeyConstraint(['id','current_revision_id'], ['document_revisions.document_id','document_revisions.id'], name='document_current_revision_fk', deferrable=True, initially='DEFERRED', use_alter=True),
        ForeignKeyConstraint(['id','active_revision_id'], ['document_revisions.document_id','document_revisions.id'], name='document_active_revision_fk', deferrable=True, initially='DEFERRED', use_alter=True),
    )


class DocumentRevision(Base):
    __tablename__ = 'document_revisions'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('rev'))
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'))
    revision: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(80))
    raw_path: Mapped[str] = mapped_column(Text)
    raw_sha256: Mapped[str] = mapped_column(String(64))
    input_hash: Mapped[str] = mapped_column(String(64))
    content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column('metadata', JSONB, default=dict)
    processing_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    read_scope: Mapped[str] = mapped_column(String(16), default='unknown')
    limitations: Mapped[list] = mapped_column(JSONB, default=list)
    index_status: Mapped[str] = mapped_column(String(24), default='queued')
    embedding_profile: Mapped[str | None] = mapped_column(String(240))
    index_snapshot_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint('document_id','revision'), UniqueConstraint('document_id','input_hash'), UniqueConstraint('document_id','id'))


class Passage(Base):
    __tablename__ = 'passages'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('psg'))
    source_revision_id: Mapped[str] = mapped_column(ForeignKey('document_revisions.id'))
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    locator: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[int] = mapped_column(Integer)
    end_offset: Mapped[int] = mapped_column(Integer)
    embedding_text: Mapped[str] = mapped_column(Text)
    input_hash: Mapped[str] = mapped_column(String(64))
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(Text)
    source_map: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (UniqueConstraint('source_revision_id','ordinal'),)


class EmbeddingRecord(Base):
    __tablename__ = 'embedding_records'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('vec'))
    scope: Mapped[str] = mapped_column(String(16), default='shared')
    profile_id: Mapped[str] = mapped_column(String(240))
    input_hash: Mapped[str] = mapped_column(String(64))
    vector: Mapped[list] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint('scope','profile_id','input_hash'),)


class PassageEmbedding(Base):
    __tablename__ = 'passage_embeddings'
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id('pe'))
    passage_id: Mapped[str] = mapped_column(ForeignKey('passages.id'))
    profile_id: Mapped[str] = mapped_column(String(240))
    embedding_id: Mapped[str] = mapped_column(ForeignKey('embedding_records.id'))
    __table_args__ = (UniqueConstraint('passage_id','profile_id'),)
