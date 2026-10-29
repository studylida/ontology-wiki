"""Shared lexical tokenization, reciprocal rank scoring and optional rerank fallback."""
import re


def query_terms(query):
    separated = re.sub(r'(?<=[^\W\d_가-힣])(?=[가-힣])', ' ', query)
    return list(dict.fromkeys(t.casefold() for t in re.findall(r'[\w\u2070-\u209f-]{2,}', separated)))[:16]


def rank_score(rank):
    return 1 / (60 + rank)


async def optional_rerank(reranker, query, hits):
    if reranker is None or not hits:
        return hits, {'status': 'disabled'}, []
    try:
        result = await reranker.rerank(query, hits)
        return result['hits'], {**{k: v for k, v in result.items() if k != 'hits'}, 'status': 'used'}, []
    except Exception as exc:
        return hits, {'status': 'fallback', 'code': getattr(exc, 'code', 'reranker_failed')}, [
            '선택적 재순위화가 실패하여 기본 검색 순위를 사용했습니다.']
