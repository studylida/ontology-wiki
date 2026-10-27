import re

from sqlalchemy import String, cast, func, or_, select

from knowledge.core.errors import AppError
from knowledge.documents.entities import Document, DocumentRevision, Passage
from knowledge.documents.repository import DocumentRepository, citation_dict, public_scope
from knowledge.ontology.entities import Concept, ConceptRelation, ConceptSourceView
from knowledge.ontology.identity import IdentityCandidate


class OntologyRepository:
    def __init__(self, session):
        self.session = session

    async def lock_concept_identity(self):
        # A short save-only lock serializes alias-aware creation across jobs.
        # It is scoped to the current DB schema; no provider call holds it.
        await self.session.execute(select(func.pg_advisory_xact_lock(
            func.hashtext(func.current_schema() + ":ontology-concept-identity-v1"))))

    async def identity_candidates(self) -> list[IdentityCandidate]:
        """Use the same current public-evidence boundary as ontology read APIs."""
        allowed = await self.visible_public_revisions(None)
        views = list((await self.session.scalars(select(ConceptSourceView).join(DocumentRevision).where(
            ConceptSourceView.source_revision_id.in_(allowed), ConceptSourceView.status == "active",
            ConceptSourceView.metadata_version == DocumentRevision.metadata_version,
            ConceptSourceView.metadata_hash == DocumentRevision.metadata_hash))).all())
        source_labels = {}
        for view in views:
            if await self._evidence(view.evidence_refs, allowed):
                source_labels.setdefault(view.concept_id, []).extend(view.extractor.get("sourceLabels", []))
        result = []
        for concept in (await self.session.scalars(select(Concept))).all():
            if await self.concept_dict(concept, allowed) is not None:
                labels = [concept.name, *concept.aliases, *concept.names.values(), *source_labels.get(concept.id, [])]
                result.append(IdentityCandidate(concept.id, concept.type,
                                               tuple(label for label in labels if isinstance(label, str))))
        return result

    async def visible_public_revisions(self, principal, allowed=None):
        # Ontology is shared source-derived data. It never reads private sources.
        stmt = select(DocumentRevision.id).join(Document).where(public_scope())
        if allowed is None:
            stmt = stmt.where(Document.active_revision_id == DocumentRevision.id)
        else:
            stmt = stmt.where(DocumentRevision.id.in_(allowed))
        return list((await self.session.scalars(stmt)).all())

    async def _evidence(self, references, allowed, *, require_complete=True):
        ids = [r.get("passageId") for r in references if r.get("sourceRevisionId") in allowed]
        if not ids:
            return []
        rows = (await self.session.execute(select(Passage, DocumentRevision, Document)
            .join(DocumentRevision, Passage.source_revision_id == DocumentRevision.id)
            .join(Document, DocumentRevision.document_id == Document.id)
            .where(Passage.id.in_(ids), DocumentRevision.id.in_(allowed), Passage.excluded.is_(False), public_scope()))).all()
        # Cross-check both components of a reference. IDs alone cannot redirect citations.
        pairs = {(r.get("passageId"), r.get("sourceRevisionId")) for r in references}
        evidence = [citation_dict(p, r, d) for p, r, d in rows if (p.id, r.id) in pairs]
        if require_complete and {(e["passageId"], e["sourceRevisionId"]) for e in evidence} != pairs:
            # Hide the complete derivative when an input is no longer public.
            # This is authorization/provenance, not semantic string matching.
            return []
        return evidence

    async def concept_dict(self, concept, allowed):
        evidence = await self._evidence(concept.evidence_refs, allowed)
        name_evidence = evidence or await self._evidence(concept.evidence_refs, allowed, require_complete=False)
        if not name_evidence:
            views = list((await self.session.scalars(select(ConceptSourceView).join(DocumentRevision).where(
                ConceptSourceView.concept_id == concept.id, ConceptSourceView.source_revision_id.in_(allowed),
                ConceptSourceView.status == "active", ConceptSourceView.metadata_version == DocumentRevision.metadata_version,
                ConceptSourceView.metadata_hash == DocumentRevision.metadata_hash))).all())
            for view in views:
                if await self._evidence(view.evidence_refs, allowed):
                    name_evidence = True
                    break
        if not name_evidence:
            return None
        return {"id": concept.id, "name": concept.name, "names": concept.names,
                "aliases": concept.aliases, "type": concept.type, "revision": concept.revision,
                "description": concept.description if evidence else None,
                "evidence": evidence, "origin": concept.origin,
                "descriptionStatus": "source_linked" if evidence else "evidence_unavailable"}

    async def concepts(self, principal, query="", cursor=None, limit=40):
        allowed = await self.visible_public_revisions(principal)
        stmt = select(Concept)
        if query:
            stmt = stmt.where(or_(Concept.name.ilike(f"%{query}%"), cast(Concept.aliases, String).ilike(f"%{query}%")))
        if cursor:
            stmt = stmt.where(Concept.id > cursor)
        concepts = list((await self.session.scalars(stmt.order_by(Concept.id).limit(limit + 1))).all())
        items = [await self.concept_dict(c, allowed) for c in concepts[:limit]]
        return {"items": [item for item in items if item is not None],
                "nextCursor": concepts[limit - 1].id if len(concepts) > limit else None}

    async def concept(self, principal, concept_id):
        concept = await self.session.get(Concept, concept_id)
        if not concept:
            raise AppError(404, "concept_not_found", "개념을 찾을 수 없습니다.")
        result = await self.concept_dict(concept, await self.visible_public_revisions(principal))
        if result is None:
            raise AppError(404, "concept_not_public", "현재 공개 근거가 있는 개념을 찾을 수 없습니다.")
        return result

    async def context(self, principal, concept_ids, allowed_revision_ids):
        allowed = await self.visible_public_revisions(principal, allowed_revision_ids)
        if not concept_ids or not allowed:
            return {"relatedConcepts": [], "relations": [], "sourceViews": []}
        concepts = list((await self.session.scalars(select(Concept).where(Concept.id.in_(concept_ids)))).all())
        names = {c.id: c.name for c in concepts}
        relation_rows = list((await self.session.scalars(select(ConceptRelation).where(
            or_(ConceptRelation.from_concept_id.in_(concept_ids), ConceptRelation.to_concept_id.in_(concept_ids)),
            ConceptRelation.status.in_(["machine_extracted", "legacy_source_linked"])).limit(40))).all())
        relations = []
        for relation in relation_rows:
            evidence = await self._evidence(relation.evidence_refs, allowed)
            if not evidence:
                continue
            for cid in (relation.from_concept_id, relation.to_concept_id):
                if cid not in names:
                    c = await self.session.get(Concept, cid)
                    names[cid] = c.name
            relations.append({"id": relation.id, "fromConceptId": relation.from_concept_id,
                "toConceptId": relation.to_concept_id, "fromName": names[relation.from_concept_id],
                "toName": names[relation.to_concept_id], "type": relation.type,
                "summary": relation.summary, "conditions": relation.conditions, "status": relation.status,
                "evidence": evidence})
        views = await self.source_views(principal, concept_ids, allowed=allowed)
        related = [await self.concept_dict(c, allowed) for c in concepts]
        return {"relatedConcepts": [item for item in related if item is not None],
                "relations": relations, "sourceViews": views["items"]}

    async def source_views(self, principal, concept_ids, *, allowed=None, publisher_id=None, source_type=None,
                           aspect=None, date_from=None, date_to=None, cursor=None, limit=40):
        allowed = await self.visible_public_revisions(principal, allowed)
        stmt = select(ConceptSourceView, DocumentRevision).join(DocumentRevision).where(
            ConceptSourceView.concept_id.in_(concept_ids), ConceptSourceView.source_revision_id.in_(allowed),
            ConceptSourceView.status == "active", ConceptSourceView.metadata_version == DocumentRevision.metadata_version,
            ConceptSourceView.metadata_hash == DocumentRevision.metadata_hash)
        for field, value in (("publisherId", publisher_id), ("sourceType", source_type)):
            if value:
                stmt = stmt.where(DocumentRevision.metadata_json[field].astext == value)
        if aspect:
            stmt = stmt.where(ConceptSourceView.aspect == aspect)
        if date_from:
            stmt = stmt.where(DocumentRevision.metadata_json["publishedAt"].astext >= date_from)
        if date_to:
            stmt = stmt.where(DocumentRevision.metadata_json["publishedAt"].astext <= date_to)
        if cursor:
            stmt = stmt.where(ConceptSourceView.id > cursor)
        rows = (await self.session.execute(stmt.order_by(ConceptSourceView.id).limit(limit + 1))).all()
        result = []
        for view, rev in rows[:limit]:
            evidence = await self._evidence(view.evidence_refs, allowed)
            if not evidence:
                continue
            attribution = {k: view.attribution.get(k) for k in ("publisher", "publisherId", "author", "attributedTo", "attributionBasis", "sourceType")}
            result.append({"id": view.id, "conceptId": view.concept_id, "sourceRevisionId": rev.id,
                **attribution, "documentForm": rev.metadata_json.get("documentForm"), "aspect": view.aspect, "summary": view.summary,
                "conditions": view.conditions, "publishedAt": rev.metadata_json.get("publishedAt"),
                "status": view.extraction_status, "evidence": evidence,
                "metadataVersion": view.metadata_version, "extractedAt": view.created_at.isoformat(),
                "extractor": view.extractor})
        return {"items": result, "nextCursor": rows[limit - 1][0].id if len(rows) > limit else None}

    async def resolve_mentions(self, query_text: str) -> list[str]:
        """Resolve registered names/aliases only. Ambiguous aliases stay unresolved."""
        concepts = list((await self.session.scalars(select(Concept))).all())
        aliases = {}
        for concept in concepts:
            for name in [concept.name, *concept.aliases, *concept.names.values()]:
                if isinstance(name, str) and len(name.strip()) >= 2:
                    aliases.setdefault(name.casefold().strip(), set()).add(concept.id)
        query = query_text.casefold()
        matched = set()
        for alias, ids in aliases.items():
            pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
            if len(ids) == 1 and re.search(pattern, query):
                matched.update(ids)
        return sorted(matched)[:12]
