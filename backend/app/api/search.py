"""Search API Router for Ontology Wiki.

Provides /api/v1/search/spotlight endpoint for Cmd+K search modal with low-latency ranking.
"""
from typing import Optional, List, Dict, Any, Tuple
import re
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.core.cache import cache_manager
from backend.app.models.entities import ConceptModel
from backend.app.schemas.search import (
    SpotlightSearchResponse,
    SpotlightSearchResult
)

logger = logging.getLogger("ontology_wiki.search")

router = APIRouter(prefix="/search", tags=["Search"])


def normalize_term(s: str) -> str:
    """반도체 특수 약어(MR-MUF, High-NA, TC-NCF 등) 매칭을 위해 하이픈/공백/특수문자 제거 정규화."""
    return re.sub(r"[\s\-_/().,]", "", s.lower())


def extract_highlight(text: str, query: str, context_len: int = 40) -> Optional[str]:
    """검색어 매칭 지점 전후 문맥을 발췌하여 하이라이트 스니펫을 생성."""
    if not text or not query:
        return None
    idx = text.lower().find(query.lower())
    if idx == -1:
        # 정규화된 위치 검색
        return text[:context_len * 2] if len(text) > context_len * 2 else text
    start = max(0, idx - context_len)
    end = min(len(text), idx + len(query) + context_len)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def score_concept(
    c: ConceptModel,
    q: str
) -> Tuple[float, str, Optional[str]]:
    """개념에 대해 검색어 관련도 점수(0~100)와 매칭 축, 하이라이트를 산출."""
    q_raw = q.lower()
    q_norm = normalize_term(q)
    title_lower = c.title.lower()
    title_norm = normalize_term(c.title)
    eng_lower = c.eng_name.lower()
    eng_norm = normalize_term(c.eng_name)
    aliases = c.aliases if isinstance(c.aliases, list) else []
    cat_lower = c.process_category.lower()
    summary_lower = c.summary.lower() if c.summary else ""
    purpose_lower = c.purpose.lower() if c.purpose else ""

    # 1. Exact Title Match (원문 또는 정규화)
    if title_lower == q_raw or (len(q_norm) >= 2 and title_norm == q_norm):
        return 100.0, "title", c.title

    # 2. Exact Alias Match (약어 정규화 포함: 예: mrmuf -> MR-MUF)
    for a in aliases:
        if isinstance(a, str):
            a_norm = normalize_term(a)
            if a.lower() == q_raw or (len(q_norm) >= 2 and a_norm == q_norm):
                return 90.0, "alias", f"동의어/약어 일치: {a}"

    # 3. Exact English Name Match
    if eng_lower == q_raw or (len(q_norm) >= 2 and eng_norm == q_norm):
        return 85.0, "eng_name", c.eng_name

    # 4. Title Starts With Query
    if title_lower.startswith(q):
        return 80.0, "title", extract_highlight(c.title, q)

    # 5. Title Contains Query
    if q in title_lower:
        return 65.0, "title", extract_highlight(c.title, q)

    # 6. Alias Starts With Query
    for a in aliases:
        if isinstance(a, str) and a.lower().startswith(q):
            return 60.0, "alias", f"동의어 일치: {a}"

    # 7. Alias Contains Query
    for a in aliases:
        if isinstance(a, str) and q in a.lower():
            return 50.0, "alias", f"동의어 포함: {a}"

    # 8. English Name Contains Query
    if q in eng_lower:
        return 45.0, "eng_name", extract_highlight(c.eng_name, q)

    # 9. Process Category Match
    if q in cat_lower:
        return 35.0, "category", f"공정 분류: {c.process_category}"

    # 10. Summary Contains Query
    if q in summary_lower:
        return 20.0, "summary", extract_highlight(c.summary, q)

    # 11. Purpose Contains Query
    if q in purpose_lower:
        return 15.0, "summary", extract_highlight(c.purpose, q)

    return 0.0, "default", None


