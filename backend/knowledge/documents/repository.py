"""Source access and retrieval SQL. All callers share current permission checks."""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from sqlalchemy import and_, case, func, or_, select

from knowledge.core.errors import AppError
from knowledge.core.ids import new_id
from knowledge.documents.entities import Document, DocumentAttachment, DocumentRevision, EmbeddingRecord, Passage, PassageEmbedding
from knowledge.documents.parsing import digest, metadata_digest, segment


def is_reviewer(principal) -> bool:
    return "documents:review" in principal.permissions


def public_scope():
    return and_(Document.visibility == "shared_candidate", DocumentRevision.review_status == "approved", Document.withdrawn.is_(False))


def read_scope(principal, *, derived=False):
    public = public_scope()
    if principal.kind == "service":
        return public
    private = and_(Document.owner_id == principal.id, Document.withdrawn.is_(False), DocumentRevision.review_status != "withdrawn")
    if not derived and is_reviewer(principal):
        return or_(public, private, Document.visibility == "shared_candidate")
    return or_(public, private)


def group_predicate(group: dict):
    parts = []
    if group.get("publisherId"):
        parts.append(DocumentRevision.metadata_json["publisherId"].astext == group["publisherId"])
    if group.get("sourceType"):
        parts.append(DocumentRevision.metadata_json["sourceType"].astext == group["sourceType"])
    return and_(*parts) if parts else True


def group_match(metadata: dict, group: dict) -> bool:
    return all(metadata.get(k) == group[k] for k in ("publisherId", "sourceType") if group.get(k))


def citation_dict(passage: Passage, revision: DocumentRevision, document: Document) -> dict:
    meta = revision.metadata_json
    return {"id": passage.id, "passageId": passage.id, "sourceRevisionId": revision.id,
            "title": document.title, "locator": passage.locator, "excerpt": passage.text,
            "publisher": meta.get("publisher"), "publisherId": meta.get("publisherId"),
            "author": meta.get("author"), "attributedTo": meta.get("attributedTo"),
            "attributionBasis": meta.get("attributionBasis", "unknown"),
            "sourceType": meta.get("sourceType", "unknown"), "url": meta.get("url"),
            "publishedAt": meta.get("publishedAt"), "readScope": revision.read_scope,
            "metadataVersion": revision.metadata_version}


