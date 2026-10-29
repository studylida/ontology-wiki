from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from ...core.database import Base
from ...core.ids import new_id, utcnow


class WikiProposal(Base):
    __tablename__ = 'wiki_proposals'
    id = Column(String(80), primary_key=True, default=lambda: new_id('wpr'))
    owner_id = Column(String(80), ForeignKey('knowledge_users.id'), nullable=False)
    request_id = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    page_id = Column(String(80), ForeignKey('wiki_pages.id'))
    base_revision_id = Column(String(80))
    base_version = Column(Integer)
    mode = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False, default='pending')
    input = Column(JSONB, nullable=False)
    base_snapshot = Column(JSONB, nullable=False, default=dict)
    result = Column(JSONB, nullable=False, default=dict)
    error = Column(JSONB)
    usage = Column(JSONB, nullable=False, default=dict)
    applied_result = Column(JSONB)
    applied_hash = Column(String(64))
    applied_by = Column(String(80), ForeignKey('knowledge_users.id'))
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    __table_args__ = (UniqueConstraint('owner_id','request_id'),
        ForeignKeyConstraint(['page_id','base_revision_id'], ['wiki_revisions.page_id','wiki_revisions.id']))
