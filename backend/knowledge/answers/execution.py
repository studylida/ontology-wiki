"""Retrieval and generation orchestration with commit-before-publication events."""
import asyncio
import logging
import re
from time import monotonic
from knowledge.core.errors import AppError
from knowledge.conversations.protection import source_state
from knowledge.documents.repository import DocumentRepository
from .citations import CitationNormalizer
from .prompt import build_messages
from .repository import AnswerRepository


async def persist(service, runtime, *, status=None, retrieval_id=None, error=None):
    async with runtime.write_lock:
        events = list(runtime.pending)
        try:
            async with service.sessions() as session, session.begin():
                if status == 'completed' and not await DocumentRepository(session).ensure_readable(
                        None, runtime.source_ids, lock=True):
                    raise AppError(409, 'source_unavailable', '답변 중 근거 문헌이 비활성화되었습니다.', retryable=True)
                await AnswerRepository(session).persist(runtime.run_id, runtime.epoch,
                    events=events, content=runtime.text, citations=runtime.citations,
                    source_ids=runtime.source_ids, warnings=runtime.warnings,
                    status=status, retrieval_id=retrieval_id, usage=runtime.usage, error=error)
        except Exception:
            # No pending event, especially complete, is exposed before COMMIT succeeds.
            runtime.storage_failed = True
            raise
        runtime.pending.clear()
        runtime.pending_chars = 0
        runtime.last_flush = monotonic()
        if status:
            runtime.status = status
        runtime.changed.set()


async def execute(service, runtime, principal, question, conversation_id, user_message_id):
    phase = 'retrieval'
    iterator = next_delta = None
    normalizer = None
    try:
        async with asyncio.timeout(600):
            runtime.pending.append({'type': 'state', 'data': {'status': 'retrieving'}})
            await persist(service, runtime, status='retrieving')
            history, history_sources = [], set()
            async with service.sessions() as session:
                rows = await AnswerRepository(session).history_before(conversation_id, user_message_id)
                for message in rows:
                    if message.role == 'assistant':
                        if message.status != 'completed' or await source_state(session, principal, message.source_revision_ids) != 'current':
                            continue
                        history_sources.update(message.source_revision_ids)
                    history.append({'role': message.role,
                        'content': re.sub(r'\[\[[^\]]+\]\]', '', message.content) if message.role == 'assistant' else message.content})
            retrieval_id, found = await service.rag.retrieve(principal, conversation_id, question, history)
            runtime.source_ids = sorted(history_sources | set(found['sourceRevisionIds']))
            runtime.warnings = found['warnings']
            runtime.usage = {'retrieval': found['usage']}
            messages = build_messages(question, history, found['evidence'], service.settings.prompt_max_characters)
            normalizer = CitationNormalizer(found['evidence'])
            runtime.pending.append({'type': 'state', 'data': {'status': 'generating',
                'retrievalRunId': retrieval_id, 'evidenceStatus': found['status'], 'warnings': runtime.warnings}})
            await persist(service, runtime, status='generating', retrieval_id=retrieval_id)
            phase = 'generation'
            await service.check_live(principal, runtime.source_ids)
            iterator = service.generation.stream(messages, effort=service.settings.generation_effort,
                                                 cancel_event=runtime.cancel_event).__aiter__()
            checked = monotonic()
            while True:
                if runtime.cancel_event.is_set():
                    raise asyncio.CancelledError()
                if next_delta is None:
                    next_delta = asyncio.ensure_future(anext(iterator))
                try:
                    delta = await asyncio.wait_for(asyncio.shield(next_delta), timeout=.25)
                except TimeoutError:
                    if runtime.pending and monotonic() - runtime.last_flush >= service.settings.stream_flush_seconds:
                        await persist(service, runtime)
                    if monotonic() - checked >= .5:
                        await service.check_live(principal, runtime.source_ids)
                        checked = monotonic()
                    continue
                except StopAsyncIteration:
                    next_delta = None
                    break
                next_delta = None
                if monotonic() - checked >= .5:
                    await service.check_live(principal, runtime.source_ids)
                    checked = monotonic()
                if delta.usage is not None:
                    runtime.usage = {**runtime.usage, 'generation': delta.usage}
                if delta.text:
                    text, citations = normalizer.feed(delta.text)
                    runtime.citations = normalizer.citations
                    runtime.text += text
                    runtime.pending_chars += len(text)
                    runtime.pending.extend({'type': 'citation', 'data': c} for c in citations)
                    if text:
                        runtime.pending.append({'type': 'delta', 'data': {'text': text}})
                    if len(runtime.text) > 120000:
                        raise AppError(502, 'answer_output_limit', '답변 출력 한도를 초과했습니다.', retryable=True)
                if (runtime.pending_chars >= service.settings.stream_flush_characters
                        or monotonic() - runtime.last_flush >= service.settings.stream_flush_seconds):
                    await persist(service, runtime)
            tail, citations = normalizer.feed('', final=True)
            runtime.text += tail
            runtime.citations = normalizer.citations
            runtime.pending.extend({'type': 'citation', 'data': c} for c in citations)
            if tail:
                runtime.pending.append({'type': 'delta', 'data': {'text': tail}})
            runtime.warnings = list(dict.fromkeys([*runtime.warnings, *normalizer.warnings]))
            if not runtime.text.strip():
                raise AppError(502, 'empty_answer', '모델이 답변 본문을 반환하지 않았습니다.', retryable=True)
            await service.check_live(principal, runtime.source_ids)
            runtime.pending.append({'type': 'complete', 'data': {'status': 'completed', 'warnings': runtime.warnings}})
            phase = 'persistence'
            await persist(service, runtime, status='completed')
    except BaseException as exc:
        if not isinstance(exc, (Exception, asyncio.CancelledError)):
            raise
        status = 'interrupted' if runtime.shutdown else 'cancelled' if isinstance(exc, asyncio.CancelledError) else 'failed'
        if isinstance(exc, AppError):
            error = {**exc.public(), 'phase': phase}
        else:
            error = {'code': 'execution_interrupted' if runtime.shutdown else 'cancelled' if status == 'cancelled'
                     else 'answer_timeout' if isinstance(exc, TimeoutError) else phase + '_failed',
                     'message': '답변 실행이 중단되었습니다. 저장된 내용은 복원할 수 있으며 재시도는 직접 요청해야 합니다.',
                     'retryable': True, 'phase': phase}
        if getattr(exc, 'usage', None) is not None:
            runtime.usage = {**runtime.usage, 'generation' if phase == 'generation' else 'retrieval': exc.usage}
        # A failed completion transaction must never leave a complete event in the next batch.
        runtime.pending = [e for e in runtime.pending if e['type'] != 'complete']
        if normalizer is not None:
            runtime.warnings = list(dict.fromkeys([*runtime.warnings, *normalizer.warnings]))
        runtime.pending.append({'type': status if status != 'failed' else 'error', 'data': {'status': status, 'error': error}})
        try:
            await persist(service, runtime, status=status, error=error)
        except Exception:
            # Durable GET/replay will reconcile the unfinished run when storage returns.
            runtime.storage_failed = True
            logging.getLogger('knowledge.answers').error('answer_persistence_failed run_id=%s', runtime.run_id)
    finally:
        if next_delta is not None:
            next_delta.cancel()
            await asyncio.gather(next_delta, return_exceptions=True)
        if iterator is not None and hasattr(iterator, 'aclose'):
            try:
                await iterator.aclose()
            except (Exception, asyncio.CancelledError):
                pass
        runtime.changed.set()
