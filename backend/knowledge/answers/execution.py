import asyncio
import logging
from time import monotonic

from ..core.errors import AppError
from ..core.usage import summarize_usage, unknown_usage
from ..documents.repository import DocumentRepository
from ..rag.context import citation
from .prompt import build_messages
from .repository import AnswerRepository


class AnswerExecutor:
    def __init__(self, session_factory, identity, conversations, retrieval, generation_client, settings):
        self.session_factory, self.identity = session_factory, identity
        self.conversations, self.retrieval = conversations, retrieval
        self.generation_client, self.settings = generation_client, settings

    async def verify_access(self, runtime):
        runtime.principal = await self.identity.refresh_principal(runtime.principal)
        runtime.principal.require("rag:answer")
        async with self.session_factory() as session:
            if not await DocumentRepository(session).ensure_readable(runtime.principal, runtime.revision_ids()):
                raise AppError(403, "SOURCE_ACCESS_CHANGED", "사용된 자료의 접근 권한이 변경되었습니다.")

    async def flush(self, runtime, *, force=False):
        if not runtime.pending:
            return
        if not force and runtime.pending_characters < self.settings.stream_flush_characters and (
                monotonic() - runtime.last_flush < self.settings.stream_flush_seconds):
            return
        await self.verify_access(runtime)
        async with self.session_factory() as session, session.begin():
            await AnswerRepository(session).persist(runtime)
        runtime.flushed()

    async def provider_deltas(self, runtime, messages):
        iterator = self.generation_client.stream(messages, effort=self.settings.generation_effort,
                                                 cancel_event=runtime.cancel_event).__aiter__()
        pending = None
        try:
            while True:
                pending = pending or asyncio.create_task(anext(iterator))
                done, _ = await asyncio.wait({pending}, timeout=self.settings.stream_flush_seconds)
                if not done:
                    await self.flush(runtime, force=True)
                    continue
                try:
                    delta = pending.result()
                except StopAsyncIteration:
                    return
                pending = None
                yield delta
        finally:
            if pending is not None and not pending.done():
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
            close = getattr(iterator, "aclose", None)
            if close:
                await close()

    async def finish(self, runtime, status, error=None):
        async with runtime.finish_lock:
            await self._finish(runtime, status, error)

    async def _finish(self, runtime, status, error=None):
        if runtime.finished:
            return
        runtime.metrics["totalMs"] = round((monotonic() - runtime.started_clock) * 1000, 2)
        if status == "completed":
            await self.verify_access(runtime)
        async with self.session_factory() as session, session.begin():
            terminal = await AnswerRepository(session).persist(
                runtime, terminal=status, error=error, validate_sources=status == "completed")
        runtime.flushed()
        if terminal:
            # The terminal event is withheld until its answer and usage commit succeeds.
            runtime.events.append(terminal)
            runtime.status = terminal["data"]["status"]
        runtime.finished = True
        await runtime.notify()
        if runtime.status == "completed":
            try:
                from ..personal_wiki.service import enqueue_for_message
                await enqueue_for_message(self.session_factory, runtime.principal, runtime.message_id)
            except Exception:
                # Post-answer enrichment is independent. A failed enqueue must not
                # turn the already committed answer into a false generation failure.
                # Its durable warning is visible on restore; explicit organize can retry.
                async with self.session_factory() as session, session.begin():
                    row = await AnswerRepository(session).owned(runtime.run_id, runtime.principal.id, lock=True)
                    warning = "답변은 저장됐으나 개인 위키 정리 작업을 등록하지 못했습니다."
                    row.warnings = list(dict.fromkeys((row.warnings or []) + [warning]))

    async def execute(self, runtime, request):
        usages, generation_usage = [], None
        generation_started = None
        generation_attempted = False
        try:
            await self.verify_access(runtime)
            if runtime.cancel_event.is_set():
                raise asyncio.CancelledError()
            runtime.status = "running"
            await runtime.emit("run.started", {"messageId": runtime.message_id,
                "conversationId": runtime.conversation_id, "responseMode": request.response_mode,
                "extended": request.extended, "generationConfig": runtime.generation_config})
            await self.flush(runtime, force=True)
            history = await self.conversations.history(runtime.principal, runtime.conversation_id, runtime.user_message_id)

            async def progress(data):
                await runtime.emit("retrieval.status", data)
                await self.flush(runtime, force=True)

            retrieval_start = monotonic()
            try:
                result = await self.retrieval.search(runtime.principal, request, for_answer=True,
                    progress=progress, cancel_event=runtime.cancel_event, history=history)
            finally:
                runtime.metrics["retrievalMs"] = round((monotonic() - retrieval_start) * 1000, 2)
            runtime.retrieval_run_id = result["retrievalRunId"]
            usages.extend(result["usage"].get("components", []))
            runtime.usage = summarize_usage(usages)
            runtime.warnings = list(result.get("warnings", []))
            if self.settings.provider_mode == "fixture":
                runtime.warnings.append("명시적 fixture 응답입니다. 실제 모델의 생성 품질·비용을 확인한 결과가 아닙니다.")
            runtime.citations = [citation(hit) for hit in result["hits"]]
            # A follow-up can depend on an earlier answer. Keep those dependencies
            # for current ACL checks rather than hiding only the earlier citation.
            seen = {item["id"] for item in runtime.citations}
            for item in history:
                for previous in item.get("citations", []):
                    if previous.get("id") not in seen:
                        runtime.citations.append({**previous, "contextOrigin": "earlier_answer"})
                        seen.add(previous.get("id"))
            runtime.relations, runtime.source_views = result.get("relations", []), result.get("sourceViews", [])
            await self.verify_access(runtime)
            await runtime.emit("retrieval.status", {"stage": "ready", "message": "답변에 사용할 근거 범위를 구성했습니다.",
                "retrievalRunId": result["retrievalRunId"], "indexSnapshotId": result["indexSnapshotId"],
                "groupCoverage": result["groupCoverage"], "warnings": runtime.warnings,
                "stopReason": result["stopReason"]})
            for kind, values in (("citation.add", runtime.citations), ("relation.add", runtime.relations),
                                 ("source_view.add", runtime.source_views)):
                for value in values:
                    await runtime.emit(kind, value)
            await self.flush(runtime, force=True)
            messages = build_messages(request, result, history, max_characters=self.settings.prompt_max_characters)
            runtime.metrics["promptCharacters"] = sum(len(item["content"]) for item in messages)
            runtime.metrics["groundingCharacters"] = result["exploration"]["grounding"]["groundingCharacters"]
            generation_started = monotonic()
            generation_attempted = True
            # No SQL session/transaction is held while awaiting provider output.
            async for delta in self.provider_deltas(runtime, messages):
                if runtime.cancel_event.is_set() or runtime.finished:
                    raise asyncio.CancelledError()
                if delta.model:
                    runtime.generation_config["model"] = delta.model
                if getattr(delta, "provider_event_type", None) and runtime.metrics["providerEventMs"] is None:
                    runtime.metrics["providerEventMs"] = round((monotonic() - runtime.started_clock) * 1000, 2)
                if delta.usage is not None:
                    generation_usage = {**delta.usage, "operation": "answer_generation"}
                    runtime.usage = summarize_usage(usages + [generation_usage])
                if delta.text:
                    if runtime.metrics["firstTextMs"] is None:
                        runtime.metrics["firstTextMs"] = round((monotonic() - runtime.started_clock) * 1000, 2)
                    runtime.content += delta.text
                    # Forward each real provider delta without post-hoc fake typing.
                    await runtime.emit("text.delta", {"text": delta.text})
                await self.flush(runtime)
            runtime.metrics["generationMs"] = round((monotonic() - generation_started) * 1000, 2)
            runtime.usage = summarize_usage(usages + [generation_usage or unknown_usage("answer_generation", runtime.generation_config["model"])])
            if not runtime.content.strip():
                raise AppError(502, "EMPTY_PROVIDER_ANSWER", "공급자가 실제 답변 본문을 보내지 않았습니다.", retryable=True)
            await self.finish(runtime, "completed")
        except asyncio.CancelledError as exc:
            if getattr(exc, "usage", None):
                usages.extend(exc.usage.get("components", []))
            if generation_started:
                runtime.metrics["generationMs"] = round((monotonic() - generation_started) * 1000, 2)
            if generation_attempted:
                usages.append(generation_usage or unknown_usage("answer_generation", runtime.generation_config.get("model")))
            runtime.usage = summarize_usage(usages)
            error = {"code": "PROCESS_INTERRUPTED", "message": "서버 종료로 답변이 중단되었습니다.", "retryable": True} if runtime.cancel_kind == "interrupted" else None
            await self.finish(runtime, runtime.cancel_kind, error)
        except Exception as exc:
            if generation_started:
                runtime.metrics["generationMs"] = round((monotonic() - generation_started) * 1000, 2)
            observed = getattr(exc, "usage", None)
            if generation_attempted and getattr(exc, "code", None) != "configuration_blocked":
                observed_generation = observed if observed and "components" not in observed else None
                usages.append(generation_usage or observed_generation or unknown_usage("answer_generation", runtime.generation_config.get("model")))
            if observed and "components" in observed:
                usages.extend(observed["components"])
            runtime.usage = summarize_usage(usages)
            public_error = exc.public() if isinstance(exc, AppError) else {
                "code": "ANSWER_FAILED", "message": "답변 처리 중 오류가 발생했습니다. 저장된 부분을 확인하고 다시 시도하세요.", "retryable": True}
            status = "cancelled" if runtime.cancel_event.is_set() or getattr(exc, "code", None) == "RUN_CANCELLED" else "failed"
            await self.finish(runtime, status, None if status == "cancelled" else public_error)

    async def run(self, runtime, request):
        try:
            await self.execute(runtime, request)
        except Exception as exc:
            # If final persistence itself fails, never emit a false success/failure
            # commit. Restore reconciles the dead run when storage is reachable.
            runtime.storage_error = True
            logging.getLogger("knowledge.answers").error("answer_persistence_failed run_id=%s error_type=%s",
                                                         runtime.run_id, type(exc).__name__)
            await runtime.notify()
