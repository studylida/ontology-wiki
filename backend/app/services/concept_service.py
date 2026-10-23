"""[계층 3] Concept Service Layer.

Pure Business Logic Layer for Ontology Concepts, Enriched Relations, and Multi-Scale Ladder.
Coordinates ConceptRepository, AccessControl, L3 Masking, and DTO Assembly.
"""
from typing import Dict, List, Optional, Set, Any
from hashlib import sha256
import json
from urllib.parse import quote

from backend.app.core.cache import cache_manager
from backend.app.services.comparison_service import public_evidence
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import UserModel, ConceptModel, CausalEdgeModel
from backend.app.repositories.concept_repo import concept_repo
from backend.app.services.case_explanation_service import case_explanation_service
from backend.app.services.auth_service import AccessControlService
from backend.app.core.security import mask_tier3_perspective
from backend.app.schemas.ontology import (
    ConceptDetailResponse,
    PerspectiveCaseDTO,
    ContextualExplanationDTO,
    EnrichedRelationsDTO,
    EnrichedRelationItemDTO,
    ScaleLadderStepDTO,
    CompensatingParamSchema
)
from backend.app.schemas.ontology import CausalSubgraphResponse


class ContextualExplanationNotFound(LookupError):
    pass


class ContextualExplanationRestricted(PermissionError):
    pass


class ContextualExplanationUnavailable(RuntimeError):
    pass


