from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class RetrievalRun(Base):
    __tablename__ = 'retrieval_runs'
    id = Column(String(64), primary_key=True, default=lambda: new_id('ret'))
    owner_id = Column(String(64), ForeignKey('knowledge_users.id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(String(64), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    query_text = Column(Text, nullable=False)
    result = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
