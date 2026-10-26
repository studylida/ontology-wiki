from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from knowledge.core.database import Base
from knowledge.core.ids import new_id, utcnow


class ResearchItem(Base):
    __tablename__ = "research_items"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("paper"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    query: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    read_scope: Mapped[str] = mapped_column(String(32), default="metadata")
    relevance: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[list] = mapped_column(JSONB, default=list)
    usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    transferred_revision_id: Mapped[str | None] = mapped_column(ForeignKey("document_revisions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
