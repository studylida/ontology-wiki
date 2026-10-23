"""[계층 4] Concept Repository Layer.

Pure Async Database Access Layer for Concepts, CausalEdges, and Relations.
Does not perform DTO transformation or HTTP logic.
"""
from typing import List, Optional, Set, Dict, Any
from copy import deepcopy
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, null, update, exists
from sqlalchemy.orm import selectinload

from backend.app.models.entities import ConceptModel, CausalEdgeModel, PerspectiveCaseModel, EvidenceSourceModel


ID_ALIASES: Dict[str, str] = {
    "concept-tcb": "tcb-bonding",
    "concept-mrmuf": "mr-muf",
    "concept-dry-etch": "dry-etch",
    "concept-cryo-etch": "cryogenic-etch",
    "concept-high-na-euv": "high-na-euv",
    "concept-gaa-nanosheet": "gaa-nanosheet-etch",
    "concept-fdc-apc": "fab-fdc-oes-realtime",
    "concept-2f2cb28d": "tgv-glass-substrate",
    "concept-interconnect": "cu-damascene-cmp",
    "cand-samsung_fab_02_o-sio": "thermal-oxidation",
    "cand-asml_core_techno-euv": "euv-lithography",
    "cand-tier1_landmark_0-infofowlp201": "fan-out-wafer-level-packaging",
    "cand-samsung_fab_08_e-eds": "hbm-kgd-testing",
    "cand-samsung_fab_06_d-deposition": "ald-deposition",
    "cand-amat_core_techno-epitaxy": "epitaxy-growth",
    "cand-samsung_fab_06_d-ionimplantat": "ion-implantation",
    "cand-samsung_fab_04_p-": "photomask-fabrication",
    "cand-samsung_fab_05_e-etching": "wet-etching",
    "cand-semi_standards_a-": "gem300-standards",
    "cand-semi_standards_a-apcfdc": "apc-fdc-standards",
    "cand-amat_core_techno-inspectionme": "inspection-metrology",
    "cand-imec_nist_ieee_l-nist": "nist-metrology-standards",
    "cand-samsung_fab_03_i-icintegrated": "device-integration-ic",
}


