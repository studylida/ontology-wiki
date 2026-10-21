"""Section 3.6: Contextual Explainer Pipeline (인라인 문맥 맞춤 해설 파이프라인).

Implements:
1. Pre-computed Edge Caching (explainer:{parentId}:{perspectiveId}:{childId}).
2. Strict Prompt Guardrail: MUST begin with "현재 공정 맥락({parentName}):"
3. 3-Tier hybrid serving: L2 Cache -> On-demand LLM Gateway -> Deterministic fallback.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.cache import cache_manager
from backend.app.core.llm_gateway import llm_gateway
from backend.app.models.entities import ConceptModel, CausalEdgeModel
from backend.app.schemas.ontology import ContextualExplainerResponse

logger = logging.getLogger("explainer_agent")


class ExplainerAgent:
    async def get_explanation(
        self,
        child_id: str,
        parent_id: Optional[str],
        perspective_id: Optional[str],
        db: AsyncSession,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> ContextualExplainerResponse:
        parent_id = parent_id or "concept-tcb"
        perspective_id = perspective_id or "default"

        # 1. 캐시 확인
        cache_key = f"explainer:{parent_id}:{perspective_id}:{child_id}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return ContextualExplainerResponse(**cached)

        # 2. 개념 정보 로드
        child_concept = await db.get(ConceptModel, child_id)
        parent_concept = await db.get(ConceptModel, parent_id)

        child_name = child_concept.title if child_concept else child_id
        parent_name = parent_concept.title if parent_concept else parent_id

        # 3. 인과 관계 조회
        stmt = select(CausalEdgeModel).where(
            (
                (CausalEdgeModel.source_concept_id == parent_id) &
                (CausalEdgeModel.target_concept_id == child_id)
            ) | (
                (CausalEdgeModel.source_concept_id == child_id) &
                (CausalEdgeModel.target_concept_id == parent_id)
            )
        )
        edge = (await db.execute(stmt)).scalars().first()
        relation_type = edge.relation_type if edge else "part_of"

        # 4. LLM Gateway로 문맥 맞춤 해설 생성 시도
        system_instruction = (
            "당신은 반도체 공학 문맥 해설 어시스턴트입니다. "
            "장황한 사전적 정의를 금지하고, 반드시 '현재 공정 맥락({parentName}):'으로 시작하여 "
            "부모 공정에서 해당 자식 개념이 물리·화학적으로 어떤 역할을 하는지 1~2문장으로 압축 서술하세요."
        )
        prompt = (
            f"부모 공정: {parent_name} ({parent_id})\n"
            f"자식 개념: {child_name} ({child_id})\n"
            f"인과 관계: {relation_type}\n"
            f"맞춤 해설을 작성하세요."
        )

        llm_text = await llm_gateway.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            session_id=f"explainer-{parent_id}-{child_id}",
            gemini_key=gemini_key,
            openai_key=openai_key
        )

        # 프롬프트 가드레일 강제 확인
        guardrail_prefix = f"현재 공정 맥락({parent_name}):"
        evidence_ids = [edge.evidence_id] if (edge and edge.evidence_id) else ["E-01"]

        if llm_text and llm_text.startswith(guardrail_prefix):
            explanation_text = llm_text
        elif llm_text:
            explanation_text = f"{guardrail_prefix} {llm_text}"
        else:
            # 🌟 Tier 4 (Deterministic Zero-AI Ontology Fallback): 단일 진실 원천(DB) 기반 동적 합성
            if not child_concept:
                explanation_text = (
                    f"{guardrail_prefix} 해당 용어('{child_id}')는 온톨로지에 정식 등록되지 않은 미분류 용어입니다. "
                    f"{parent_name} 공정과의 상세 인과 메커니즘은 신규 검토 티켓 발급이 필요합니다."
                )
            elif edge and edge.mechanism_label:
                rel_desc_map = {
                    "causes": "직접적인 물리·화학적 인과를 유발하는",
                    "causes_defect": "공정 결함/불량을 유발하는",
                    "mitigates": "결함 및 공정 변동을 억제·완화하는",
                    "prevents": "물리적 한계 및 손상을 예방하는",
                    "alternative_to": "기술적 한계를 대체하거나 상호 경쟁하는 대안 공정",
                    "competes_with": "상호 경쟁 관계의 차세대 대안",
                    "part_of": "하위 구성 단위 공정/요소",
                    "depends_on": "선행 요구되거나 의존하는 핵심 요소",
                    "controls": "수율 및 품질을 제어하는 핵심 인자",
                }
                rel_korean = rel_desc_map.get(relation_type, f"'{relation_type}' 인과 연계")
                child_summary = f" ({child_concept.summary})" if child_concept.summary else ""
                explanation_text = (
                    f"{guardrail_prefix} {parent_name} 공정 맥락에서 {child_name}은(는) {rel_korean} 메커니즘({edge.mechanism_label})을 갖습니다.{child_summary}"
                )
            else:
                child_summary = f" ({child_concept.summary})" if child_concept.summary else ""
                explanation_text = (
                    f"{guardrail_prefix} {child_name} 개념은 온톨로지에 등록되어 있으나{child_summary}, "
                    f"{parent_name} 공정과의 구체적인 물리·화학적 인과 연계 메커니즘은 현재 검토 티켓을 통해 정밀 모델링 중입니다."
                )

        resp = ContextualExplainerResponse(
            childConceptId=child_id,
            childConceptName=child_name,
            parentConceptId=parent_id,
            parentConceptName=parent_name,
            relationType=relation_type,
            contextualExplanation=explanation_text,
            fallbackDefinition=child_concept.summary if child_concept else f"{child_name} 기본 정의",
            evidenceIds=evidence_ids
        )

        # 캐시에 저장 (5분 TTL)
        await cache_manager.set(cache_key, resp.model_dump(by_alias=True), ttl_seconds=300)
        return resp

    async def precompile_concept_explainers(self, concept_id: str, db: AsyncSession):
        """Pre-compiles explainers for all 1-hop connected concepts on ticket approval."""
        stmt = select(CausalEdgeModel).where(
            (CausalEdgeModel.source_concept_id == concept_id) |
            (CausalEdgeModel.target_concept_id == concept_id)
        )
        edges = (await db.execute(stmt)).scalars().all()
        for edge in edges:
            other_id = edge.target_concept_id if edge.source_concept_id == concept_id else edge.source_concept_id
            try:
                await self.get_explanation(child_id=other_id, parent_id=concept_id, perspective_id="default", db=db)
            except Exception as e:
                logger.warning(f"Failed to precompile explainer for {concept_id} -> {other_id}: {e}")


explainer_agent = ExplainerAgent()