@router.get(
    "/spotlight",
    response_model=SpotlightSearchResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="전역 Cmd+K Spotlight 검색 API",
    description="개념명, 동의어, 약어, 영문명, 공정 분류, 본문 요약을 초저지연 스코어링하여 프론트엔드 모달에 서빙합니다."
)
async def search_spotlight(
    q: Optional[str] = Query(default="", description="검색 키워드 (공정명, 약어, 개념 등)"),
    facet: Optional[str] = Query(default=None, description="도메인 패싯 필터 (unit_process, device, operations, materials_infra)"),
    process_category: Optional[str] = Query(default=None, description="공정 분류 필터 (예: 식각 공정)"),
    limit: int = Query(default=10, ge=1, le=50, description="최대 반환 개수"),
    db: AsyncSession = Depends(get_db)
):
    clean_query = (q or "").strip()
    cache_key = f"spotlight:{clean_query.lower()}:{facet or ''}:{process_category or ''}:{limit}"

    # 1. 캐시 확인
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return SpotlightSearchResponse(**cached_data)

    # 2. 총 인덱싱된 개념 수 조회
    total_indexed_stmt = select(func.count(ConceptModel.id))
    total_indexed = (await db.execute(total_indexed_stmt)).scalar() or 0

    # 3. 개념 목록 쿼리
    stmt = select(ConceptModel)
    if facet:
        stmt = stmt.where(ConceptModel.domain_facet == facet)
    if process_category:
        stmt = stmt.where(ConceptModel.process_category == process_category)

    concepts = (await db.execute(stmt)).scalars().all()

    # 4. 스코어링 & 필터링
    results: List[SpotlightSearchResult] = []

    if not clean_query:
        # 빈 검색어: Scale level 및 제목 오름차순으로 기본 상위 추천 항목 반환
        sorted_concepts = sorted(concepts, key=lambda c: (c.scale_level, c.title))
        for c in sorted_concepts[:limit]:
            results.append(
                SpotlightSearchResult(
                    id=c.id,
                    title=c.title,
                    eng_name=c.eng_name,
                    aliases=c.aliases if isinstance(c.aliases, list) else [],
                    process_category=c.process_category,
                    process_name=c.process_category,
                    domain_facet=c.domain_facet,
                    scale_level=c.scale_level,
                    scale_name=c.scale_name,
                    summary=c.summary,
                    match_type="default",
                    score=1.0,
                    highlight=None
                )
            )
        response_dto = SpotlightSearchResponse(
            query=clean_query,
            total_indexed=total_indexed,
            total_matches=len(concepts),
            results=results
        )
    else:
        scored_items = []
        for c in concepts:
            score, match_type, highlight = score_concept(c, clean_query)
            if score > 0.0:
                scored_items.append((score, match_type, highlight, c))

        # 정렬: 점수 내림차순 -> 스케일 레벨 오름차순 -> 제목 오름차순
        scored_items.sort(key=lambda item: (-item[0], item[3].scale_level, item[3].title))

        for score, match_type, highlight, c in scored_items[:limit]:
            results.append(
                SpotlightSearchResult(
                    id=c.id,
                    title=c.title,
                    eng_name=c.eng_name,
                    aliases=c.aliases if isinstance(c.aliases, list) else [],
                    process_category=c.process_category,
                    process_name=c.process_category,
                    domain_facet=c.domain_facet,
                    scale_level=c.scale_level,
                    scale_name=c.scale_name,
                    summary=c.summary,
                    match_type=match_type,
                    score=score,
                    highlight=highlight
                )
            )

        response_dto = SpotlightSearchResponse(
            query=clean_query,
            total_indexed=total_indexed,
            total_matches=len(scored_items),
            results=results
        )

    # 5. 응답 캐싱 (TTL: 60초)
    await cache_manager.set(cache_key, response_dto.model_dump(by_alias=True), ttl_seconds=60)
    return response_dto
