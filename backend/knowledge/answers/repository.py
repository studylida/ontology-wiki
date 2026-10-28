"""Durable runs and event batches. Callers own short transaction boundaries."""
from datetime import timedelta
from sqlalchemy import select
from knowledge.core.errors import AppError
from knowledge.core.ids import new_id, utcnow
from knowledge.conversations.entities import Conversation, Message
from .entities import AnswerRun, AnswerEventBatch
from .states import ACTIVE, TERMINAL


class AnswerRepository:
    def __init__(self, session):
        self.session = session

    async def owned(self, run_id, owner_id, *, lock=False):
        statement = select(AnswerRun).where(AnswerRun.id == run_id, AnswerRun.owner_id == owner_id)
        if lock:
            statement = statement.with_for_update()
        run = await self.session.scalar(statement)
        if run is None:
            raise AppError(404, 'ANSWER_NOT_FOUND', '답변 실행이 없거나 접근할 수 없습니다.')
        return run

    async def by_request(self, owner_id, request_id):
        return await self.session.scalar(select(AnswerRun).where(
            AnswerRun.owner_id == owner_id, AnswerRun.request_id == request_id))

    async def active(self, conversation_id):
        return await self.session.scalar(select(AnswerRun).where(
            AnswerRun.conversation_id == conversation_id, AnswerRun.status.in_(ACTIVE)))

    async def create(self, principal, conversation, payload, request_hash, epoch, *, retry_user=None):
        now = utcnow()
        if retry_user is None:
            user = Message(conversation_id=conversation.id, role='user', content=payload['question'], created_at=now)
            self.session.add(user)
            await self.session.flush()
        else:
            user = retry_user
        assistant = Message(conversation_id=conversation.id, role='assistant', content='',
                            status='accepted', created_at=now + timedelta(microseconds=1))
        self.session.add(assistant)
        await self.session.flush()
        run = AnswerRun(id=new_id('run'), owner_id=principal.id, conversation_id=conversation.id,
            user_message_id=user.id, message_id=assistant.id, request_id=payload['requestId'],
            request_hash=request_hash, request_payload=payload, process_epoch=epoch, durable_seq=0)
        self.session.add(run)
        await self.session.flush()
        assistant.run_id = run.id
        conversation.updated_at = now
        await self.append(run, [{'type': 'state', 'data': {'status': 'accepted'}}])
        return run

    async def append(self, run, events):
        if not events:
            return []
        first = run.durable_seq + 1
        numbered = [{'runId': run.id, 'seq': first + i, **event} for i, event in enumerate(events)]
        self.session.add(AnswerEventBatch(run_id=run.id, first_seq=first,
            last_seq=numbered[-1]['seq'], events=numbered))
        run.durable_seq = numbered[-1]['seq']
        run.updated_at = utcnow()
        return numbered

    async def persist(self, run_id, epoch, *, events, content=None, citations=None,
                      source_ids=None, warnings=None, status=None, retrieval_id=None, usage=None, error=None):
        run = await self.session.get(AnswerRun, run_id, with_for_update=True)
        if run is None or run.process_epoch != epoch or run.status in TERMINAL:
            return []
        message = await self.session.get(Message, run.message_id)
        if content is not None:
            message.content = content
        if citations is not None:
            message.citations = list(citations)
        if source_ids is not None:
            message.source_revision_ids = sorted(set(source_ids))
        if warnings is not None:
            message.warnings = list(dict.fromkeys(warnings))
        if retrieval_id is not None:
            run.retrieval_run_id = retrieval_id
        if usage is not None:
            run.usage = dict(usage)
        if status is not None:
            run.status = message.status = status
        run.error = error
        return await self.append(run, events)

    async def events_after(self, run_id, after):
        batches = (await self.session.scalars(select(AnswerEventBatch).where(
            AnswerEventBatch.run_id == run_id, AnswerEventBatch.last_seq > after)
            .order_by(AnswerEventBatch.first_seq).limit(16))).all()
        return [event for batch in batches for event in batch.events if event['seq'] > after]

    async def interrupt(self, run):
        if run.status not in ACTIVE:
            return
        message = await self.session.get(Message, run.message_id)
        run.status = message.status = 'interrupted'
        run.error = {'code': 'execution_interrupted', 'message': '실행이 중단되었습니다. 자동 재호출 없이 저장된 내용만 복원했습니다.', 'retryable': True}
        await self.append(run, [{'type': 'interrupted', 'data': {'status': run.status, 'error': run.error}}])

    async def recover(self):
        runs = (await self.session.scalars(select(AnswerRun).where(AnswerRun.status.in_(ACTIVE)).with_for_update())).all()
        for run in runs:
            await self.interrupt(run)
        return len(runs)

    async def history_before(self, conversation_id, user_message_id):
        user = await self.session.get(Message, user_message_id)
        rows = (await self.session.scalars(select(Message).where(
            Message.conversation_id == conversation_id, Message.created_at < user.created_at)
            .order_by(Message.created_at.desc(), Message.id.desc()).limit(24))).all()
        return list(reversed(rows))

    async def latest_user(self, conversation_id):
        return await self.session.scalar(select(Message).where(
            Message.conversation_id == conversation_id, Message.role == 'user')
            .order_by(Message.created_at.desc(), Message.id.desc()).limit(1))
