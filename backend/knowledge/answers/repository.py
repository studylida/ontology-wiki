from sqlalchemy import select

from ..conversations.entities import Message
from ..core.errors import AppError
from ..core.ids import utcnow
from ..documents.repository import DocumentRepository
from .dto import run_dto
from .entities import ACTIVE_STATUSES, TERMINAL_STATUSES, AnswerEventBatch, AnswerRun


class AnswerRepository:
    def __init__(self, session):
        self.session = session

    async def owned(self, run_id, owner_id, *, lock=False):
        stmt = select(AnswerRun).where(AnswerRun.id == run_id, AnswerRun.owner_id == owner_id)
        if lock:
            stmt = stmt.with_for_update()
        row = await self.session.scalar(stmt)
        if row is None:
            raise AppError(404, "RUN_NOT_FOUND", "답변 실행을 찾을 수 없습니다.")
        return row

    async def idempotent(self, owner_id, client_request_id):
        return await self.session.scalar(select(AnswerRun).where(
            AnswerRun.owner_id == owner_id, AnswerRun.client_request_id == client_request_id))

    async def active_for_conversation(self, conversation_id):
        return await self.session.scalar(select(AnswerRun.id).where(
            AnswerRun.conversation_id == conversation_id, AnswerRun.status.in_(ACTIVE_STATUSES)).limit(1))

    async def detail(self, run_id, owner_id):
        row = await self.owned(run_id, owner_id)
        value = run_dto(row, await self.session.get(Message, row.message_id))
        if row.retrieval_run_id:
            from ..rag.entities import RetrievalRun
            retrieval = await self.session.get(RetrievalRun, row.retrieval_run_id)
            if retrieval and retrieval.owner_id == owner_id:
                value["retrievalSummary"] = {key: retrieval.result.get(key) for key in (
                    "groupCoverage", "indexSnapshotId", "stopReason", "requirementCoverage", "semanticSufficiency", "exploration")}
        return value

    async def events(self, run_id, after):
        batches = (await self.session.scalars(select(AnswerEventBatch).where(
            AnswerEventBatch.run_id == run_id, AnswerEventBatch.last_seq > after
        ).order_by(AnswerEventBatch.first_seq))).all()
        return [event for batch in batches for event in batch.events if event["seq"] > after]

    def append_batch(self, run_id, events):
        if events:
            self.session.add(AnswerEventBatch(run_id=run_id, first_seq=events[0]["seq"],
                                             last_seq=events[-1]["seq"], events=list(events)))

    async def persist(self, runtime, *, terminal=None, error=None, validate_sources=True):
        """Caller owns a short transaction. Final events become observable after commit."""
        row = await self.owned(runtime.run_id, runtime.principal.id, lock=True)
        if row.status in TERMINAL_STATUSES:
            return None
        if row.status == "cancel_requested" and terminal != "interrupted":
            if terminal is None:
                runtime.cancel_event.set()
                raise AppError(409, "RUN_CANCELLED", "답변이 취소되었습니다.")
            terminal, error = "cancelled", None
        if validate_sources and not await DocumentRepository(self.session).ensure_readable(
                runtime.principal, runtime.revision_ids(), lock=terminal is not None):
            raise AppError(403, "SOURCE_ACCESS_CHANGED", "사용된 자료의 접근 권한이 변경되었습니다.")
        message = await self.session.get(Message, row.message_id)
        message.content = runtime.content
        message.citations, message.relations = list(runtime.citations), list(runtime.relations)
        message.source_views, message.warnings = list(runtime.source_views), list(runtime.warnings)
        message.usage = runtime.usage
        row.usage, row.metrics = runtime.usage, {**(row.metrics or {}), **runtime.metrics}
        row.warnings, row.generation_config = list(runtime.warnings), dict(runtime.generation_config)
        row.retrieval_run_id = runtime.retrieval_run_id
        terminal_event = None
        events = list(runtime.pending)
        if terminal:
            row.status = message.status = terminal
            row.finished_at, row.error = utcnow(), error
            kind = {"completed": "run.completed", "cancelled": "run.cancelled"}.get(terminal, "run.failed")
            terminal_event = runtime.make_event(kind, {"status": terminal, "messageId": row.message_id,
                "usage": runtime.usage, "warnings": list(runtime.warnings), "error": error})
            events.append(terminal_event)
        else:
            row.status = message.status = "running"
            row.started_at = row.started_at or utcnow()
        self.append_batch(row.id, events)
        row.last_seq = events[-1]["seq"] if events else row.last_seq
        await self.session.flush()
        return terminal_event

    async def interrupt_active(self):
        rows = (await self.session.scalars(select(AnswerRun).where(
            AnswerRun.status.in_(ACTIVE_STATUSES)).with_for_update())).all()
        error = {"code": "PROCESS_INTERRUPTED", "message": "서버가 중단되어 답변이 완료되지 않았습니다. 저장된 부분을 확인하고 명시적으로 다시 시도하세요.", "retryable": True}
        for row in rows:
            row.status, row.error, row.finished_at = "interrupted", error, utcnow()
            message = await self.session.get(Message, row.message_id)
            message.status = "interrupted"
            row.last_seq += 1
            event = {"type": "run.failed", "runId": row.id, "seq": row.last_seq,
                     "at": utcnow().isoformat(), "data": {"status": "interrupted", "messageId": row.message_id,
                         "usage": row.usage, "warnings": row.warnings, "error": error}}
            self.append_batch(row.id, [event])
        return len(rows)