class DocumentRepository:
    def __init__(self, session):
        self.session = session

    async def create_source(self, principal, request, raw_path, *, read_scope_value="full", origin_key=None, media_type=None):
        """Insert one source within the caller's transaction (including transfers)."""
        metadata = request.model_dump(mode="json", by_alias=True, exclude={"title", "content", "format", "visibility"})
        document = Document(id=new_id("doc"), owner_id=principal.id, title=request.title,
                            visibility=request.visibility, origin_key=origin_key)
        self.session.add(document)
        await self.session.flush()
        revision = DocumentRevision(id=new_id("rev"), document_id=document.id, revision=1,
            content=request.content, content_hash=digest(request.content), raw_path=raw_path,
            media_type=media_type or ("text/markdown" if request.format == "markdown" else "text/plain"),
            metadata_json=metadata, metadata_hash=metadata_digest(metadata),
            review_status="private" if document.visibility == "private" else "pending", read_scope=read_scope_value)
        self.session.add(revision)
        await self.session.flush()
        document.current_revision_id = revision.id
        for passage in segment(request.content, request.title):
            self.session.add(Passage(source_revision_id=revision.id, **passage.__dict__))
        await self.session.flush()
        return document, revision

    async def attach(self, principal, revision_id, conversation_id):
        # Caller first locks the owned conversation, serializing all attachment
        # creation paths without a check-then-insert race.
        await self.revision(principal, revision_id)
        if not await self.ensure_readable(principal, [revision_id]):
            raise AppError(403, "source_unavailable", "자료의 접근 권한이 변경되었습니다.")
        existing = await self.session.scalar(select(DocumentAttachment).where(
            DocumentAttachment.conversation_id == conversation_id, DocumentAttachment.source_revision_id == revision_id,
            DocumentAttachment.owner_id == principal.id))
        if existing:
            return existing.id
        attachment = DocumentAttachment(id=new_id("att"), owner_id=principal.id,
            conversation_id=conversation_id, source_revision_id=revision_id)
        self.session.add(attachment)
        await self.session.flush()
        return attachment.id

    async def resolve_snapshot(self, principal, source_revision_ids=None, source_groups=None) -> list[str]:
        stmt = select(DocumentRevision.id).join(Document, DocumentRevision.document_id == Document.id)
        if source_revision_ids is None:
            stmt = stmt.where(Document.active_revision_id == DocumentRevision.id, public_scope(), DocumentRevision.index_status == "ready")
        else:
            if not source_revision_ids:
                return []
            stmt = stmt.where(DocumentRevision.id.in_(source_revision_ids), read_scope(principal),
                              Document.withdrawn.is_(False), DocumentRevision.review_status != "withdrawn")
        if source_groups:
            stmt = stmt.where(or_(*(group_predicate(group) for group in source_groups)))
        return list((await self.session.scalars(stmt.order_by(DocumentRevision.id))).all())

    async def ensure_readable(self, principal, revision_ids, *, lock=False) -> bool:
        ids = set(revision_ids)
        if not ids:
            return True
        stmt = select(DocumentRevision.id).join(Document).where(DocumentRevision.id.in_(ids),
            read_scope(principal), Document.withdrawn.is_(False), DocumentRevision.review_status != "withdrawn")
        if lock:
            stmt = stmt.with_for_update(of=(DocumentRevision, Document))
        return set((await self.session.scalars(stmt)).all()) == ids

    async def revision(self, principal, revision_id, *, for_update=False):
        stmt = select(DocumentRevision, Document).join(Document).where(DocumentRevision.id == revision_id, read_scope(principal))
        if for_update:
            stmt = stmt.with_for_update()
        row = (await self.session.execute(stmt)).first()
        if row is None:
            raise AppError(404, "source_not_found", "문헌이 없거나 현재 읽을 권한이 없습니다.")
        return row

    async def passages(self, revision_id, *, include_excluded=False):
        stmt = select(Passage).where(Passage.source_revision_id == revision_id).order_by(Passage.ordinal)
        if not include_excluded:
            stmt = stmt.where(Passage.excluded.is_(False))
        return list((await self.session.scalars(stmt)).all())

    def _base(self, principal, revision_ids, groups):
        stmt = select(Passage, DocumentRevision, Document).join(DocumentRevision, Passage.source_revision_id == DocumentRevision.id).join(Document, DocumentRevision.document_id == Document.id)
        stmt = stmt.where(Passage.excluded.is_(False), DocumentRevision.id.in_(revision_ids), public_scope(),
                          Document.withdrawn.is_(False), DocumentRevision.review_status != "withdrawn")
        if groups:
            stmt = stmt.where(or_(*(group_predicate(group) for group in groups)))
        return stmt

    async def search(self, principal, query_vector, profile_id, query_text, source_revision_ids=None, source_groups=None, limit=12):
        if source_revision_ids is None:
            source_revision_ids = await self.resolve_snapshot(principal, None, source_groups)
        snapshot = "idx-" + hashlib.sha256("|".join(sorted(source_revision_ids)).encode()).hexdigest()[:24]
        groups, warnings = source_groups or [], []
        if not source_revision_ids:
            return {"hits": [], "indexSnapshotId": snapshot, "groupCoverage": [
                {"groupId": group["groupId"], "hitCount": 0, "status": "missing"} for group in groups],
                "warnings": ["검색 가능한 문헌이 없습니다. 승인·색인 상태와 자료 범위를 확인하세요."]}
        base = self._base(principal, source_revision_ids, groups)
        vector_stmt = base.join(PassageEmbedding, PassageEmbedding.passage_id == Passage.id).join(EmbeddingRecord, EmbeddingRecord.id == PassageEmbedding.embedding_id).where(PassageEmbedding.profile_id == profile_id)
        distance = EmbeddingRecord.vector.cosine_distance(query_vector)
        vector_rows, lexical_rows = [], []
        terms = list(dict.fromkeys(t.casefold() for t in re.findall(r"[\w가-힣-]{2,}", query_text)))[:16]
        # Query each requested group independently before ranking. A high-volume
        # publisher must not evict a smaller requested group's candidates.
        for group in groups or [{}]:
            scoped_vector = vector_stmt.where(group_predicate(group))
            vector_rows.extend((await self.session.execute(scoped_vector.add_columns(distance.label("distance")).order_by(distance, Passage.id).limit(max(60, limit * 4)))).all())
            if terms:
                matches = [func.lower(Passage.text).contains(t, autoescape=True) for t in terms]
                lexical_score = sum(case((condition, 1), else_=0) for condition in matches)
                lexical_rows.extend((await self.session.execute(base.where(group_predicate(group)).add_columns(lexical_score.label("lexical_score")).where(or_(*matches)).order_by(lexical_score.desc(), Passage.id).limit(max(60, limit * 4)))).all())
        vector_rows = sorted({row[0].id: row for row in vector_rows}.values(), key=lambda row: (float(row[3]), row[0].id))
        lexical_rows = sorted({row[0].id: row for row in lexical_rows}.values(), key=lambda row: (-int(row[3]), row[0].id))
        if not vector_rows:
            warnings.append("선택 프로필의 벡터가 없습니다. 현재 결과는 명시적 문자열 검색입니다.")
        candidates: dict[str, dict] = {}
        for method, rows in (("vector", vector_rows), ("lexical", lexical_rows)):
            for rank, row in enumerate(rows, 1):
                passage, revision, document = row[:3]
                hit = candidates.setdefault(passage.id, {**citation_dict(passage, revision, document),
                    "text": passage.text, "score": 0.0, "methods": [], "documentId": document.id})
                hit["score"] += 1 / (60 + rank)
                hit["methods"].append(method)
                if method == "vector":
                    hit["cosineDistance"] = float(row[3])
        ordered = sorted(candidates.values(), key=lambda h: (-h["score"], h["passageId"]))
        chosen, seen, per_doc = [], set(), defaultdict(int)
        # Give every requested source group an opportunity, never fabricate coverage.
        for group in groups:
            for hit in ordered:
                if group_match(hit, group) and hit["passageId"] not in seen:
                    chosen.append(hit); seen.add(hit["passageId"]); per_doc[hit["documentId"]] += 1
                    break
        for hit in ordered:
            if len(chosen) >= limit:
                break
            if hit["passageId"] not in seen and per_doc[hit["documentId"]] < 3:
                chosen.append(hit); seen.add(hit["passageId"]); per_doc[hit["documentId"]] += 1
        coverage = [{"groupId": group["groupId"], "hitCount": sum(group_match(h, group) for h in chosen),
                     "status": "available" if any(group_match(h, group) for h in chosen) else "missing"} for group in groups]
        return {"hits": chosen, "indexSnapshotId": snapshot, "groupCoverage": coverage, "warnings": warnings}

    async def get_neighbors(self, principal, passage_ids, source_revision_ids=None, source_groups=None):
        origins = list((await self.session.scalars(select(Passage).where(Passage.id.in_(passage_ids)))).all())
        if not origins:
            return []
        if source_revision_ids is None:
            source_revision_ids = await self.resolve_snapshot(principal, None, source_groups)
        neighbor_conditions = [and_(Passage.source_revision_id == origin.source_revision_id,
            Passage.ordinal.in_([origin.ordinal - 1, origin.ordinal + 1])) for origin in origins]
        rows = (await self.session.execute(self._base(principal, source_revision_ids, source_groups).where(or_(*neighbor_conditions)).order_by(Passage.source_revision_id, Passage.ordinal).limit(24))).all()
        return [{**citation_dict(p, r, d), "text": p.text, "score": None, "methods": ["neighbor"],
                 "neighborOf": [o.id for o in origins if o.source_revision_id == p.source_revision_id and abs(o.ordinal - p.ordinal) == 1]}
                for p, r, d in rows]

    async def attachment_context(self, principal, attachment_ids, conversation_id=None):
        if principal.kind != "user" or not attachment_ids:
            return []
        stmt = select(DocumentAttachment).where(DocumentAttachment.id.in_(attachment_ids), DocumentAttachment.owner_id == principal.id)
        if conversation_id:
            stmt = stmt.where(DocumentAttachment.conversation_id == conversation_id)
        attachments = list((await self.session.scalars(stmt)).all())
        if len(attachments) != len(set(attachment_ids)):
            raise AppError(404, "attachment_not_found", "첨부 자료가 없거나 현재 대화에서 사용할 수 없습니다.")
        result = []
        for attachment in attachments:
            revision, document = await self.revision(principal, attachment.source_revision_id)
            if not await self.ensure_readable(principal, [revision.id]):
                raise AppError(403, "source_unavailable", "첨부 자료의 접근 권한이 변경되었습니다.")
            for passage in (await self.passages(revision.id))[:24]:
                result.append({**citation_dict(passage, revision, document), "text": passage.text,
                               "score": None, "methods": ["attachment"]})
        return result

    async def selected_context(self, principal, source_revision_ids):
        """Explicitly selected source excerpts, separate from shared-index eligibility."""
        result = []
        for revision_id in dict.fromkeys(source_revision_ids):
            revision, document = await self.revision(principal, revision_id)
            if not await self.ensure_readable(principal, [revision.id]):
                raise AppError(403, "source_unavailable", "선택한 자료의 접근 권한이 변경되었습니다.")
            for passage in (await self.passages(revision.id))[:24]:
                result.append({**citation_dict(passage, revision, document), "text": passage.text,
                               "score": None, "methods": ["explicit_source"]})
        return result
