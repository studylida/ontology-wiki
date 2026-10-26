from pydantic import Field
from ..core.dto import DTO


class ConversationCreate(DTO):
    title: str | None = Field(None, max_length=300)


class ConversationPatch(DTO):
    title: str | None = Field(None, min_length=1, max_length=300)
    auto_wiki: bool | None = None


def conversation_dto(row):
    return {"id": row.id, "title": row.title, "updatedAt": row.updated_at.isoformat(),
            "autoWiki": row.auto_wiki, "nextSettings": row.next_settings}


def message_dto(row):
    return {"id": row.id, "role": row.role, "content": row.content,
            "responseMode": row.response_mode, "extended": row.extended, "runId": row.run_id,
            "status": row.status, "createdAt": row.created_at.isoformat(),
            "citations": row.citations or [], "relations": row.relations or [],
            "sourceViews": row.source_views or [], "warnings": row.warnings or [], "usage": row.usage}
