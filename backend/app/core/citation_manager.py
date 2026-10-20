"""Section 6.2: Evidence Citation Manager (공인 출처 각주 총괄 매니저).

Unified manager for handling public evidence citations across Tab 1, Tab 3, Tab 4, and Chatbot:
1. Regex extraction of citation anchors (e.g. [E-01], [E-02]).
2. Immutability validation and automatic restoration of accidentally deleted citations.
3. Promotion pipeline from research feed to official 사내 출처 마스터 (evidence_sources).
"""
import re
import logging
from typing import List, Set, Optional, Tuple, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import EvidenceSourceModel, ResearchSessionModel

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
        tags: Set[str] = {f"E-{int(m):02d}" for m in matches}
        return sorted(list(tags))

    @staticmethod
    def extract_citation_sentences(text: str) -> Dict[str, str]:
        """텍스트를 문장 단위로 분리하여 각 출처 태그([E-xx])가 포함된 원문 문장을 매핑합니다."""
        if not text:
            return {}
        # 문장 분리 (마침표, 개행 등)
        raw_sentences = re.split(r"(?<=[.!?\n])\s+", text)
        tag_to_sentence: Dict[str, str] = {}
        for s in raw_sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            tags = EvidenceCitationManager.parse_citations(s_clean)
            for t in tags:
                if t not in tag_to_sentence:
                    tag_to_sentence[t] = s_clean
        return tag_to_sentence

    @staticmethod
    def validate_and_restore(
        original_text: str,
        edited_text: str,
        allow_citation_deletion: bool = False,
        override_reason: str = ""
    ) -> Tuple[str, List[str], bool]:
        """사용자가 직접 편집 중 누락된 공인 출처 각주를 감지하고 복원 여부를 판단합니다.
        
        복원 원칙:
        1. 의도적 폐기(Deprecation) 인가:
           사용자가 allow_citation_deletion=True로 명시했거나, 거버넌스 사유(override_reason)에
           '폐기', '삭제', '구버전', '구 규격', '세대 교체', 'deprecated' 등의 사유를 기재한 경우
           ➔ 강제 복원을 수행하지 않고 깔끔하게 삭제 인가 (is_deprecated=True 반환).
        2. 단순 실수 누락:
           - 단순 태그만 삭제된 경우: 편집문 끝에 태그 복원 주입.
           - 출처 문장 자체가 통째로 삭제된 경우:
             원문의 핵심 근거 문장 자체를 '[공인 출처 인용 근거 보존] 원문장 [E-xx]' 형태로 복원하여
             공학적 데이터와 출처 문맥이 영구 소실되는 것을 원천 방어.

        Returns:
            Tuple[str, List[str], bool]: (최종 본문, 복원된 태그 목록, 출처 공식 폐기 여부)
        """
        orig_citations = set(EvidenceCitationManager.parse_citations(original_text))
        edited_citations = set(EvidenceCitationManager.parse_citations(edited_text))

        missing_citations = orig_citations - edited_citations
        if not missing_citations:
            return edited_text, [], False

        sorted_missing = sorted(list(missing_citations))

        # 🌟 의도적 폐기(Deprecation) 감지
        deprecation_keywords = ["폐기", "삭제", "구버전", "구 규격", "세대 교체", "deprecated", "대체"]
        is_intentional_deprecation = (
            allow_citation_deletion or
            any(k in (override_reason or "").lower() for k in deprecation_keywords)
        )

        if is_intentional_deprecation:
            logger.info(
                f"Citations {sorted_missing} intentionally deprecated with reason: '{override_reason}'. "
                f"Permitting deletion without forced restoration."
            )
            return edited_text, sorted_missing, True

        # 실수 누락 복원 처리
        orig_sentences = EvidenceCitationManager.extract_citation_sentences(original_text)

        restoration_blocks: List[str] = []
        simple_tag_restores: List[str] = []

        for tag in sorted_missing:
            orig_sentence = orig_sentences.get(tag)
            if orig_sentence:
                clean_orig_sentence = re.sub(r"\[E-\d+\]", "", orig_sentence).strip()
                words = [w for w in clean_orig_sentence.split() if len(w) >= 2]
                match_count = sum(1 for w in words if w in edited_text)
                is_sentence_deleted = (len(words) > 0 and (match_count / len(words)) < 0.4)

                if is_sentence_deleted:
                    restoration_blocks.append(f"[공인 출처 인용 근거 보존]: \"{clean_orig_sentence}\" [{tag}]")
                else:
                    simple_tag_restores.append(f"[{tag}]")
            else:
                simple_tag_restores.append(f"[{tag}]")

        restored_text = edited_text.rstrip()
        if simple_tag_restores:
            restored_text += " " + " ".join(simple_tag_restores)
        if restoration_blocks:
            restored_text += "\n\n" + "\n".join(restoration_blocks)

        logger.warning(
            f"Detected missing citations in human edits: {sorted_missing}. "
            f"Automatically restored (Sentences: {len(restoration_blocks)}, Tags: {len(simple_tag_restores)})."
        )
        return restored_text, sorted_missing, False

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
