"""Wiki preprocessing/index orchestration; no content edits or generation calls."""
import logging
from ..core.errors import AppError
from ..core.ids import utcnow
from ..documents.parsing import digest, segment
from ..indexing.dto import IndexUnit
from ..indexing.embeddings import embed_uncached
from ..indexing.repository import EmbeddingCache
from .index_repository import WikiIndexRepository


def prepare_wiki(revision):
    """Reuse the source-preserving Markdown splitter. Never index audit/source-note fields."""
    prefix = f'위키: {revision.title}\n뜻: {revision.meaning}\n별칭: {", ".join(revision.aliases)}'
    records = []
    for p in segment(revision.markdown, revision.title):
        embedded = f'{prefix}\n절: {p.locator}\n{p.text}'
        oversized = len(embedded.encode('utf-8')) > 7000
        records.append(dict(ordinal=p.ordinal, text=p.text, locator=p.locator,
            start_offset=p.start_offset, end_offset=p.end_offset, embedding_text=embedded,
            input_hash=digest(embedded), excluded=p.excluded or oversized,
            exclusion_reason=p.exclusion_reason or ('긴 문단 또는 표의 분할 검토 필요' if oversized else None)))
    return records


async def recover_wiki_jobs(sessions):
    async with sessions() as session:
        ids = await WikiIndexRepository(session).running_ids()
    for job_id in ids:
        async with sessions() as session, session.begin():
            repo = WikiIndexRepository(session)
            page, revision, job = await repo.locked(job_id)
            if repo.valid(page, revision, job):
                job.status, job.updated_at = 'failed', utcnow()
                job.error = {'code': 'worker_interrupted', 'message': '이전 작업자가 종료되었습니다. 색인을 재시도하세요.', 'retryable': True}


async def process_wiki_index_job(sessions, settings, job_id, embedding_client=None):
    phase = 'parsing'
    try:
        async with sessions() as session, session.begin():
            repo = WikiIndexRepository(session)
            page, revision, job = await repo.locked(job_id)
            if not repo.valid(page, revision, job):
                return {'jobId': job.id, 'kind': 'wiki_index', 'status': job.status}
            job.progress, job.updated_at = {'phase': phase}, utcnow()
            if not await repo.has_passages(revision.id):
                await repo.store_passages(revision.id, prepare_wiki(revision))
            passages = await repo.passages(revision.id, all_passages=True)
            held = sum(p.excluded for p in passages)
            units = [IndexUnit(p.id, p.revision_id, p.embedding_text, p.input_hash, 'wiki_passage')
                     for p in passages if not p.excluded]
        if not units:
            raise AppError(422, 'no_indexable_passages', '사용 가능한 본문이 없습니다. 보류 구간이나 편집 기록을 확인하세요.')
        phase = 'embedding'
        if embedding_client is None:
            from ..integrations.providers import get_embedding_client
            embedding_client = get_embedding_client(settings)
        profile, embedded, reused = embedding_client.profile_id, 0, 0
        for offset in range(0, len(units), 32):
            batch = units[offset:offset + 32]
            async with sessions() as session, session.begin():
                repo = WikiIndexRepository(session)
                page, revision, job = await repo.locked(job_id)
                if not repo.valid(page, revision, job):
                    return {'jobId': job.id, 'kind': 'wiki_index', 'status': job.status}
                cached = await EmbeddingCache(session).lookup(profile, [u.input_hash for u in batch])
                job.progress = {'phase': phase, 'processed': offset, 'total': len(units), 'held': held}
                job.updated_at = utcnow()
            # No page/job/database lock crosses provider I/O.
            vectors, usage = await embed_uncached(embedding_client, batch, cached)
            async with sessions() as session, session.begin():
                repo = WikiIndexRepository(session)
                page, revision, job = await repo.locked(job_id)
                if usage is not None:
                    job.usage = {'calls': [*(job.usage or {}).get('calls', []), usage]}
                if not repo.valid(page, revision, job):
                    return {'jobId': job.id, 'kind': 'wiki_index', 'status': job.status}
                cached.update(await EmbeddingCache(session).store(profile, vectors))
                await repo.attach(profile, batch, cached)
                embedded += len(vectors); reused += len(batch) - len(vectors)
                job.progress = {'phase': phase, 'processed': offset + len(batch), 'total': len(units),
                                'embedded': embedded, 'reused': reused, 'held': held}
                job.updated_at = utcnow()
        phase = 'activation'
        async with sessions() as session, session.begin():
            repo = WikiIndexRepository(session)
            page, revision, job = await repo.locked(job_id)
            if not repo.valid(page, revision, job):
                return {'jobId': job.id, 'kind': 'wiki_index', 'status': job.status}
            if await repo.indexed_count(profile, units) != len(units):
                raise AppError(409, 'incomplete_index', '유효 구간의 색인이 완료되지 않았습니다.')
            page.indexed_revision_id = revision.id
            job.status, job.profile_id, job.error, job.updated_at = 'succeeded', profile, None, utcnow()
            job.progress = {**job.progress, 'phase': 'complete'}
        return {'jobId': job_id, 'kind': 'wiki_index', 'status': 'succeeded', 'indexedPassages': len(units), 'heldPassages': held}
    except Exception as exc:
        error = exc.public() if isinstance(exc, AppError) else {
            'code': 'wiki_index_failed', 'message': '위키 색인에 실패했습니다. 본문은 보존되어 있습니다.', 'retryable': True}
        logging.getLogger('knowledge.worker').warning('wiki_index_failed job=%s phase=%s type=%s', job_id, phase, type(exc).__name__)
        async with sessions() as session, session.begin():
            repo = WikiIndexRepository(session)
            page, revision, job = await repo.locked(job_id)
            if repo.valid(page, revision, job):
                job.status, job.error, job.updated_at = 'failed', {**error, 'phase': phase}, utcnow()
                if getattr(exc, 'usage', None):
                    job.usage = {'calls': [*(job.usage or {}).get('calls', []), exc.usage]}
            return {'jobId': job.id, 'kind': 'wiki_index', 'status': job.status, 'error': job.error}
