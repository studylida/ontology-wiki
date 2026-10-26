from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base
from ..core.ids import new_id, utcnow


class RetrievalRun(Base):
    __tablename__ = "retrieval_runs"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("ret"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("knowledge_users.id"), index=True)
    request: Mapped[dict] = mapped_column(JSONB)
    snapshot_id: Mapped[str] = mapped_column(String(80))
    revision_ids: Mapped[list] = mapped_column(JSONB)
    result: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
