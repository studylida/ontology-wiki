"""One internal retrieval policy: candidates, optional rerank, companions and neighbors."""
from time import monotonic
from knowledge.core.errors import AppError
from knowledge.core.ids import new_id
from knowledge.documents.repository import DocumentRepository, select_ranked_hits
from .context import (conflict_companions, experiment_companions, prioritize_conflict_notes,
                      select_context, serialized_evidence)
from .entities import RetrievalRun
from .ranking import optional_rerank


def select_anchors(candidates, limit):
    ranked = select_ranked_hits(candidates, limit=limit)['hits']
    if any('rerankScore' in hit for hit in candidates):
        return ranked
    source = lambda hit: hit.get('lineageKey') or hit.get('documentId', hit['sourceRevisionId'])
    chosen = {hit['passageId'] for hit in ranked}
    for hit in candidates[:limit * 2]:
        if hit['passageId'] in chosen or any(source(item) == source(hit) for item in ranked):
            continue
        duplicate = next((item for item in reversed(ranked)
                          if sum(source(other) == source(item) for other in ranked) > 1), None)
        # Trade only near-tied fusion scores; do not displace a clearly stronger passage.
        if duplicate and duplicate.get('score', 0) > 0 and hit.get('score', 0) >= duplicate['score'] * .98:
            ranked.remove(duplicate)
            ranked.append(hit)
            chosen.remove(duplicate['passageId'])
            chosen.add(hit['passageId'])
    order = {hit['passageId']: i for i, hit in reversed(list(enumerate(candidates)))}
    return sorted(ranked, key=lambda hit: order[hit['passageId']])


class RAGService:
    def __init__(self, sessions, settings, embedding_client, reranker=None):
        self.sessions, self.settings = sessions, settings
        self.embedding_client, self.reranker = embedding_client, reranker

    async def retrieve(self, principal, conversation_id, question, history):
        started = monotonic()
        query = question[:4000]
        previous = next((m['content'] for m in reversed(history) if m['role'] == 'user'), None)
        if previous and len(question) < 300:
            query = previous[-1000:] + '\n후속 질문: ' + question
        async with self.sessions() as session:
            revisions = await DocumentRepository(session).resolve_snapshot(principal)
        candidates, evidence, warnings, usage, reranking = [], [], [], {}, {'status': 'disabled'}
        snapshot = None
        if revisions:
            response = await self.embedding_client.embed([query])
            usage = response.usage
            async with self.sessions() as session:
                repository = DocumentRepository(session)
                found = await repository.search_candidates(principal, response.vectors[0],
                    self.embedding_client.profile_id, query, revisions,
                    candidate_limit=self.settings.retrieval_candidate_limit)
            candidates = found['hits']
            warnings.extend(found.get('warnings', []))
            snapshot = found.get('indexSnapshotId')
            candidates, reranking, rerank_warnings = await optional_rerank(self.reranker, query, candidates)
            warnings.extend(rerank_warnings)
            selected = select_anchors(candidates, self.settings.retrieval_limit)
            companions = experiment_companions(candidates, selected)
            companions += conflict_companions(candidates, [*selected, *companions])
            anchors = prioritize_conflict_notes([*selected, *companions])
            async with self.sessions() as session:
                neighbors = await DocumentRepository(session).get_neighbors(
                    principal, [h['passageId'] for h in anchors], revisions)
            evidence = select_context([*anchors, *neighbors], self.settings.context_max_characters)
            if len({h['passageId'] for h in [*anchors, *neighbors]}) > len(evidence):
                warnings.append('문맥 예산 때문에 일부 후보 구간은 답변 모델에 전달하지 않았습니다.')
        if not evidence:
            warnings.append('현재 검색에서 사용할 사내 근거를 확보하지 못했습니다. 회사 관련 사실을 추측하지 않습니다.')
        result = {
            'status': 'found' if evidence else 'no_evidence', 'query': query,
            'embeddingProfile': self.embedding_client.profile_id, 'indexSnapshotId': snapshot,
            'sourceRevisionIds': sorted({h['sourceRevisionId'] for h in evidence}),
            'evidence': evidence, 'contextCharacters': len(serialized_evidence(evidence)),
            'candidates': [{k: h[k] for k in ('passageId', 'sourceRevisionId', 'score', 'cosineDistance', 'rerankScore', 'methods') if k in h}
                           for h in candidates],
            'reranking': reranking, 'warnings': warnings, 'usage': usage,
            'elapsedMs': round((monotonic() - started) * 1000, 2),
        }
        run_id = new_id('ret')
        async with self.sessions() as session, session.begin():
            # Recheck before preserving the context as usable evidence.
            active = await DocumentRepository(session).resolve_snapshot(principal, result['sourceRevisionIds'])
            if set(active) != set(result['sourceRevisionIds']):
                raise AppError(409, 'source_changed', '검색 중 문헌 상태가 변경되었습니다. 다시 질문해 주세요.', retryable=True)
            session.add(RetrievalRun(id=run_id, owner_id=principal.id, conversation_id=conversation_id,
                                     query_text=query, result=result))
        return run_id, result
