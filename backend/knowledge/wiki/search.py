"""Wiki discovery service: bounded hybrid queries, ambiguity hints and index status."""
from sqlalchemy.exc import SQLAlchemyError
from ..core.errors import AppError
from ..indexing.embeddings import validate_vectors
from ..rag.ranking import optional_rerank
from .index_repository import WikiIndexRepository
from .policy import can_edit, require_edit, require_read, require_version
from .repository import WikiRepository
from .search_repository import WikiSearchRepository
from .search_dto import IndexStatus, NameAlternative, SearchResult, WikiSearchHit
from .service import page_view


class WikiSearchService:
    def __init__(self, sessions, settings, embedding_client, reranker=None):
        self.sessions, self.settings = sessions, settings
        self.embedding_client, self.reranker = embedding_client, reranker

    async def alternatives(self, principal, page_id):
        require_read(principal)
        async with self.sessions() as session:
            repo = WikiRepository(session)
            matches = await WikiSearchRepository(session).alternatives(page_id)
            return [NameAlternative(page=page_view(await repo.detail(pid), principal), matched_names=names)
                    for pid, names in matches]

    async def similar(self, principal, title, markdown='', *, exclude=None):
        # Transient draft text: not persisted or logged. Bound provider input.
        query = (title.strip() + '\n' + markdown[:3000]).strip()
        if not query:
            raise AppError(422, 'invalid_wiki_query', '제목 또는 본문을 입력해 주세요.')
        return await self.search(principal, query, limit=5, exclude=exclude, name_query=title)

    async def search(self, principal, query, *, limit=12, exclude=None, name_query=None):
        require_read(principal)
        profile = self.embedding_client.profile_id
        try:
            async with self.sessions() as session:
                available = await WikiSearchRepository(session).has_vectors(profile, exclude)
            vector, warnings, status = None, [], 'unavailable'
            if available:
                try:
                    response = await self.embedding_client.embed([query])
                    validate_vectors(response.vectors, 1)
                    vector, status = response.vectors[0], 'used'
                except Exception:
                    status = 'failed'
                    warnings.append('의미 검색 호출에 실패했습니다. 현재 결과는 키워드 검색이며 본문 열람·편집은 계속할 수 있습니다.')
            else:
                warnings.append('현재 임베딩 프로필로 준비된 위키 색인이 없습니다. 제목·별칭 및 준비된 키워드 결과를 표시합니다.')
            async with self.sessions() as session:
                candidates = await WikiSearchRepository(session).candidates(query, vector, profile,
                    exclude=exclude, name_query=name_query, limit=self.settings.retrieval_candidate_limit)
            ranked, reranking, extra = await optional_rerank(self.reranker, query, candidates)
            warnings.extend(extra)
            selected, seen = [], set()
            async with self.sessions() as session:
                repo = WikiRepository(session)
                for hit in ranked:
                    if hit['pageId'] in seen:
                        continue
                    row = await repo.detail(hit['pageId'])
                    if row[0].current_revision_id != hit['sourceRevisionId']:
                        warnings.append('검색 중 변경된 문서는 결과에서 제외했습니다. 다시 검색하면 최신 내용을 확인할 수 있습니다.')
                        continue
                    selected.append(WikiSearchHit(page=page_view(row, principal), revision_id=hit['sourceRevisionId'],
                        passage_id=hit['passageId'] if hit['hasPassage'] else None, locator=hit['locator'],
                        excerpt=hit.get('excerpt', hit['text'])[:1200], methods=hit['methods'], score=hit['score'], name_match=hit['nameMatch']))
                    seen.add(hit['pageId'])
                    if len(selected) >= limit:
                        break
            return SearchResult(items=selected, warnings=list(dict.fromkeys(warnings)), semantic_status=status,
                                embedding_profile=profile, reranking=reranking)
        except SQLAlchemyError as exc:
            raise AppError(503, 'wiki_search_failed', '위키 검색 저장소에 접근하지 못했습니다. 자료 없음과는 다른 오류입니다.', retryable=True) from exc

    async def status(self, principal, page_id):
        require_read(principal)
        profile = self.embedding_client.profile_id
        async with self.sessions() as session:
            page = await WikiRepository(session).get(page_id)
            repo = WikiIndexRepository(session)
            job = await repo.for_revision(page.current_revision_id)
            held = [p for p in await repo.passages(page.current_revision_id, all_passages=True) if p.excluded]
            state = {'pending': 'queued', 'running': 'processing', 'succeeded': 'ready'}.get(job.status, job.status) if job else 'not_indexed'
            if state == 'ready' and (page.indexed_revision_id != page.current_revision_id or job.profile_id != profile):
                state = 'profile_mismatch'
            elif state == 'ready' and held:
                state = 'partial'
            return IndexStatus(status=state, current_revision_id=page.current_revision_id,
                indexed_revision_id=page.indexed_revision_id, embedding_profile=job.profile_id if job else None,
                requested_profile=profile, job=None if job is None else {'id': job.id, 'status': job.status,
                    'attempts': job.attempts, 'progress': job.progress, 'error': job.error, 'updatedAt': job.updated_at.isoformat()},
                held_passages=[{'id': p.id, 'locator': p.locator, 'reason': p.exclusion_reason} for p in held],
                can_retry=can_edit(principal, page) and state in ('failed', 'not_indexed', 'profile_mismatch'))

    async def retry(self, principal, page_id, base_version):
        require_read(principal)
        async with self.sessions() as session, session.begin():
            page = await WikiRepository(session).get(page_id, lock=True)
            require_edit(principal, page)
            require_version(page, base_version)
            await WikiIndexRepository(session).retry(page, self.embedding_client.profile_id)
        return await self.status(principal, page_id)
