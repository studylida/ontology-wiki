"""Current pages and immutable content revisions. Titles are intentionally not unique."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class WikiPage(Base):
    __tablename__ = 'wiki_pages'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    creator_id: Mapped[str] = mapped_column(ForeignKey('knowledge_users.id'))
    current_revision_id: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    protection_updated_by: Mapped[str | None] = mapped_column(ForeignKey('knowledge_users.id'))
    protection_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (ForeignKeyConstraint(['id', 'current_revision_id'],
        ['wiki_revisions.page_id', 'wiki_revisions.id'], name='wiki_current_revision_fk',
        deferrable=True, initially='DEFERRED', use_alter=True),)


class WikiRevision(Base):
    __tablename__ = 'wiki_revisions'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    page_id: Mapped[str] = mapped_column(ForeignKey('wiki_pages.id'))
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    markdown: Mapped[str] = mapped_column(Text)
    source_note: Mapped[str] = mapped_column(Text, default='')
    change_summary: Mapped[str] = mapped_column(String(500), default='')
    editor_id: Mapped[str] = mapped_column(ForeignKey('knowledge_users.id'))
    restored_from_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint('page_id', 'number'), UniqueConstraint('page_id', 'id'),
        ForeignKeyConstraint(['page_id', 'restored_from_id'], ['wiki_revisions.page_id', 'wiki_revisions.id']))


class WikiMutation(Base):
    __tablename__ = 'wiki_mutations'
    actor_id: Mapped[str] = mapped_column(ForeignKey('knowledge_users.id'), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    page_id: Mapped[str] = mapped_column(ForeignKey('wiki_pages.id'))
    result: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
