from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from ...core.database import Base
from ...core.ids import new_id, utcnow


class DocumentWikiJob(Base):
    __tablename__ = 'wiki_document_jobs'
    id = Column(String(80), primary_key=True, default=lambda: new_id('wdj'))
    source_revision_id = Column(String(80), ForeignKey('document_revisions.id'), nullable=False, unique=True)
    status = Column(String(16), nullable=False, default='pending')
    result = Column(JSONB, nullable=False, default=dict)
    error = Column(JSONB)
    usage = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    started_at = Column(DateTime(timezone=True))
