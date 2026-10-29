"""Bounded discovery on the existing worker; publication stays in ProposalService."""
import asyncio
from ...core.errors import AppError
from ...core.ids import utcnow
from ...identity.repository import UserRepository
from ...identity.service import principal_from_user
from ...documents.entities import DocumentRevision, Document
from ...integrations.providers import get_embedding_client, get_generation_client, generate_json
from ...integrations.rerank import configured_reranker
from ..names import name_key
from ..repository import WikiRepository
from ..search import WikiSearchService
from ..proposals.dto import ProposalRequest
from ..proposals.service import ProposalService
from ..proposals.source import document_context
from .repository import DocumentWikiRepository
from .dto import ChangePlan
from .prompt import messages


async def process_document_wiki_job(sessions, settings, job_id, embedding_client=None, generation_client=None):
    usage, reranker = {}, None
    try:
        async with asyncio.timeout(settings.wiki_proposal_timeout_seconds):
            embedding = embedding_client or get_embedding_client(settings)
            generator = generation_client or get_generation_client(settings)
            reranker = configured_reranker(settings)
            async with sessions() as session:
                item = await DocumentWikiRepository(session).get(job_id)
                if not item or item.status != 'running':
                    return {'status': item.status if item else 'superseded'}
                revision = await session.get(DocumentRevision, item.source_revision_id)
                document = await session.get(Document, revision.document_id)
                user = await UserRepository(session).get(document.owner_id)
                if not user or not user.is_active:
                    raise AppError(403, 'source_owner_unavailable', '문헌 등록자 계정이 비활성화되어 자동 검토를 중단했습니다.')
                principal = principal_from_user(user)
                document, revision, evidence, warnings = await document_context(session, principal, revision.id)
                source_id, title = revision.id, revision.title
            search = WikiSearchService(sessions, settings, embedding, reranker)
            similar = await search.similar(principal, title[:300], '\n'.join(e['text'] for e in evidence)[:3000])
            warnings.extend(similar.warnings)
            candidates = []
            async with sessions() as session:
                for hit in similar.items:
                    page, rev, _, _ = await WikiRepository(session).detail(hit.page.id)
                    candidates.append({'pageId': page.id, 'revisionId': rev.id, 'title': rev.title,
                        'aliases': rev.aliases, 'meaning': rev.meaning, 'markdown': rev.markdown[:2400]})
            payload = {'source': {'revisionId': source_id, 'title': title, 'passages': evidence},
                       'candidates': candidates, 'maxProposals': settings.wiki_auto_max_proposals}
            raw, usage['generation'] = await generate_json(generator, messages(payload, settings.prompt_max_characters),
                effort=settings.generation_effort, max_characters=8000)
            plan = ChangePlan.model_validate(raw)
            allowed_ids = {e['passageId'] for e in evidence}
            allowed_pages = {c['pageId'] for c in candidates}
            selected, targets = [], set()
            for idea in plan.ideas[:settings.wiki_auto_max_proposals]:
                if not set(idea.evidence_ids) <= allowed_ids:
                    warnings.append('제공한 실제 원문 구간과 대응하지 않는 보강점은 제외했습니다.'); continue
                if idea.mode == 'create':
                    if not idea.title.strip() or idea.page_id:
                        continue
                    # Exact names warn, never force a semantic merge or retarget an edit.
                    same = [c for c in candidates if name_key(idea.title) in {name_key(c['title']), *map(name_key, c['aliases'])}]
                    if same:
                        warnings.append('같은 이름의 기존 개념이 있습니다. 새 초안을 반영하기 전에 유사 문서를 비교해 주세요.')
                if idea.mode == 'edit' and idea.page_id not in allowed_pages:
                    continue
                key = idea.page_id or name_key(idea.title)
                if key in targets:
                    continue
                targets.add(key); selected.append(idea)
            # Atomic enqueue + completion. A crash never commits half the proposal set.
            async with sessions() as session, session.begin():
                current = await DocumentWikiRepository(session).get(job_id, lock=True)
                if current.status != 'running':
                    return {'status': current.status}
                await document_context(session, principal, source_id)
                proposals = []
                for index, idea in enumerate(selected):
                    request = ProposalRequest(request_id=f'auto:{job_id}:{index}', mode=idea.mode,
                        page_id=idea.page_id, instruction=f'{idea.title}\n{idea.instruction}', context_text='')
                    try:
                        async with session.begin_nested():
                            proposal = await ProposalService(sessions).enqueue(session, principal, request,
                                origin_revision_id=source_id, source_passage_ids=list(dict.fromkeys(idea.evidence_ids)))
                        proposals.append(proposal['id'])
                    except AppError as exc:
                        warnings.append('한 보강점의 제안을 생략했습니다: ' + exc.message)
                current.status = 'succeeded' if proposals else 'no_changes'
                current.result = {'reason': plan.reason, 'proposalIds': proposals, 'warnings': list(dict.fromkeys(warnings)),
                    'model': generator.model, 'sourcePassageIds': sorted(allowed_ids),
                    'candidatePageIds': sorted(allowed_pages), 'semanticStatus': similar.semantic_status,
                    'reranking': similar.reranking}
                current.usage, current.updated_at = usage, utcnow()
            return {'status': current.status, 'discoveryId': job_id, 'proposals': len(proposals)}
    except Exception as exc:
        if getattr(exc, 'usage', None):
            usage['generation'] = exc.usage
        error = exc.public() if isinstance(exc, AppError) else {'code': 'wiki_discovery_failed',
            'message': '위키 보강 기회를 확인하지 못했습니다. 문헌 검색과 직접 위키 편집은 계속 사용할 수 있습니다.'}
        async with sessions() as session, session.begin():
            current = await DocumentWikiRepository(session).get(job_id, lock=True)
            if current and current.status == 'running':
                current.status = 'superseded' if getattr(exc, 'code', '') in ('source_not_found', 'proposal_source_changed') else 'failed'
                current.error, current.usage, current.updated_at = error, usage, utcnow()
        return {'status': current.status if current else 'failed', 'discoveryId': job_id}
    finally:
        if reranker:
            await reranker.aclose()
