"""Bounded requested work on the existing serial worker; no provider calls in DB locks."""
import asyncio
from ...core.errors import AppError
from ...core.ids import utcnow
from ...identity.repository import UserRepository
from ...identity.service import principal_from_user
from ...integrations.providers import get_embedding_client, get_generation_client, generate_json
from ...integrations.rerank import configured_reranker
from ...rag.service import RAGService
from ..repository import WikiRepository
from ..search import WikiSearchService
from .dto import GeneratedProposal
from .editing import materialize
from .prompt import messages
from .repository import ProposalRepository
from .service import require_sources


async def process_proposal_job(sessions, settings, job_id, embedding_client=None, generation_client=None):
    embedding = embedding_client or get_embedding_client(settings)
    generator = generation_client or get_generation_client(settings)
    usage, reranker = {}, configured_reranker(settings)
    try:
        async with asyncio.timeout(settings.wiki_proposal_timeout_seconds):
            async with sessions() as session:
                item = await ProposalRepository(session).get(job_id)
                if item.status != 'running':
                    return {'status': item.status}
                user = await UserRepository(session).get(item.owner_id)
                if user is None or not user.is_active:
                    raise AppError(403, 'proposal_owner_unavailable', '요청한 직원 계정이 비활성화되었습니다.')
                principal = principal_from_user(user)
                await require_sources(session, principal, item)
                mode, page_id, base, data = item.mode, item.page_id, item.base_snapshot, item.input
                if page_id:
                    page = await WikiRepository(session).get(page_id)
                    if page.version != item.base_version:
                        raise AppError(409, 'wiki_version_conflict', '생성 전에 대상 문서가 변경되었습니다. 최신 내용으로 다시 요청해 주세요.')
            query = (base.get('title', '') + '\n' + data['instruction'] + '\n' + data['employeeText'])[:4000]
            rag = RAGService(sessions, settings, embedding, reranker)
            _, retrieval = await rag.retrieve(principal, None, query, [], record=False)
            usage['retrieval'] = retrieval['usage']
            evidence, chars = [], 0
            for hit in retrieval['evidence']:
                if hit['sourceRevisionId'] == item.base_revision_id:
                    continue
                if chars + len(hit['text']) > 12000:
                    continue
                evidence.append({k: v for k, v in hit.items() if k in
                    ('sourceKind','documentId','pageId','passageId','sourceRevisionId','title','locator','text')})
                chars += len(hit['text'])
            search = WikiSearchService(sessions, settings, embedding, reranker)
            similar = await search.similar(principal, base.get('title') or data['instruction'][:300],
                base.get('markdown', '')[:3000] or data['employeeText'], exclude=page_id)
            candidates = {}
            async with sessions() as session:
                repo = WikiRepository(session)
                matches = await ProposalRepository(session).mentions(base.get('markdown','') + '\n' + data['employeeText'], page_id)
                for page, revision in matches:
                    candidates[page.id] = {'pageId': page.id, 'revisionId': revision.id, 'title': revision.title,
                        'aliases': revision.aliases, 'meaning': revision.meaning, 'excerpt': revision.markdown[:600]}
                for hit in similar.items:
                    if hit.page.id not in candidates and len(candidates) < 16:
                        candidates[hit.page.id] = {'pageId': hit.page.id, 'revisionId': hit.revision_id,
                            'title': hit.page.title, 'aliases': hit.page.aliases, 'meaning': hit.page.meaning,
                            'excerpt': hit.excerpt[:600]}
            payload = {'mode': mode, 'base': base, 'instruction': data['instruction'],
                       'employeeText': data['employeeText'], 'evidence': evidence, 'linkCandidates': list(candidates.values())}
            raw, generation_usage = await generate_json(generator, messages(payload, settings.prompt_max_characters),
                effort=settings.generation_effort, max_characters=45000)
            usage['generation'] = generation_usage
            parsed = GeneratedProposal.model_validate(raw)
            result = materialize(base, parsed, mode, candidates, evidence)
            result['sourceRevisionIds'] = sorted({e['sourceRevisionId'] for e in evidence} | {c['revisionId'] for c in candidates.values()})
            result['linkCandidates'] = [{'pageId': c['pageId'], 'revisionId': c['revisionId'], 'title': c['title']} for c in candidates.values()]
            result['similar'] = [{'pageId': h.page.id, 'title': h.page.title, 'meaning': h.page.meaning} for h in similar.items]
            result['warnings'] += [*retrieval['warnings'], *similar.warnings]
            result['model'] = generator.model
            result['sourceNote'] = base.get('sourceNote', '')
            result['aliases'], result['meaning'] = base.get('aliases', []), base.get('meaning', '')
            async with sessions() as session, session.begin():
                current = await ProposalRepository(session).get(job_id, lock=True)
                if current.status != 'running':
                    return {'status': current.status}
                current.result = result
                await require_sources(session, principal, current)
                current.status, current.updated_at, current.usage = 'ready', utcnow(), usage
            return {'status': 'ready', 'proposalId': job_id}
    except Exception as exc:
        if getattr(exc, 'usage', None):
            usage['generation'] = exc.usage
        error = exc.public() if isinstance(exc, AppError) else {
            'code': 'proposal_timeout' if isinstance(exc, TimeoutError) else 'proposal_generation_failed',
            'message': '제안 생성을 완료하지 못했습니다. 요청과 근거를 확인한 뒤 다시 요청해 주세요.'}
        async with sessions() as session, session.begin():
            current = await ProposalRepository(session).get(job_id, lock=True)
            if current.status == 'running':
                current.status, current.error, current.usage, current.updated_at = 'failed', error, usage, utcnow()
        return {'status': 'failed', 'proposalId': job_id}
    finally:
        if reranker:
            await reranker.aclose()
