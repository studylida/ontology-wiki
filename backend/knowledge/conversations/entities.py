from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String(64), primary_key=True, default=lambda: new_id('conv'))
    owner_id = Column(String(64), ForeignKey('knowledge_users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(300), nullable=False, default='새 대화')
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class Message(Base):
    __tablename__ = 'messages'
    id = Column(String(64), primary_key=True, default=lambda: new_id('msg'))
    conversation_id = Column(String(64), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default='completed')
    run_id = Column(String(64), ForeignKey('answer_runs.id', use_alter=True))
    citations = Column(JSONB, nullable=False, default=list)
    source_revision_ids = Column(JSONB, nullable=False, default=list)
    warnings = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
