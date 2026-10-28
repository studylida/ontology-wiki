"""Owner-scoped answer use cases. GET/reconnect never starts generation."""
import asyncio
import hashlib
import json
from time import monotonic
import asyncpg
from sqlalchemy.exc import IntegrityError
from knowledge.core.errors import AppError
from knowledge.conversations.entities import Message
from knowledge.conversations.protection import source_state, visible_message
from knowledge.conversations.repository import ConversationRepository
from knowledge.documents.repository import DocumentRepository
from knowledge.rag.entities import RetrievalRun
from .repository import AnswerRepository
from .runtime import RunRegistry
from .states import ACTIVE, RETRYABLE, TERMINAL


class AnswerService:
    def __init__(self, sessions, settings, identity, rag, generation):
        self.sessions, self.settings, self.identity = sessions, settings, identity
        self.rag, self.generation = rag, generation
        self.registry = RunRegistry()
        self._lease = None

    async def start(self):
        # Dedicated session lock, no long-lived SQL transaction. A second API
        # must not recover a first process's live generation as interrupted.
        self._lease = await asyncpg.connect(self.settings.database_url.replace('postgresql+asyncpg://', 'postgresql://', 1))
        if not await self._lease.fetchval('SELECT pg_try_advisory_lock(820261031)'):
            await self._lease.close()
            self._lease = None
            raise RuntimeError('This MVP requires one answer API process per database; use --workers 1')
        async with self.sessions() as session, session.begin():
            await AnswerRepository(session).recover()

    async def close(self):
        await self.registry.close()
        if self.rag.reranker is not None and hasattr(self.rag.reranker, 'aclose'):
            await self.rag.reranker.aclose()
        if self._lease is not None:
            await self._lease.close()
            self._lease = None

    async def check_live(self, principal, source_ids):
        if self._lease is None or self._lease.is_closed():
            raise AppError(503, 'execution_lease_lost', '실행 연결이 중단되었습니다. 자동으로 모델을 다시 호출하지 않습니다.', retryable=True)
        await self.identity.refresh_principal(principal)
        async with self.sessions() as session:
            if not await DocumentRepository(session).ensure_readable(principal, source_ids):
                raise AppError(409, 'source_unavailable', '근거 문헌이 비활성화되어 실행을 중단했습니다.', retryable=True)

    @staticmethod
    def summary(run):
        return {'runId': run.id, 'conversationId': run.conversation_id,
                'userMessageId': run.user_message_id, 'messageId': run.message_id,
                'requestId': run.request_id, 'status': run.status, 'durableSeq': run.durable_seq,
                'eventsUrl': '/api/v1/answer-runs/' + run.id + '/events'}

    async def create(self, principal, body, *, retry_of=None):
        principal.require('conversations:write')
        payload = {'conversationId': body.conversation_id, 'question': body.question, 'requestId': body.request_id}
        if retry_of:
            payload['retryOf'] = retry_of
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        runtime = None
        try:
            async with self.sessions() as session, session.begin():
                conversation = await ConversationRepository(session).owned(body.conversation_id, principal.id, lock=True)
                repository = AnswerRepository(session)
                existing = await repository.by_request(principal.id, body.request_id)
                if existing is not None:
                    if existing.request_hash != fingerprint:
                        raise AppError(409, 'request_id_conflict', '같은 요청 ID가 다른 질문에 사용되었습니다.')
                    return self.summary(existing)
                if await repository.active(conversation.id) is not None:
                    raise AppError(409, 'conversation_busy', '이 대화의 답변이 진행 중입니다. 완료하거나 취소한 뒤 질문해 주세요.', retryable=True)
                retry_user = None
                if retry_of:
                    old = await repository.owned(retry_of, principal.id)
                    latest = await repository.latest_user(conversation.id)
                    if old.status not in RETRYABLE or latest is None or latest.id != old.user_message_id:
                        raise AppError(409, 'retry_not_allowed', '가장 최근 질문의 중단·실패 답변만 재시도할 수 있습니다.')
                    retry_user = latest
                run = await repository.create(principal, conversation, payload, fingerprint, self.registry.epoch,
                                              retry_user=retry_user)
                result = self.summary(run)
                # Reserve before commit so a simultaneous GET cannot mistake
                # the committed-but-not-launched run for an abandoned task.
                runtime = self.registry.add(run.id)
        except IntegrityError:
            if runtime is not None:
                self.registry.runs.pop(runtime.run_id, None)
            async with self.sessions() as session:
                existing = await AnswerRepository(session).by_request(principal.id, body.request_id)
                if existing is not None and existing.request_hash == fingerprint:
                    return self.summary(existing)
            raise AppError(409, 'request_id_conflict', '요청 ID 또는 대화의 진행 상태가 충돌했습니다.') from None
        except BaseException:
            if runtime is not None:
                self.registry.runs.pop(runtime.run_id, None)
            raise
        from .execution import execute
        try:
            # Cancellation may arrive after commit but before task creation.
            # Its endpoint persists the terminal state; do not start a provider call.
            if not runtime.cancel_event.is_set():
                runtime.task = asyncio.create_task(execute(self, runtime, principal, body.question,
                    body.conversation_id, result['userMessageId']), name='answer:' + result['runId'])
        except Exception:
            self.registry.runs.pop(runtime.run_id, None)
            async with self.sessions() as session, session.begin():
                stored = await AnswerRepository(session).owned(result['runId'], principal.id, lock=True)
                await AnswerRepository(session).interrupt(stored)
            raise
        return result

    async def repair_if_abandoned(self, principal, run_id):
        runtime = self.registry.get(run_id)
        if runtime is not None:
            if runtime.task is None or not runtime.task.done():
                return
            if runtime.status in TERMINAL and not runtime.storage_failed:
                return
        async with self.sessions() as session, session.begin():
            repository = AnswerRepository(session)
            run = await repository.owned(run_id, principal.id, lock=True)
            if run.status in ACTIVE:
                await repository.interrupt(run)

    async def get(self, principal, run_id):
        principal.require('conversations:read')
        await self.repair_if_abandoned(principal, run_id)
        async with self.sessions() as session:
            # persist() locks this same run before changing its message and cursor.
            # Hold it only for this DB snapshot, never for HTTP/SSE/provider I/O.
            # Otherwise READ COMMITTED could pair an older cursor with newer text.
            run = await AnswerRepository(session).owned(run_id, principal.id, lock=True)
            message = await session.get(Message, run.message_id)
            view = await visible_message(session, principal, message)
            result = {**self.summary(run), 'answer': view.public(), 'error': run.error,
                      'usage': run.usage, 'retrievalRunId': run.retrieval_run_id}
            if view.source_unavailable:
                result['retrieval'] = None
            else:
                retrieval = await session.get(RetrievalRun, run.retrieval_run_id) if run.retrieval_run_id else None
                result['retrieval'] = retrieval.result if retrieval else None
            return result

    async def cancel(self, principal, run_id):
        principal.require('conversations:write')
        async with self.sessions() as session:
            run = await AnswerRepository(session).owned(run_id, principal.id)
            terminal = run.status in TERMINAL
        if not terminal:
            runtime = self.registry.get(run_id)
            if runtime is not None:
                runtime.cancel_event.set()
                if runtime.task is not None and not runtime.task.done():
                    runtime.task.cancel()
                    await asyncio.gather(runtime.task, return_exceptions=True)
            # A coroutine cancelled before first execution cannot run its handler.
            async with self.sessions() as session, session.begin():
                repository = AnswerRepository(session)
                run = await repository.owned(run_id, principal.id, lock=True)
                if run.status in ACTIVE:
                    error = {'code': 'cancelled', 'message': '사용자가 답변을 취소했습니다.', 'retryable': True}
                    await repository.persist(run.id, run.process_epoch, status='cancelled', error=error,
                        events=[{'type': 'cancelled', 'data': {'status': 'cancelled', 'error': error}}])
            if runtime is not None and runtime.task is None:
                runtime.status = 'cancelled'
                self.registry.runs.pop(run_id, None)
        return await self.get(principal, run_id)

    async def retry(self, principal, run_id, body):
        from .dto import AnswerRequest
        principal.require('conversations:write')
        await self.repair_if_abandoned(principal, run_id)
        async with self.sessions() as session:
            old = await AnswerRepository(session).owned(run_id, principal.id)
            request = AnswerRequest(conversation_id=old.conversation_id,
                question=old.request_payload['question'], request_id=body.request_id)
        return await self.create(principal, request, retry_of=run_id)

    async def check_stream(self, principal, run_id, after):
        principal.require('conversations:read')
        await self.repair_if_abandoned(principal, run_id)
        async with self.sessions() as session:
            run = await AnswerRepository(session).owned(run_id, principal.id)
            if after > run.durable_seq:
                raise AppError(409, 'invalid_event_cursor', '저장된 이벤트보다 뒤의 커서입니다. 실행 상태를 다시 조회해 주세요.')
            message = await session.get(Message, run.message_id)
            if await source_state(session, principal, message.source_revision_ids) == 'unavailable':
                raise AppError(409, 'source_unavailable', '비활성화된 근거가 있어 이전 답변 이벤트를 재생하지 않습니다.')

    async def event_stream(self, principal, run_id, after, disconnected, authenticate=None):
        heartbeat = monotonic()
        while not await disconnected():
            try:
                principal = await authenticate() if authenticate is not None else await self.identity.refresh_principal(principal)
                await self.check_stream(principal, run_id, after)
                async with self.sessions() as session:
                    repository = AnswerRepository(session)
                    run = await repository.owned(run_id, principal.id)
                    events = await repository.events_after(run_id, after)
                    done = run.status in TERMINAL
                for event in events:
                    if authenticate is not None:
                        principal = await authenticate()
                    await self.check_stream(principal, run_id, after)
                    after = event['seq']
                    yield event
                if done and not events:
                    return
            except AppError as exc:
                yield {'type': 'stream_error', 'runId': run_id, 'data': {'error': exc.public()}}
                return
            except Exception:
                yield {'type': 'stream_error', 'runId': run_id, 'data': {'error': {
                    'code': 'event_store_unavailable', 'message': '저장된 이벤트를 읽지 못했습니다. 재연결은 새 생성을 시작하지 않습니다.', 'retryable': True}}}
                return
            if monotonic() - heartbeat > 10:
                heartbeat = monotonic()
                yield None
            if not events:
                await asyncio.sleep(.15)
