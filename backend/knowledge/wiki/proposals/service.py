"""Draft visibility and atomic human publication. Never calls the model on GET."""
import hashlib
import json
from sqlalchemy.exc import SQLAlchemyError
from ...core.errors import AppError
from ...core.ids import utcnow
from ...evidence.access import EvidenceAccess
from ...identity.authorization import is_administrator
from ...conversations.repository import ConversationRepository
from ...conversations.protection import visible_message
from ..dto import PageCreate, PageEdit, MutationResult
from ..entities import WikiRevision
from ..repository import WikiRepository
from ..service import WikiService
from ..policy import require_read, can_edit
from .entities import WikiProposal
from .repository import ProposalRepository


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def require_access(principal, proposal):
    require_read(principal)
    if not proposal.origin_revision_id and proposal.owner_id != principal.id and not (proposal.page_id and is_administrator(principal)):
        raise AppError(404, 'proposal_not_found', '제안을 찾을 수 없습니다.')


async def require_sources(session, principal, proposal, *, current=False, lock=False):
    ids = set(proposal.result.get('sourceRevisionIds', []))
    if proposal.origin_revision_id:
        ids.add(proposal.origin_revision_id)
    if proposal.base_revision_id:
        ids.add(proposal.base_revision_id)
    ids.update(proposal.input.get('selectionRevisionIds', []))
    access = EvidenceAccess(session)
    if not await access.ensure_readable(principal, ids, lock=lock):
        raise AppError(409, 'proposal_source_unavailable', '제안의 근거가 비활성화되었습니다. 제안 내용을 다시 공개하거나 적용하지 않습니다.')
    if current and proposal.origin_revision_id:
        from .source import document_context
        await document_context(session, principal, proposal.origin_revision_id, proposal.input['sourcePassageIds'])
    if current:
        supporting = ids - {proposal.base_revision_id}
        if set(await access.current_ids(principal, supporting)) != supporting:
            raise AppError(409, 'proposal_sources_changed', '제안 이후 근거 판본이 바뀌었습니다. 최신 자료로 다시 요청해 주세요.')


def summary(item):
    return {'id': item.id, 'pageId': item.page_id, 'mode': item.mode, 'status': item.status,
            'originRevisionId': item.origin_revision_id, 'shared': bool(item.origin_revision_id),
            'createdAt': item.created_at.isoformat(), 'updatedAt': item.updated_at.isoformat()}


