from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
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
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="ck_user_role"),
        CheckConstraint("kind IN ('user', 'service')", name="ck_user_kind"),
        CheckConstraint("token_version >= 1", name="ck_user_token_version"),
    )


# Document upload permissions are not role-separated. Stage 2 adds the shared
# document capability. Neither role can access another employee's conversation.
ROLE_PERMISSIONS = {
    "user": {"conversations:read", "conversations:write"},
    "admin": {"conversations:read", "conversations:write", "users:manage"},
}
