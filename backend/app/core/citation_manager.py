"""Section 6.2: Evidence Citation Manager (공인 출처 각주 총괄 매니저).

Unified manager for handling public evidence citations across Tab 1, Tab 3, Tab 4, and Chatbot:
1. Regex extraction of citation anchors (e.g. [E-01], [E-02]).
2. Immutability validation and automatic restoration of accidentally deleted citations.
3. Promotion pipeline from research feed to official 사내 출처 마스터 (evidence_sources).
"""
import re
import logging
from typing import List, Set, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import EvidenceSourceModel, ResearchEvidenceFeedModel

logger = logging.getLogger("citation_manager")

CITATION_REGEX = re.compile(r"\[E-(\d+)\]", re.IGNORECASE)


class EvidenceCitationManager:
    """전 도메인 공인 출처 각주 파싱, 불변성 보존 및 자동 복원 총괄 엔진."""

    @staticmethod
    def parse_citations(text: str) -> List[str]:
        """본문 텍스트 내에서 [E-01], [E-02] 등 모든 공인 출처 각주 태그를 고유 추출합니다."""
        if not text:
            return []
        matches = CITATION_REGEX.findall(text)
        # 01 -> E-01 형태로 표준화
        tags: Set[str] = {f"E-{int(m):02d}" for m in matches}
        return sorted(list(tags))

    @staticmethod
    def validate_and_restore(original_text: str, edited_text: str) -> tuple[str, List[str]]:
        """사용자가 직접 편집 중 실수로 삭제한 공인 출처 각주를 감지하고 문장 끝에 자동 복원합니다.

        Returns:
            tuple[str, List[str]]: (복원된 본문 텍스트, 복원된 누락 출처 태그 목록)
        """
        orig_citations = set(EvidenceCitationManager.parse_citations(original_text))
        edited_citations = set(EvidenceCitationManager.parse_citations(edited_text))

        missing_citations = orig_citations - edited_citations
        if not missing_citations:
            return edited_text, []

        sorted_missing = sorted(list(missing_citations))
        restoration_suffix = " " + " ".join([f"[{tag}]" for tag in sorted_missing])
        restored_text = f"{edited_text.rstrip()}{restoration_suffix}"

        logger.warning(
            f"Detected missing citations in human edits: {sorted_missing}. "
            f"Automatically restored to protect public evidence immutability."
        )
        return restored_text, sorted_missing

    @staticmethod
    async def promote_to_evidence_source(
        feed_id: int,
        db: AsyncSession
    ) -> Optional[str]:
        """외부 문헌 조사 증빙 피드(research_evidence_feeds)를 사내 공식 출처 마스터(evidence_sources)로 승격합니다.

        Returns:
            Optional[str]: 발급된 공식 출처 ID (예: 'E-05')
        """
        feed = await db.get(ResearchEvidenceFeedModel, feed_id)
        if not feed:
            logger.error(f"Cannot promote feed {feed_id}: record not found.")
            return None

        if feed.promoted_evidence_id:
            logger.info(f"Feed {feed_id} already promoted as {feed.promoted_evidence_id}.")
            return feed.promoted_evidence_id

        # 차기 E-xx 고유 번호 채번
        stmt = select(func.count(EvidenceSourceModel.id))
        total_sources = (await db.execute(stmt)).scalar() or 0
        new_evidence_id = f"E-{total_sources + 1:02d}"

        new_source = EvidenceSourceModel(
            id=new_evidence_id,
            source_name=feed.source_name,
            source_type="whitepaper" if "백서" in feed.source_name or "Architecture" in feed.source_name else "paper",
            publisher=feed.publisher,
            published_date=feed.published_date,
            quote=feed.quote,
            section_context=f"외부 문헌 조사실 발굴 채택 문헌 (세션: {feed.session_id})",
            relevance_score=1.00,
            external_url=feed.external_url,
            url_label=f"{feed.publisher} 공식 열람 원문",
            credibility_tier=feed.credibility_tier,
            referenced_concepts=[]
        )
        db.add(new_source)

        # 피드에 승격된 ID 연결
        feed.promoted_evidence_id = new_evidence_id
        await db.commit()
        await db.refresh(feed)

        logger.info(f"Feed {feed_id} successfully promoted to official evidence {new_evidence_id}.")
        return new_evidence_id


citation_manager = EvidenceCitationManager()