class ProposalService:
    def __init__(self, sessions):
        self.sessions, self.wiki = sessions, WikiService(sessions)

    async def submit(self, principal, body):
        async with self.sessions() as session, session.begin():
            return await self.enqueue(session, principal, body)

    async def enqueue(self, session, principal, body, *, origin_revision_id=None, source_passage_ids=None):
        """Shared submission use case. Origin is trusted worker-only input, never an HTTP field."""
        require_read(principal)
        fingerprint = body.model_dump(mode='json', exclude={'request_id'})
        if origin_revision_id:
            fingerprint.update(originRevisionId=origin_revision_id, sourcePassageIds=source_passage_ids)
        hashed = digest(fingerprint)
        repo = ProposalRepository(session)
        old = await repo.request_lock(principal.id, body.request_id)
        if old:
            if old.request_hash != hashed:
                raise AppError(409, 'proposal_request_conflict', '같은 요청 ID의 내용을 바꿀 수 없습니다.')
            return summary(old)
        base, revision_id, version = {}, None, None
        if body.page_id:
            page, revision, _, _ = await WikiRepository(session).detail(body.page_id)
            if len(revision.markdown) > 20000:
                raise AppError(422, 'proposal_budget', 'AI 부분 편집은 현재 20,000자 이하 문서에 제공됩니다. 직접 편집은 계속 사용할 수 있습니다.')
            base = {'title': revision.title, 'markdown': revision.markdown, 'sourceNote': revision.source_note,
                    'aliases': revision.aliases, 'meaning': revision.meaning}
            revision_id, version = revision.id, page.version
        data = {'instruction': body.instruction, 'employeeText': body.context_text, 'inputKind': 'employee',
                'selectionRevisionIds': []}
        if body.selection:
            selected = body.selection
            message = await ConversationRepository(session).message_for_owner(
                selected.conversation_id, selected.message_id, principal.id)
            view = await visible_message(session, principal, message)
            if view.source_unavailable or message.status not in ('completed', 'complete', 'saved'):
                raise AppError(409, 'selection_unavailable', '완료되고 열람 가능한 대화 내용만 선택할 수 있습니다.')
            if not selected.text.strip() or selected.text not in view.content:
                raise AppError(422, 'selection_mismatch', '선택한 문장이 해당 대화 메시지와 일치하지 않습니다.')
            data.update(employeeText=selected.text, inputKind='chat_selection',
                selectionRevisionIds=message.source_revision_ids or [])
            # No full conversation, message ID or nonselected text enters this draft.
        if origin_revision_id:
            from .source import document_context
            await document_context(session, principal, origin_revision_id, source_passage_ids)
            data.update(inputKind='document_change', sourcePassageIds=source_passage_ids)
        item = WikiProposal(origin_revision_id=origin_revision_id, owner_id=principal.id, request_id=body.request_id, request_hash=hashed,
            page_id=body.page_id, base_revision_id=revision_id, base_version=version,
            mode=body.mode, input=data, base_snapshot=base)
        session.add(item)
        await session.flush()
        return summary(item)


    async def list(self, principal, page_id=None):
        require_read(principal)
        async with self.sessions() as session:
            if page_id:
                await WikiRepository(session).get(page_id)
            return {'items': [summary(p) for p in await ProposalRepository(session).list(principal.id,
                            admin=is_administrator(principal), page_id=page_id)]}

    async def get(self, principal, proposal_id):
        async with self.sessions() as session:
            item = await ProposalRepository(session).get(proposal_id)
            require_access(principal, item)
            await require_sources(session, principal, item)
            editable, stale, current_version = True, False, None
            source_changed = False
            if item.origin_revision_id:
                try:
                    await require_sources(session, principal, item, current=True)
                except AppError:
                    source_changed = True
            if item.page_id:
                page = await WikiRepository(session).get(item.page_id)
                editable, current_version = can_edit(principal, page), page.version
                stale = page.version != item.base_version
            return {**summary(item), 'ownerId': item.owner_id, 'baseVersion': item.base_version,
                'baseRevisionId': item.base_revision_id, 'base': item.base_snapshot,
                'instruction': item.input['instruction'], 'employeeText': item.input['employeeText'],
                'inputKind': item.input['inputKind'], 'result': item.result,
                'error': item.error, 'usage': item.usage, 'stale': stale, 'currentVersion': current_version,
                'sourceChanged': source_changed,
                'canApply': item.status == 'ready' and editable and not stale and not source_changed,
                'appliedResult': MutationResult(**item.applied_result).public() if item.applied_result else None}

    async def dismiss(self, principal, proposal_id):
        async with self.sessions() as session, session.begin():
            item = await ProposalRepository(session).get(proposal_id, lock=True)
            require_access(principal, item)
            if item.status == 'applied':
                raise AppError(409, 'proposal_applied', '이미 반영된 내용은 위키의 일반 편집·이력을 이용해 주세요.')
            item.status, item.updated_at = 'dismissed', utcnow()
            return summary(item)

    async def apply(self, principal, proposal_id, body):
        require_read(principal)
        hashed = digest({'proposal': proposal_id, 'content': body.model_dump(mode='json', exclude={'request_id'})})
        try:
            async with self.sessions() as session, session.begin():
                wiki_repo = WikiRepository(session)
                receipt = await wiki_repo.mutation(principal.id, body.request_id)
                if receipt:
                    if receipt.payload_hash != hashed:
                        raise AppError(409, 'wiki_request_conflict', '같은 요청 ID에 다른 반영 내용을 사용할 수 없습니다.')
                    return MutationResult(**{**receipt.result, 'replayed': True})
                item = await ProposalRepository(session).get(proposal_id, lock=True)
                require_access(principal, item)
                if item.status == 'applied':
                    if item.applied_by != principal.id or item.applied_hash != hashed:
                        raise AppError(409, 'proposal_applied', '이미 반영된 제안입니다. 현재 위키와 이력을 확인해 주세요.')
                    return MutationResult(**{**item.applied_result, 'replayed': True})
                if item.status != 'ready':
                    raise AppError(409, 'proposal_not_ready', '검토 가능한 제안만 반영할 수 있습니다.')
                # Fixed mixed-source lock order before the target write. No network I/O here.
                await require_sources(session, principal, item, current=True, lock=True)
                content = body.model_dump(exclude={'request_id'})
                if item.page_id:
                    command = PageEdit(request_id=body.request_id, base_version=item.base_version, **content)
                    operation = 'edit'
                else:
                    command = PageCreate(request_id=body.request_id, **content)
                    operation = 'create'
                page = await self.wiki.write(session, principal, operation, command, item.page_id)
                revision = await session.get(WikiRevision, page.current_revision_id)
                revision.ai_proposal_id = item.id
                revision.provenance = {'kind': 'ai_assisted', 'requestedBy': item.owner_id,
                    'appliedBy': principal.id, 'inputKind': item.input['inputKind'],
                    'evidence': [{k: e[k] for k in ('sourceKind','pageId','documentId','sourceRevisionId','passageId','title','locator') if k in e}
                                 for e in item.result.get('evidence', [])],
                    'notice': 'AI 제안 당시 참고 자료입니다. 최종 문장의 사실성을 자동 인증하지 않습니다.'}
                result = MutationResult(page_id=page.id, revision_id=revision.id, version=page.version)
                item.status, item.updated_at = 'applied', utcnow()
                item.applied_result, item.applied_hash, item.applied_by = result.model_dump(), hashed, principal.id
                await wiki_repo.remember(principal.id, body.request_id, hashed, page, result.model_dump())
                return result
        except SQLAlchemyError as exc:
            raise AppError(503, 'proposal_storage_failed', '반영 결과를 확인하지 못했습니다. 동일한 요청으로 다시 확인해 주세요.', retryable=True) from exc
