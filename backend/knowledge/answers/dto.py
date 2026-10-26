from ..conversations.dto import message_dto
from pydantic import Field
from ..core.dto import DTO


class ClientMetricsRequest(DTO):
    first_visible_text_ms: float = Field(ge=0, le=86400000, allow_inf_nan=False)


def run_handle(row):
    return {"runId": row.id, "conversationId": row.conversation_id,
            "messageId": row.message_id, "status": row.status,
            "eventsUrl": f"/api/v1/answer-runs/{row.id}/events"}


def run_dto(row, message):
    return {**run_handle(row), "lastSeq": row.last_seq, "message": message_dto(message),
            "request": row.request, "error": row.error, "usage": row.usage,
            "warnings": row.warnings, "metrics": row.metrics,
            "generationConfig": row.generation_config,
            "retrievalRunId": row.retrieval_run_id,
            "retryOfRunId": row.retry_of_run_id, "createdAt": row.created_at.isoformat(),
            "startedAt": row.started_at.isoformat() if row.started_at else None,
            "finishedAt": row.finished_at.isoformat() if row.finished_at else None}
