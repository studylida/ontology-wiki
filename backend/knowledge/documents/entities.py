"""Immutable source bodies and passages; mutable review/index pointers are explicit."""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("doc"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(32), default="private")
    current_revision_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    active_revision_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    withdrawn: Mapped[bool] = mapped_column(Boolean, default=False)
    origin_key: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentRevision(Base):
    __tablename__ = "document_revisions"
    __table_args__ = (UniqueConstraint("document_id", "revision"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("rev"))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_path: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(String(100), default="text/markdown")
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_version: Mapped[int] = mapped_column(Integer, default=1)
    metadata_hash: Mapped[str] = mapped_column(String(64))
    review_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    index_status: Mapped[str] = mapped_column(String(32), default="pending")
    index_snapshot_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    read_scope: Mapped[str] = mapped_column(String(32), default="full")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Passage(Base):
    __tablename__ = "passages"
    __table_args__ = (UniqueConstraint("source_revision_id", "ordinal"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("psg"))
    source_revision_id: Mapped[str] = mapped_column(ForeignKey("document_revisions.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    locator: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_text: Mapped[str] = mapped_column(Text)
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmbeddingRecord(Base):
    __tablename__ = "embedding_records"
    __table_args__ = (UniqueConstraint("scope", "profile_id", "input_hash"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("vec"))
    scope: Mapped[str] = mapped_column(String(100))
    profile_id: Mapped[str] = mapped_column(String(160), index=True)
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    vector: Mapped[list[float]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PassageEmbedding(Base):
    __tablename__ = "passage_embeddings"
    __table_args__ = (UniqueConstraint("passage_id", "profile_id"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("pe"))
    passage_id: Mapped[str] = mapped_column(ForeignKey("passages.id"), index=True)
    profile_id: Mapped[str] = mapped_column(String(160))
    embedding_id: Mapped[str] = mapped_column(ForeignKey("embedding_records.id"))


class ReviewDecision(Base):
    __tablename__ = "document_review_decisions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("review"))
    source_revision_id: Mapped[str] = mapped_column(ForeignKey("document_revisions.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"))
    decision: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MetadataHistory(Base):
    __tablename__ = "document_metadata_history"
    __table_args__ = (UniqueConstraint("source_revision_id", "version"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("meta"))
    source_revision_id: Mapped[str] = mapped_column(ForeignKey("document_revisions.id"))
    version: Mapped[int] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column(JSONB)
    changed_by: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentAttachment(Base):
    __tablename__ = "document_attachments"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("att"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    source_revision_id: Mapped[str] = mapped_column(ForeignKey("document_revisions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
