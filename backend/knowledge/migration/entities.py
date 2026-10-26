"""Lossless legacy retention, separate from current reviewed knowledge."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class LegacyArchive(Base):
    __tablename__ = "legacy_archive"
    __table_args__ = (UniqueConstraint("source_system", "source_table", "source_id", "record_hash"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("archive"))
    source_system: Mapped[str] = mapped_column(String(160))
    source_table: Mapped[str] = mapped_column(String(160))
    source_id: Mapped[str] = mapped_column(Text)
    record_hash: Mapped[str] = mapped_column(String(64))
    first_import_id: Mapped[str | None] = mapped_column(ForeignKey("legacy_imports.id"), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    access_classification: Mapped[str] = mapped_column(String(80), default="restricted_legacy_archive")
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LegacyImport(Base):
    """A content-addressed original export, distinct from parsed row preservation."""
    __tablename__ = "legacy_imports"
    __table_args__ = (UniqueConstraint("source_system", "export_sha256"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("legacy_import"))
    source_system: Mapped[str] = mapped_column(String(160), index=True)
    export_sha256: Mapped[str] = mapped_column(String(64))
    raw_path: Mapped[str] = mapped_column(Text)
    counts: Mapped[dict] = mapped_column(JSONB)
    record_count: Mapped[int] = mapped_column(Integer)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LegacyMapping(Base):
    __tablename__ = "legacy_mappings"
    __table_args__ = (UniqueConstraint("source_system", "source_table", "source_id"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("mapping"))
    source_system: Mapped[str] = mapped_column(String(160))
    source_table: Mapped[str] = mapped_column(String(160))
    source_id: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    disposition: Mapped[str] = mapped_column(String(80), default="preserved_pending_mapping")