class ConceptRepository:
    """Async database operations for ontology concepts and causal edges."""

    async def get_by_id(self, session: AsyncSession, concept_id: str) -> Optional[ConceptModel]:
        """Fetch concept by ID with perspectives eager loaded, resolving legacy aliases."""
        resolved_id = ID_ALIASES.get(concept_id, concept_id)
        stmt = (
            select(ConceptModel)
            .options(selectinload(ConceptModel.perspectives))
            .where(ConceptModel.id == resolved_id)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def merge_aliases(self, session: AsyncSession, concept_id: str, aliases: List[str]) -> None:
        """Add reviewed names without replacing existing source aliases or committing."""
        concept = await self.get_by_id(session, concept_id)
        if concept is None:
            raise LookupError(concept_id)
        concept.aliases = list(dict.fromkeys([*(concept.aliases or []), *aliases]))

    async def get_case(
        self, session: AsyncSession, concept_id: str, case_id: str
    ) -> Optional[PerspectiveCaseModel]:
        result = await session.execute(select(PerspectiveCaseModel).where(
            PerspectiveCaseModel.id == case_id,
            PerspectiveCaseModel.concept_id == concept_id,
        ))
        return result.scalar_one_or_none()

    async def get_case_evidences(
        self, session: AsyncSession, ids: List[str]
    ) -> List[EvidenceSourceModel]:
        if not ids:
            return []
        result = await session.execute(select(EvidenceSourceModel).where(EvidenceSourceModel.id.in_(ids)))
        return list(result.scalars().all())

    async def save_case_explanation(
        self, session: AsyncSession, concept_id: str, case_id: str,
        case_updated_at, concept_updated_at, payload: Dict[str, Any],
    ) -> bool:
        result = await session.execute(update(PerspectiveCaseModel).where(
            PerspectiveCaseModel.id == case_id,
            PerspectiveCaseModel.concept_id == concept_id,
            PerspectiveCaseModel.updated_at == case_updated_at,
            exists(select(ConceptModel.id).where(
                ConceptModel.id == concept_id,
                ConceptModel.updated_at == concept_updated_at,
            )),
        ).values(context_explanation=payload).execution_options(synchronize_session=False))
        return result.rowcount == 1

    async def get_all_concepts(self, session: AsyncSession) -> List[ConceptModel]:
        """Fetch all concept entities."""
        stmt = select(ConceptModel)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def get_all_concept_ids(self, session: AsyncSession) -> Set[str]:
        """Fetch set of all registered concept IDs."""
        stmt = select(ConceptModel.id)
        res = await session.execute(stmt)
        return set(res.scalars().all())

    async def get_evidence_ids_for_concept(self, session: AsyncSession, concept: ConceptModel) -> List[str]:
        rows = await session.execute(select(EvidenceSourceModel.id, EvidenceSourceModel.referenced_concepts))
        return [eid for eid, refs in rows if any(
            ref.get("conceptId") == concept.id and (bool(ref.get("citationTag") and ref["citationTag"] in (concept.summary or "")) or any(
                text and text == getattr(concept, field) for field, text in (ref.get("bodyFields") or {}).items()
                if field in ("summary", "purpose")))
            for ref in (refs or []) if isinstance(ref, dict))]

    async def get_causal_edges_for_concept(
        self, session: AsyncSession, concept_id: str
    ) -> List[CausalEdgeModel]:
        """Fetch incoming and outgoing causal edges for a concept."""
        stmt = select(CausalEdgeModel).where(
            (CausalEdgeModel.source_concept_id == concept_id) |
            (CausalEdgeModel.target_concept_id == concept_id)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    def relation_items(value: Any) -> List[Dict[str, Any]]:
        if isinstance(value, (str, dict)):
            value = [value]
        return [({"id": item} if isinstance(item, str) else item)
                for item in (value or []) if isinstance(item, (str, dict))]

    @staticmethod
    def resolve_reference_id(reference_id: str, name: Optional[str], concepts: List[ConceptModel]) -> str:
        ids = {c.id for c in concepts}
        if reference_id in ids:
            return reference_id
        mapped = ID_ALIASES.get(reference_id, reference_id)
        if mapped in ids:
            return mapped
        def key(value):
            return re.sub(r"[\s_-]+", "", value or "").casefold()
        candidates = {key(value) for value in (reference_id, name) if value}
        matches = {c.id for c in concepts if candidates.intersection(
            key(value) for value in [c.id, c.title, c.eng_name, *(c.aliases or [])] if value
        )}
        return next(iter(matches)) if len(matches) == 1 else mapped

    async def get_relations_for_concept(self, session: AsyncSession, concept: ConceptModel):
        """Read recorded links in both directions; resolve registration against the whole DB."""
        concepts = await self.get_all_concepts(session)
        by_id = {c.id: c for c in concepts}
        fields = {"previous_step": "previousSteps", "next_step": "nextSteps",
                  "alternative_to": "alternatives", "part_of": "partOf", "is_a": "isA"}
        relations = {field: [] for field in [*fields.values(), "hasParts", "subtypes"]}

        def append(field, item, target_id):
            target_id = self.resolve_reference_id(target_id, item.get("name") or item.get("targetName"), concepts)
            if not target_id:
                return
            existing = next((r for r in relations[field] if r["id"] == target_id), None)
            if existing:
                if item.get("compensatingParams"):
                    existing["compensatingParams"] = item["compensatingParams"]
                existing["evidenceIds"] = list(dict.fromkeys((existing.get("evidenceIds") or []) + (item.get("evidenceIds") or [])))
                return
            target = by_id.get(target_id)
            relations[field].append({
                **item, "id": target_id,
                "name": target.title if target else item.get("name") or item.get("targetName") or target_id,
                "scaleLevel": target.scale_level if target else item.get("scaleLevel"),
                "isRegistered": target is not None
            })

        for source in concepts:
            raw = source.relations if isinstance(source.relations, dict) else {}
            for relation_type, field in fields.items():
                for item in self.relation_items(raw.get(relation_type)):
                    target_id = self.resolve_reference_id(item.get("id") or item.get("targetId"), item.get("name") or item.get("targetName"), concepts)
                    if source.id == concept.id:
                        append(field, item, target_id)
                    elif target_id == concept.id:
                        reverse = {"previous_step": "nextSteps", "next_step": "previousSteps", "alternative_to": "alternatives", "part_of": "hasParts", "is_a": "subtypes"}[relation_type]
                        append(reverse, {**item, "name": source.title}, source.id)

        for edge in await self.get_causal_edges_for_concept(session, concept.id):
            field = fields.get(edge.relation_type)
            if not field:
                continue
            target_id = edge.target_concept_id
            if edge.source_concept_id != concept.id:
                reverse = {"next_step": "previousSteps", "previous_step": "nextSteps", "alternative_to": "alternatives", "part_of": "hasParts", "is_a": "subtypes"}
                field = reverse.get(edge.relation_type)
                target_id = edge.source_concept_id
            if field:
                append(field, {"reason": edge.mechanism_label or None,
                               "evidenceIds": [edge.evidence_id] if edge.evidence_id else [],
                               "compensatingParams": edge.compensating_params}, target_id)
        return relations, concepts

    async def get_all_causal_edges(self, session: AsyncSession) -> List[CausalEdgeModel]:
        result = await session.execute(select(CausalEdgeModel))
        return list(result.scalars().all())

    @staticmethod
    def relation_edge_key(source, target, kind):
        if kind == "previous_step":
            source, target, kind = target, source, "next_step"
        if kind == "alternative_to":
            source, target = sorted((source, target))
        return source, target, kind

    async def update_review_relations(self, session, concept_id, previous, state):
        from fastapi import HTTPException
        concepts=await self.get_all_concepts(session)
        fields={'previousSteps':'previous_step','nextSteps':'next_step','alternatives':'alternative_to','partOf':'part_of','isA':'is_a'}
        edges=(await session.execute(select(CausalEdgeModel))).scalars().all()
        for field,kind in fields.items():
            for old in previous[field]:
                target=self.resolve_reference_id(old.get('id') or old.get('targetId'),old.get('name') or old.get('targetName'),concepts)
                new=next((r for r in state[field] if (r.get('id') or r.get('targetId'))==(old.get('id') or old.get('targetId'))),None)
                if new is None or (old.get('reason') or old.get('tradeoff') or '',old.get('evidenceIds') or [])==(new.get('reason') or new.get('tradeoff') or '',new.get('evidenceIds') or []):continue
                if not target:continue
                key=self.relation_edge_key(concept_id,target,kind)
                for edge in edges:
                    if self.relation_edge_key(edge.source_concept_id,edge.target_concept_id,edge.relation_type)!=key:continue
                    shared=False
                    for concept in concepts:
                        if concept.id==concept_id:continue
                        for other_kind in fields.values():
                            for link in self.relation_items((concept.relations or {}).get(other_kind)):
                                other_target=self.resolve_reference_id(link.get('id') or link.get('targetId'),link.get('name') or link.get('targetName'),concepts)
                                if other_target and self.relation_edge_key(concept.id,other_target,other_kind)==key:shared=True
                    if shared or (edge.mechanism_label or '')!=(old.get('reason') or old.get('tradeoff') or '') or edge.evidence_id and edge.evidence_id not in (old.get('evidenceIds') or []):
                        raise HTTPException(409,'다른 자료나 독립 편집이 지지하는 관계입니다. 관계 근거를 함께 검토해 주세요.')
                    edge.mechanism_label=new.get('reason') or new.get('tradeoff') or ''
                    edge.evidence_id=next(iter(new.get('evidenceIds') or []),None)
        await session.flush()

    async def reconcile_relation_edges(self, session: AsyncSession, removed_relations=None):
        """Resolve earlier references too, so newly registered concepts join existing knowledge."""
        # shortcut: scan current wiki references on apply; index pending references if this becomes slow.
        concepts = await self.get_all_concepts(session)
        ids = {c.id for c in concepts}
        edges = (await session.execute(select(CausalEdgeModel))).scalars().all()
        by_key = {(e.source_concept_id, e.target_concept_id, e.relation_type): e for e in edges}
        supported = set()
        for concept in concepts:
            relations = deepcopy(concept.relations or {})
            changed = False
            for relation_type in ("previous_step", "next_step", "alternative_to", "part_of", "is_a"):
                items = self.relation_items(relations.get(relation_type))
                for item in items:
                    original = item.get("id") or item.get("targetId")
                    target = self.resolve_reference_id(original, item.get("name") or item.get("targetName"), concepts)
                    if target and target != original:
                        item["targetId" if "targetId" in item else "id"] = target
                        changed = True
                    if not target or target not in ids or target == concept.id:
                        continue
                    source, dest, kind = self.relation_edge_key(concept.id, target, relation_type)
                    supported.add((source, dest, kind))
                    evidence_ids = item.get("evidenceIds") or []
                    reason = item.get("reason") or item.get("tradeoff") or ""
                    key = (source, dest, kind)
                    edge = by_key.get(key)
                    if edge is None:
                        edge = CausalEdgeModel(source_concept_id=source, target_concept_id=dest,
                                              relation_type=kind, mechanism_label=reason,
                                              evidence_id=evidence_ids[0] if evidence_ids else None,
                                              polarity=null())
                        session.add(edge)
                        by_key[key] = edge
                    else:
                        if reason and not edge.mechanism_label:
                            edge.mechanism_label = reason
                        if evidence_ids and not edge.evidence_id:
                            edge.evidence_id = evidence_ids[0]
                if changed:
                    relations[relation_type] = items
            if changed:
                concept.relations = relations
        fields = {"previousSteps": "previous_step", "nextSteps": "next_step", "alternatives": "alternative_to", "partOf": "part_of", "isA": "is_a"}
        for removed in removed_relations or []:
            link = removed["link"]
            target = self.resolve_reference_id(link.get("id") or link.get("targetId"), link.get("name") or link.get("targetName"), concepts)
            key = self.relation_edge_key(removed["sourceId"], target, fields[removed["field"]])
            # An edge edited independently or still supported by another JSON link must survive.
            for edge_key, edge in list(by_key.items()):
                if self.relation_edge_key(*edge_key) != key or key in supported:
                    continue
                if edge.mechanism_label != (link.get("reason") or link.get("tradeoff") or ""):
                    continue
                if edge.evidence_id and edge.evidence_id not in (link.get("evidenceIds") or []):
                    continue
                await session.delete(edge)
                del by_key[edge_key]
        await session.flush()

    async def find_previous_steps_by_reverse_lookup(
        self, session: AsyncSession, concept_id: str
    ) -> List[ConceptModel]:
        """Find concepts whose next_step links point to concept_id."""
        all_concepts = await self.get_all_concepts(session)
        matching = []
        for c in all_concepts:
            if not isinstance(c.relations, dict):
                continue
            next_steps = c.relations.get("next_step", [])
            for ns in next_steps:
                target_id = ns.get("id") or ns.get("targetId")
                if target_id == concept_id:
                    matching.append(c)
                    break
        return matching


concept_repo = ConceptRepository()