class ConceptService:
    """Domain business service for ontology concept details and relation enrichment."""

    async def get_contextual_explanation(self, concept_id, selected_text, selection_context, session,
                                         gemini_key=None, openai_key=None):
        parent = await concept_repo.get_by_id(session, concept_id)
        if not parent:
            raise ContextualExplanationNotFound("설명할 위키를 찾을 수 없습니다.")
        # Always use the existing public projection, even when the caller can read L3.
        perspectives = await self.masked_perspectives(parent, session)

        def fragments(value):
            if isinstance(value, str):
                return [value]
            if isinstance(value, dict):
                return [text for item in value.values() for text in fragments(item)]
            if isinstance(value, list):
                return [text for item in value for text in fragments(item)]
            return [str(value)] if value is not None else []

        visible = fragments(dict(title=parent.title, engName=parent.eng_name, aliases=parent.aliases,
            summary=parent.summary, purpose=parent.purpose, principles=parent.principles,
            limitations=parent.limitations, perspectives=[case.model_dump(by_alias=True) for case in perspectives]))
        masked_ids = {case.id for case in perspectives if case.isMasked}
        restricted = fragments([dict(context=case.context_narrative, caution=case.caution,
            specifications=case.specifications) for case in parent.perspectives if case.id in masked_ids])
        private_only = [item for item in restricted if item and not any(item in public for public in visible)]
        needle = selected_text.strip()
        if needle and not any(needle in item for item in visible) and any(
                needle in item or item in needle for item in private_only):
            raise ContextualExplanationRestricted("비공개 내용은 문맥 해설에 사용할 수 없습니다.")
        context = selection_context if selection_context and any(selection_context in item for item in visible) else ""

        concepts = await concept_repo.get_all_concepts(session)
        matches = [concept for concept in concepts if selected_text.casefold() in
            {name.casefold() for name in [concept.id, concept.title, concept.eng_name, *(concept.aliases or [])]
             if isinstance(name, str)}]
        child = matches[0] if len(matches) == 1 else None
        edges = [edge for edge in await concept_repo.get_causal_edges_for_concept(session, parent.id)
            if child and child.id in (edge.source_concept_id, edge.target_concept_id)]
        evidences = [item for item in await concept_repo.get_case_evidences(session,
            list({edge.evidence_id for edge in edges if edge.evidence_id})) if public_evidence(item)]
        evidence_ids = {item.id for item in evidences}
        relations = [dict(source=edge.source_concept_id, target=edge.target_concept_id,
            type=edge.relation_type, explanation=edge.mechanism_label) for edge in edges
            if not edge.evidence_id or edge.evidence_id in evidence_ids]
        public_input = dict(selectedText=selected_text, selectionContext=context,
            wiki=dict(title=parent.title, summary=parent.summary, purpose=parent.purpose),
            registeredDefinition=child.summary if child else None, relations=relations,
            evidences=[dict(id=item.id, quote=item.quote) for item in evidences])
        signature = sha256(json.dumps(public_input, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        cache_key = f"concept:explainer:{parent.id}:context-v1:{signature}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return ContextualExplanationDTO(**cached).model_copy(update={"cached": True})
        from backend.app.agents.explainer_agent import explainer_agent
        try:
            explanation = await explainer_agent.get_explanation(public_input, session_id=f"popover-{signature}",
                gemini_key=gemini_key, openai_key=openai_key)
        except Exception as error:
            raise ContextualExplanationUnavailable("문맥 해설을 생성하지 못했습니다.") from error
        result = ContextualExplanationDTO(childConceptId=child.id if child else None,
            parentConceptId=parent.id, title=selected_text, definition=explanation.definition,
            contextSentence=explanation.contextSentence, cached=False,
            sourceEvidence={"evidenceIds": sorted(evidence_ids)} if evidence_ids else None,
            deepLink=f"/wiki?concept={quote(child.id, safe='')}" if child else None)
        await cache_manager.set(cache_key, result.model_dump(by_alias=True), ttl_seconds=300)
        return result

    async def mask_subgraph_response(self, response: CausalSubgraphResponse, current_user, session):
        """A two-hop neighbor must not inherit the center concept's confidential access."""
        result = response.model_copy(deep=True)
        permissions = {}
        for edge in result.graph.get("edges", []):
            params = edge.get("compensatingParams")
            if not params:
                continue
            for cid in (edge["source"], edge["target"]):
                if cid not in permissions:
                    permissions[cid] = await AccessControlService.can_view_confidential_l3(current_user, cid, session)
            if not (permissions[edge["source"]] or permissions[edge["target"]]):
                params["compensationFormula"] = "L3 열람 인가 필요"
        return result

    @staticmethod
    def build_scale_ladder(concept, concepts, edges):
        by_id = {c.id: c for c in concepts}
        links = {}
        for node in concepts:
            for kind in ('previous_step', 'next_step', 'alternative_to', 'part_of', 'is_a'):
                for item in concept_repo.relation_items((node.relations or {}).get(kind)):
                    target = concept_repo.resolve_reference_id(item.get('id') or item.get('targetId'), item.get('name'), concepts)
                    key = concept_repo.relation_edge_key(node.id, target, kind)
                    if target in by_id and target != node.id:
                        links[key] = dict(source=key[0], target=key[1], relationType=key[2],
                            mechanismLabel=item.get('reason') or item.get('mechanism') or '',
                            evidenceId=next(iter(item.get('evidenceIds') or []), None))
        for edge in edges:
            key = concept_repo.relation_edge_key(edge.source_concept_id, edge.target_concept_id, edge.relation_type)
            if key[0] in by_id and key[1] in by_id and key[0] != key[1] and key not in links:
                links[key] = dict(source=key[0], target=key[1], relationType=key[2],
                    mechanismLabel=edge.mechanism_label or '', evidenceId=edge.evidence_id)
        connected, frontier = {concept.id}, {concept.id}
        hops = {concept.id: 0}
        for depth in range(1, 3):
            adjacent = {other for link in links.values() for node, other in ((link['source'], link['target']), (link['target'], link['source'])) if node in frontier}
            frontier = adjacent - connected
            connected.update(frontier)
            hops.update({cid: depth for cid in frontier})
        if len(connected) == 1:
            return []
        selected = [dict(id=f'scale-link-{index}', **link) for index, (_, link) in enumerate(sorted(links.items()))
                    if link['source'] in connected and link['target'] in connected]
        return [ScaleLadderStepDTO(scaleLevel=node.scale_level, scaleName=node.scale_name or f'Scale {node.scale_level}',
                    title=node.title, description=node.summary or '', isCurrent=node.id == concept.id,
                    entityId=node.id, entityName=node.title, hops=hops[node.id],
                    connections=[link for link in selected if node.id in (link['source'], link['target'])])
                for node in sorted((by_id[cid] for cid in connected), key=lambda c: (-(c.scale_level or 0), c.id))
                if node.scale_level in range(1, 6)]

    async def masked_perspectives(self, concept, session, can_view_l3=False):
        """Share the existing public/L3 projection without assembling the detail screen."""
        from backend.app.repositories.source_repo import source_repo
        public_cases=await source_repo.public_case_ids(session,concept.id,concept.perspectives)
        perspectives_dto: List[PerspectiveCaseDTO] = []
        for p in concept.perspectives:
            raw_p = {
                "id": p.id,
                "is_public_case": p.id in public_cases,
                "concept_id": p.concept_id,
                "perspective_id": p.perspective_id,
                "perspective_title": p.perspective_title,
                "perspective_badge": p.perspective_badge,
                "management_code": p.management_code,
                "context_narrative": p.context_narrative,
                "specifications": p.specifications if isinstance(p.specifications, list) else [],
                "caution": p.caution,
                "evidence_id": p.evidence_id,
                "is_masked": False
            }
            masked = mask_tier3_perspective(raw_p, can_view_confidential=can_view_l3)
            masked.update(await case_explanation_service.fields(session, concept, p))
            perspectives_dto.append(PerspectiveCaseDTO(**masked))

        return perspectives_dto

    async def get_enriched_concept_detail(
        self,
        concept_id: str,
        current_user: Optional[UserModel],
        session: AsyncSession
    ) -> ConceptDetailResponse:
        # 1. Fetch concept from repository
        concept = await concept_repo.get_by_id(session, concept_id)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept '{concept_id}' not found in ontology knowledge base."
            )

        # 2. Check Level 3 confidentiality access
        can_view_l3 = False
        if current_user:
            can_view_l3 = await AccessControlService.can_view_confidential_l3(current_user, concept_id, session)

        # 3. Process perspectives and apply Tier 3 masking
        perspectives_dto = await self.masked_perspectives(concept, session, can_view_l3)

        # 4. Use recorded links and registered target metadata, including inverse process links.
        relation_records, concepts = await concept_repo.get_relations_for_concept(session, concept)
        enriched = {}
        for field, records in relation_records.items():
            values = []
            for item in records:
                cp = dict(item.get("compensatingParams") or {})
                if cp and not can_view_l3:
                    cp.pop("compensation_formula", None)
                    cp["compensationFormula"] = "L3 인가 필요"
                values.append(EnrichedRelationItemDTO(
                    id=item["id"], name=item["name"], relationType=field,
                    reason=item.get("reason") or item.get("mechanism"), mechanism=item.get("mechanism"),
                    scaleLevel=item.get("scaleLevel"), isRegistered=item["isRegistered"],
                    commonGoal=item.get("commonGoal"), tradeoff=item.get("tradeoff"),
                    evidenceIds=item.get("evidenceIds") or [], evidenceQuote=item.get("evidenceQuote"),
                    compensatingParams=CompensatingParamSchema(**cp) if cp else None))
            enriched[field] = values
        enriched_relations = EnrichedRelationsDTO(**enriched)
        raw_relations = concept.relations if isinstance(concept.relations, dict) else {}

        # Group the recorded two-hop neighborhood by scale; relation types remain explicit.
        scale_ladder = self.build_scale_ladder(concept, concepts, await concept_repo.get_all_causal_edges(session))

        # 7. Preloaded explainers for 0ms hover
        preloaded_explainers: Dict[str, ContextualExplanationDTO] = {}
        self_dto = ContextualExplanationDTO(
            child_concept_id=concept.id,
            parent_concept_id=concept.id,
            title=concept.title,
            definition=concept.summary,
            context_sentence=f"현재 열람 중인 [{concept.title}]의 핵심 지식 규격입니다. {concept.purpose or ''}".strip(),
            cached=True,
            deep_link=f"/wiki?concept={concept.id}"
        )
        preloaded_explainers[concept.id] = self_dto
        preloaded_explainers[concept.title.lower()] = self_dto

        # Normalize limitations to dicts with title & description
        norm_limitations = []
        if isinstance(concept.limitations, list):
            for lim in concept.limitations:
                if isinstance(lim, str):
                    norm_limitations.append({"title": lim[:40], "description": lim, "evidenceIds": []})
                elif isinstance(lim, dict):
                    norm_limitations.append(lim)

        # 8. Assemble ConceptDetailResponse
        return ConceptDetailResponse(
            id=concept.id,
            title=concept.title,
            eng_name=concept.eng_name,
            aliases=concept.aliases if isinstance(concept.aliases, list) else [],
            domain_facet=concept.domain_facet,
            process_category=concept.process_category,
            scale_level=concept.scale_level or 3,
            scale_name=concept.scale_name,
            version=concept.version,
            status=concept.status,
            last_reviewed_at=concept.last_reviewed_at.isoformat() if concept.last_reviewed_at else None,
            last_reviewed_by=concept.last_reviewed_by,
            summary=concept.summary,
            purpose=concept.purpose,
            principles=concept.principles if isinstance(concept.principles, list) else [],
            limitations=norm_limitations,
            relations=raw_relations,
            perspectives=perspectives_dto,
            evidence_ids=await concept_repo.get_evidence_ids_for_concept(session, concept),
            selection_terms=sorted({name.strip() for c in concepts
                for name in [c.title, c.eng_name, *(c.aliases or [])]
                if isinstance(name, str) and name.strip()}),
            preloaded_explainers=preloaded_explainers,
            enriched_relations=enriched_relations,
            scale_ladder=scale_ladder
        )


concept_service = ConceptService()
