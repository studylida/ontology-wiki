import asyncio
import hashlib
import json
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from ..conversations.entities import Conversation, Message
from ..conversations.repository import ConversationRepository
from ..conversations.service import protect_message
from ..core.errors import AppError
from ..core.ids import new_id, utcnow
from ..rag.dto import AnswerRequest
from .dto import run_handle
from .entities import ACTIVE_STATUSES, AnswerRun
from .execution import AnswerExecutor
from .repository import AnswerRepository
from .runtime import RunRuntime


class AnswerService:
    def __init__(self, session_factory, identity, conversations, retrieval, generation_client, settings):
        self.session_factory, self.settings = session_factory, settings
        self.executor = AnswerExecutor(session_factory, identity, conversations, retrieval, generation_client, settings)
        self.runtimes: dict[str, RunRuntime] = {}
        self.stopping = False

    async def recover(self):
        # V1 explicitly runs one API process; no lease or distributed worker is implied.
        async with self.session_factory() as session, session.begin():
            return await AnswerRepository(session).interrupt_active()

    async def shutdown(self):
        self.stopping = True
        tasks = []
        for runtime in self.runtimes.values():
            if runtime.task and not runtime.task.done():
                runtime.cancel_kind = "interrupted"
                runtime.cancel_event.set()
                runtime.task.cancel()
                tasks.append(runtime.task)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def same_request(existing, request_hash):
        if existing.request_hash != request_hash:
            raise AppError(409, "IDEMPOTENCY_CONFLICT", "같은 요청 ID에 다른 내용이 전달됐습니다. 새 요청 ID를 사용하세요.")
        return run_handle(existing)

    async def create(self, principal, request: AnswerRequest):
        principal.require("rag:answer")
        if self.stopping:
            raise AppError(503, "SERVER_STOPPING", "서버가 종료 중입니다. 잠시 후 다시 시도하세요.", retryable=True)
        body = request.public()
        fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        async with self.session_factory() as session:
            existing = await AnswerRepository(session).idempotent(principal.id, request.client_request_id)
            if existing:
                return self.same_request(existing, fingerprint)
        config = {"model": getattr(self.executor.generation_client, "model", self.settings.generation_model),
                  "effort": self.settings.generation_effort, "providerMode": self.settings.provider_mode}
        try:
            async with self.session_factory() as session, session.begin():
                repo = AnswerRepository(session)
                if request.conversation_id:
                    conversation = await ConversationRepository(session).owned(request.conversation_id, principal.id, lock=True)
                    existing = await repo.idempotent(principal.id, request.client_request_id)
                    if existing:
                        return self.same_request(existing, fingerprint)
                    if await repo.active_for_conversation(conversation.id):
                        raise AppError(409, "CONVERSATION_BUSY", "이 대화의 답변이 진행 중입니다. 완료하거나 취소한 뒤 이어서 질문하세요.")
                else:
                    conversation = Conversation(id=new_id("conv"), owner_id=principal.id, title=request.message[:100],
                        auto_wiki=self.settings.auto_wiki_default and principal.kind == "user")
                    session.add(conversation)
                    await session.flush()
                if request.retry_of_run_id:
                    previous = await repo.owned(request.retry_of_run_id, principal.id)
                    if previous.status in ACTIVE_STATUSES:
                        raise AppError(409, "RETRY_NOT_READY", "진행 중인 답변은 별도 재시도할 수 없습니다.")
                    if previous.conversation_id != conversation.id:
                        raise AppError(422, "RETRY_CONVERSATION_MISMATCH", "재시도는 원래 대화에서 시작해야 합니다.")
                created_at, run_id = utcnow(), new_id("run")
                user_message = Message(id=new_id("msg"), conversation_id=conversation.id, role="user",
                    content=request.message, status="completed", created_at=created_at)
                assistant = Message(id=new_id("msg"), conversation_id=conversation.id, role="assistant",
                    content="", response_mode=request.response_mode, extended=request.extended,
                    run_id=run_id, status="queued", created_at=created_at + timedelta(microseconds=1))
                session.add_all([user_message, assistant])
                await session.flush()
                run = AnswerRun(id=run_id, owner_id=principal.id, conversation_id=conversation.id,
                    user_message_id=user_message.id, message_id=assistant.id, client_request_id=request.client_request_id,
                    request_hash=fingerprint, request=body, retry_of_run_id=request.retry_of_run_id,
                    status="queued", generation_config=config)
                session.add(run)
                conversation.updated_at = created_at
                conversation.next_settings = {key: body[key] for key in ("responseMode", "extended", "conceptIds",
                    "sourceRevisionIds", "documentContextIds", "sourceGroups", "aspect", "attachmentIds")}
                await session.flush()
                handle = run_handle(run)
        except IntegrityError:
            # Unique owner/request key resolves concurrent submissions atomically;
            # the losing transaction also rolls back its messages/conversation.
            async with self.session_factory() as session:
                existing = await AnswerRepository(session).idempotent(principal.id, request.client_request_id)
                if existing:
                    return self.same_request(existing, fingerprint)
            raise
        runtime = RunRuntime(run.id, assistant.id, conversation.id, user_message.id, principal,
                             generation_config=config)
        self.runtimes[run.id] = runtime
        actual_request = request.model_copy(update={"conversation_id": conversation.id})
        runtime.task = asyncio.create_task(self.executor.run(runtime, actual_request), name=f"answer:{run.id}")
        # Completed run events are durable; keep only a bounded recent in-memory cache.
        completed = [key for key, value in self.runtimes.items() if value.finished]
        for key in completed[:-128]:
            self.runtimes.pop(key, None)
        return handle

    async def get(self, principal, run_id):
        runtime = self.runtimes.get(run_id)
        if runtime and runtime.storage_error and not runtime.finished:
            await self.executor.finish(runtime, "interrupted", {"code": "PERSISTENCE_INTERRUPTED",
                "message": "답변 저장 중 연결이 중단되었습니다. 저장된 부분을 확인하고 명시적으로 다시 시도하세요.", "retryable": True})
        async with self.session_factory() as session:
            value = await AnswerRepository(session).detail(run_id, principal.id)
            value["message"] = await protect_message(session, principal, value["message"])
            value["warnings"] = list(dict.fromkeys((value["warnings"] or []) + value["message"].get("warnings", [])))
            return value

    async def cancel(self, principal, run_id):
        async with self.session_factory() as session, session.begin():
            row = await AnswerRepository(session).owned(run_id, principal.id, lock=True)
            if row.status in ACTIVE_STATUSES:
                row.status = "cancel_requested"
            status = row.status
        runtime = self.runtimes.get(run_id)
        if runtime and not runtime.finished:
            runtime.cancel_event.set()
            if runtime.task and not runtime.task.done():
                runtime.task.cancel()
                await asyncio.gather(runtime.task, return_exceptions=True)
            # Cancellation can win before the coroutine's first instruction.
            if not runtime.finished:
                await self.executor.finish(runtime, "cancelled")
            status = runtime.status
        return {"runId": run_id, "status": status}

    async def record_client_metrics(self, principal, run_id, first_visible_text_ms):
        async with self.session_factory() as session, session.begin():
            row = await AnswerRepository(session).owned(run_id, principal.id, lock=True)
            metrics = dict(row.metrics or {})
            if "clientFirstVisibleTextMs" not in metrics:
                metrics.update(clientFirstVisibleTextMs=first_visible_text_ms, clientTimingSource="browser_untrusted")
                row.metrics = metrics
            runtime = self.runtimes.get(run_id)
            if runtime:
                runtime.metrics.setdefault("clientFirstVisibleTextMs", metrics["clientFirstVisibleTextMs"])
                runtime.metrics["clientTimingSource"] = "browser_untrusted"
            return {"runId": run_id, "metrics": metrics}

    @staticmethod
    def historical_event(event, protected):
        stale = set(protected.get("staleSourceRevisionIds", []))
        if not stale:
            return event
        if event["type"] == "source_view.add" and event["data"].get("sourceRevisionId") in stale:
            return None
        if event["type"] == "citation.add" and event["data"].get("sourceRevisionId") in stale:
            return {**event, "data": {**event["data"], "historicalMetadata": True}}
        if event["type"] in ("retrieval.status", "run.completed", "run.failed", "run.cancelled"):
            return {**event, "data": {**event["data"], "warnings": list(dict.fromkeys(
                event["data"].get("warnings", []) + protected.get("warnings", [])))}}
        return event

    async def check_stream(self, principal, run_id, after):
        detail = await self.get(principal, run_id)
        if detail["message"]["status"] == "restricted":
            raise AppError(403, "SOURCE_ACCESS_CHANGED", "이 응답의 근거 자료에 현재 접근할 수 없습니다.")
        runtime = self.runtimes.get(run_id)
        highest = runtime.seq if runtime else detail["lastSeq"]
        if after > highest or (not runtime and detail["status"] == "interrupted" and after >= highest):
            raise AppError(409, "REPLAY_CURSOR_AHEAD", "저장된 이벤트 범위보다 앞선 위치입니다. 실행 상세를 다시 불러오세요.",
                           details={"lastSeq": detail["lastSeq"]}, retryable=True)
        return detail

    async def event_stream(self, principal, run_id, after, disconnected):
        cursor = after
        runtime = self.runtimes.get(run_id)
        if not runtime:
            detail = await self.get(principal, run_id)
            protected = detail["message"]
            if protected["status"] == "restricted":
                return
            async with self.session_factory() as session:
                events = await AnswerRepository(session).events(run_id, cursor)
            for event in events:
                if await disconnected():
                    return
                event = self.historical_event(event, protected)
                if event is not None:
                    yield event
            return
        while True:
            if await disconnected():
                return
            try:
                await self.executor.verify_access(runtime)
            except AppError:
                # Do not replay withdrawn text or fabricate a durable terminal event.
                # The authenticated detail endpoint exposes its restricted state.
                return
            async with self.session_factory() as session:
                protected = await protect_message(session, runtime.principal, {"citations": runtime.citations,
                    "relations": runtime.relations, "sourceViews": runtime.source_views,
                    "warnings": runtime.warnings, "status": runtime.status})
            if protected["status"] == "restricted":
                return
            ready = [event for event in runtime.events if event["seq"] > cursor]
            for event in ready:
                cursor = event["seq"]
                event = self.historical_event(event, protected)
                if event is not None:
                    yield event
            if runtime.finished or runtime.storage_error:
                return
            async with runtime.changed:
                if any(event["seq"] > cursor for event in runtime.events):
                    continue
                try:
                    await asyncio.wait_for(runtime.changed.wait(), timeout=15)
                except TimeoutError:
                    yield None  # SSE comment heartbeat, never a fake answer token.
