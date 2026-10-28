from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class AnswerRun(Base):
    __tablename__ = 'answer_runs'
    __table_args__ = (UniqueConstraint('owner_id', 'request_id', name='uq_answer_owner_request'),)
    id = Column(String(64), primary_key=True, default=lambda: new_id('run'))
    owner_id = Column(String(64), ForeignKey('knowledge_users.id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(String(64), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    user_message_id = Column(String(64), ForeignKey('messages.id'), nullable=False)
    message_id = Column(String(64), ForeignKey('messages.id'), nullable=False, unique=True)
    request_id = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    request_payload = Column(JSONB, nullable=False)
    status = Column(String(24), nullable=False, default='accepted')
    process_epoch = Column(String(64), nullable=False)
    durable_seq = Column(Integer, nullable=False, default=0)
    retrieval_run_id = Column(String(64), ForeignKey('retrieval_runs.id'))
    usage = Column(JSONB, nullable=False, default=dict)
    error = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class AnswerEventBatch(Base):
    __tablename__ = 'answer_event_batches'
    __table_args__ = (UniqueConstraint('run_id', 'first_seq', name='uq_answer_batch_first'),)
    id = Column(String(64), primary_key=True, default=lambda: new_id('evt'))
    run_id = Column(String(64), ForeignKey('answer_runs.id', ondelete='CASCADE'), nullable=False)
    first_seq = Column(Integer, nullable=False)
    last_seq = Column(Integer, nullable=False)
    events = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
