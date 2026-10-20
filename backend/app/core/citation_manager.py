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
    async def is_deprecation_intended(
        reason: Optional[str],
        missing_tags: Optional[List[str]] = None,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> bool:
        """사유(override_reason)의 자연어 문맥을 분석하여 공인 출처의 의도적 폐기/대체 의도인지 판별합니다.
        
        1단계: 빠른 결정 (Quick Rule) - 명시적 폐기/교체 키워드 존재 시 0ms 즉시 승인.
        2단계: Tier 1 초고속 AI(gpt-4o-mini) - 고정 키워드가 없더라도 자연어 문맥(예: '28nm 측정치는 3nm에서 무효')을 인과적으로 해석.
        """
        if not reason or not reason.strip():
            return False
        
        reason_clean = reason.strip().lower()
        FAST_KEYWORDS = {
            "폐기", "삭제", "제거", "deprecated", "구버전", "세대 교체",
            "호환 제외", "파기", "무효", "무효화", "대체됨", "만료", "퇴출", "배제"
        }
        if any(k in reason_clean for k in FAST_KEYWORDS):
            return True

        # 2단계: Tier 1 AI 문맥 의도 판별
        try:
            from backend.app.core.llm_gateway import llm_gateway
            prompt = (
                f"사용자가 반도체 위키 문서에서 기존 공인 출처/인용을 제외하면서 작성한 사유입니다:\n"
                f"사유: \"{reason}\"\n"
                f"제외 대상 출처 태그: {missing_tags or '기존 출처'}\n\n"
                "질문: 위 사유가 해당 기존 출처나 측정값의 '의도적 폐기, 대체, 유효성 만료, 공정 세대 교체로 인한 배제'를 의미합니까?\n"
                "반드시 단 한 단어로만 답변하세요: YES 또는 NO"
            )
            resp = await llm_gateway.generate_text(
                prompt=prompt,
                system_instruction="You are a strict compliance auditor determining if an engineering note expresses intent to deprecate or replace an old reference. Reply only YES or NO.",
                model_tier="tier1_fast",
                temperature=0.0,
                max_tokens=10,
                gemini_key=gemini_key,
                openai_key=openai_key
            )
            if resp and "yes" in resp.strip().lower():
                logger.info(f"AI classified reason '{reason}' as intentional deprecation (YES).")
                return True
        except Exception as e:
            logger.warning(f"Tier 1 AI deprecation check fallback: {e}")

        return False

    @staticmethod
    async def validate_and_restore(
        original_text: str,
        edited_text: str,
        allow_citation_deletion: bool = False,
        deprecated_citations: Optional[List[str]] = None,
        override_reason: Optional[str] = None,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> Tuple[str, List[str], List[str]]:
        """사용자가 직접 편집 중 누락된 공인 출처 각주를 감지하고 복원 또는 공식 폐기를 처리합니다.
        
        복원 및 공식 폐기(Deprecation) 거버넌스 원칙 (대안 1 + 대안 2 결합형):
        1. 명시적 플래그 및 태그: allow_citation_deletion=True이거나 deprecated_citations에 포함된 태그는 즉시 폐기 인가.
        2. AI 자연어 사유 분석: 강제 키워드가 없더라도 작성된 사유의 문맥이 의도적 폐기/대체로 판별되면 공식 폐기 인가.
        3. 단순 실수 누락: 위 사유가 없는 경우, 원문의 핵심 근거 문장과 태그를 안전하게 자동 복원.

        Returns:
            Tuple[str, List[str], List[str]]: (처리된 본문, 복원된 태그 목록, 공식 폐기 인가된 태그 목록)
        """
        orig_citations = set(EvidenceCitationManager.parse_citations(original_text))
        edited_citations = set(EvidenceCitationManager.parse_citations(edited_text))

        missing_citations = orig_citations - edited_citations
        if not missing_citations:
            return edited_text, [], []

        sorted_missing = sorted(list(missing_citations))
        explicit_deprecated_set = set(deprecated_citations or [])

        # 사유 문맥을 통한 의도적 폐기 여부 판별
        reason_is_deprecation = await EvidenceCitationManager.is_deprecation_intended(
            override_reason,
            missing_tags=sorted_missing,
            gemini_key=gemini_key,
            openai_key=openai_key
        )

        officially_deprecated: List[str] = []
        tags_to_restore: List[str] = []

        for tag in sorted_missing:
            if allow_citation_deletion or (tag in explicit_deprecated_set) or reason_is_deprecation:
                officially_deprecated.append(tag)
            else:
                tags_to_restore.append(tag)

        if officially_deprecated:
            logger.info(
                f"Official citation deprecation authorized for tags: {officially_deprecated}. "
                f"(Reason: {override_reason}, ExplicitFlag: {allow_citation_deletion})"
            )

        if not tags_to_restore:
            return edited_text, [], officially_deprecated

        orig_sentences = EvidenceCitationManager.extract_citation_sentences(original_text)
        restoration_blocks: List[str] = []
        simple_tag_restores: List[str] = []

        for tag in tags_to_restore:
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
            f"Detected missing citations in human edits: {tags_to_restore}. "
            f"Automatically restored (Sentences: {len(restoration_blocks)}, Tags: {len(simple_tag_restores)})."
        )
        return restored_text, tags_to_restore, officially_deprecated

    @staticmethod
    def validate_and_restore_sync(
        original_text: str,
        edited_text: str,
        allow_citation_deletion: bool = False,
        override_reason: Optional[str] = None
    ) -> Tuple[str, List[str], List[str]]:
        """동기 호출용 래퍼 (AI 비동기 호출 없이 순수 규칙 기반으로 즉시 판별)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                reason_clean = (override_reason or "").lower()
                is_explicit = allow_citation_deletion or any(
                    k in reason_clean for k in ["폐기", "삭제", "제거", "deprecated", "구버전", "세대 교체", "호환 제외"]
                )
                orig_c = set(EvidenceCitationManager.parse_citations(original_text))
                edit_c = set(EvidenceCitationManager.parse_citations(edited_text))
                missing = sorted(list(orig_c - edit_c))
                if not missing:
                    return edited_text, [], []
                if is_explicit:
                    return edited_text, [], missing
                return edited_text + " " + " ".join(f"[{t}]" for t in missing), missing, []
            return loop.run_until_complete(
                EvidenceCitationManager.validate_and_restore(
                    original_text, edited_text, allow_citation_deletion=allow_citation_deletion, override_reason=override_reason
                )
            )
        except Exception:
            return edited_text, [], []

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
