from datetime import datetime, timezone
from uuid import uuid4


def new_id(prefix: str = "") -> str:
    return f"{prefix}_{uuid4().hex}" if prefix else uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
