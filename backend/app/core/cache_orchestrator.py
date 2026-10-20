"""Section 6.4: Cache Orchestrator (전 도메인 캐시 일괄 무효화 오케스트레이터).

Centralizes multi-domain cache invalidation rules to prevent Stale Cache and version mismatch:
1. Invalidates wiki detail, 2-hop subgraph, contextual explainer, and spotlight caches on approval.
2. Eliminates hardcoded cache key string typos across services.
"""
import logging
from typing import List
from backend.app.core.cache import cache_manager

logger = logging.getLogger("cache_orchestrator")


class CacheOrchestrator:
    """전 도메인 캐시 일괄 무효화 오케스트레이터."""

    @staticmethod
    async def invalidate_concept_domain(concept_id: str) -> int:
        """위키 개정 승인 또는 개념 수정 시 연계된 모든 상위/하위 캐시를 0ms 원자적 일괄 소거합니다.

        소거 대상:
        1. 위키 본문 상세 캐시: `concept:detail:{concept_id}`
        2. 2-Hop 인과 서브그래프 캐시: `concept:subgraph:{concept_id}:*`
        3. 인라인 용어 설명 캐시: `concept:explainer:{concept_id}:*`
        4. 전역 스포트라이트 검색 캐시: `spotlight:*`
        5. 챗봇 컨텍스트 캐시: `chatbot:context:*`

        Returns:
            int: 무효화된 총 캐시 키 개수
        """
        if not concept_id:
            return 0

        total_invalidated = 0
        try:
            # 1. 단건 상세 캐시 제거
            if await cache_manager.delete(f"concept:detail:{concept_id}"):
                total_invalidated += 1

            # 2. 연관 서브그래프 및 인라인 팝업 접두사 캐시 제거
            total_invalidated += await cache_manager.delete_prefix(f"concept:subgraph:{concept_id}:")
            total_invalidated += await cache_manager.delete_prefix(f"concept:explainer:{concept_id}:")

            # 3. 전역 스포트라이트 및 챗봇 컨텍스트 캐시 일괄 제거
            total_invalidated += await cache_manager.delete_prefix("spotlight:")
            total_invalidated += await cache_manager.delete_prefix("chatbot:context:")

            logger.info(
                f"[CacheOrchestrator] Successfully invalidated all domain caches "
                f"for concept '{concept_id}'. (Total purged keys: {total_invalidated})"
            )
        except Exception as e:
            logger.error(f"[CacheOrchestrator] Failed during cache invalidation for '{concept_id}': {e}", exc_info=True)

        return total_invalidated

    @staticmethod
    async def invalidate_spotlight() -> int:
        """스포트라이트 검색 캐시를 전역 무효화합니다."""
        return await cache_manager.delete_prefix("spotlight:")


cache_orchestrator = CacheOrchestrator()
