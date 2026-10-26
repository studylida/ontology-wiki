from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base
from ..core.ids import new_id, utcnow


class User(Base):
    __tablename__ = "knowledge_users"
    id: Mapped[str] = mapped_column(String(80), primary_key=True, default=lambda: new_id("usr"))
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(32), default="user")
    kind: Mapped[str] = mapped_column(String(16), default="user")
    permissions: Mapped[list] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_wiki: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


ROLE_PERMISSIONS = {
    "user": {"ontology:read", "rag:retrieve", "rag:answer", "documents:write", "research:use", "personal_wiki:write"},
    "reviewer": {"ontology:read", "rag:retrieve", "rag:answer", "documents:write", "documents:review", "jobs:manage", "research:use", "personal_wiki:write"},
    "admin": {"ontology:read", "rag:retrieve", "rag:answer", "documents:write", "documents:review", "jobs:manage", "users:manage", "research:use", "personal_wiki:write"},
}
