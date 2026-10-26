from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class Concept(Base):
    __tablename__ = "ontology_concepts"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("concept"))
    name: Mapped[str] = mapped_column(Text, index=True)
    names: Mapped[dict] = mapped_column(JSONB, default=dict)
    aliases: Mapped[list] = mapped_column(JSONB, default=list)
    type: Mapped[str] = mapped_column(String(80), default="concept")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    origin: Mapped[str] = mapped_column(String(80), default="machine_extracted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConceptRelation(Base):
    __tablename__ = "ontology_relations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("rel"))
    from_concept_id: Mapped[str] = mapped_column(ForeignKey("ontology_concepts.id"), index=True)
    to_concept_id: Mapped[str] = mapped_column(ForeignKey("ontology_concepts.id"), index=True)
    type: Mapped[str] = mapped_column(String(48))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(48), default="machine_extracted")
    origin: Mapped[str] = mapped_column(String(80), default="source_extraction")
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)
    extractor: Mapped[dict] = mapped_column(JSONB, default=dict)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConceptSourceView(Base):
    __tablename__ = "concept_source_views"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("view"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("ontology_concepts.id"), index=True)
    source_revision_id: Mapped[str] = mapped_column(ForeignKey("document_revisions.id"), index=True)
    aspect: Mapped[str] = mapped_column(String(80), default="definition")
    summary: Mapped[str] = mapped_column(Text)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    attribution: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_version: Mapped[int] = mapped_column(Integer)
    metadata_hash: Mapped[str] = mapped_column(String(64))
    input_hash: Mapped[str] = mapped_column(String(64))
    evidence_refs: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(48), default="active", index=True)
    extraction_status: Mapped[str] = mapped_column(String(48), default="machine_extracted")
    extractor: Mapped[dict] = mapped_column(JSONB, default=dict)
    supersedes_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
