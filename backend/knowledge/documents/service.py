from sqlalchemy import select, update

from knowledge.core.errors import AppError
from knowledge.core.ids import new_id, utcnow
from knowledge.documents.entities import Document, DocumentAttachment, DocumentRevision, MetadataHistory, Passage, ReviewDecision
from knowledge.documents.parsing import declared_document_form, digest, metadata_digest, save_raw, segment
from knowledge.documents.repository import DocumentRepository, is_reviewer, read_scope
from knowledge.jobs.repository import JobRepository


def document_dict(document, revision):
    metadata = revision.metadata_json
    return {"id": document.id, "title": document.title, "currentRevisionId": revision.id,
            "activeRevisionId": document.active_revision_id, "revision": revision.revision,
            "reviewStatus": revision.review_status, "indexStatus": revision.index_status,
            "visibility": document.visibility, "publisher": metadata.get("publisher"),
            "publisherId": metadata.get("publisherId"), "sourceType": metadata.get("sourceType"),
            "url": metadata.get("url"), "updatedAt": document.updated_at.isoformat()}


class DocumentService:
    def __init__(self, session_factory, settings):
        self.sessions, self.settings = session_factory, settings

    async def create(self, principal, request, *, read_scope_value="full", raw_bytes=None, origin_key=None,
                     media_type=None, processing_metadata=None, passage_records=None):
        principal.require("documents:write")
        raw_path = save_raw(self.settings.storage_path, raw_bytes or request.content.encode())
        async with self.sessions() as session, session.begin():
            doc, rev = await DocumentRepository(session).create_source(principal, request, raw_path,
                read_scope_value=read_scope_value, origin_key=origin_key, media_type=media_type,
                processing_metadata=processing_metadata, passage_records=passage_records)
            return document_dict(doc, rev)

    @staticmethod
    def _add_passages(session, revision_id, title, content):
        for p in segment(content, title):
            session.add(Passage(source_revision_id=revision_id, **p.__dict__))

    async def add_revision(self, principal, document_id, request):
        principal.require("documents:write")
        raw_path = save_raw(self.settings.storage_path, request.content.encode())
        async with self.sessions() as session, session.begin():
            doc = await session.get(Document, document_id, with_for_update=True)
            if not doc or (doc.owner_id != principal.id and not is_reviewer(principal)):
                raise AppError(404, "source_not_found", "문헌이 없거나 편집 권한이 없습니다.")
            previous = await session.get(DocumentRevision, doc.current_revision_id)
            if previous.content_hash == digest(request.content):
                return document_dict(doc, previous)
            metadata = dict(previous.metadata_json)
            if metadata.get("parserProfile"):
                metadata["derivedFromRevisionId"] = previous.id
                for field in ("parserProfile", "chunkProfile", "preparedPassagesArtifact", "sourceMapArtifact", "structuredArtifact",
                              "sourceMapPath", "structuredDocumentPath", "extractedTextPath", "conversionKey"):
                    metadata.pop(field, None)
                metadata["documentForm"] = "edited_derivative"
            declared_form = declared_document_form(request.content)
            if declared_form is not None and declared_form != declared_document_form(previous.content):
                metadata["documentForm"] = declared_form
            rev = DocumentRevision(id=new_id("rev"), document_id=doc.id, revision=previous.revision + 1,
                content=request.content, content_hash=digest(request.content), raw_path=raw_path,
                metadata_json=metadata, metadata_hash=metadata_digest(metadata),
                review_status="private" if doc.visibility == "private" else "pending")
            session.add(rev)
            await session.flush()
            doc.current_revision_id, doc.updated_at = rev.id, utcnow()
            self._add_passages(session, rev.id, doc.title, request.content)
            await session.flush()
            return document_dict(doc, rev)

    async def list(self, principal, review_status=None):
        async with self.sessions() as session:
            stmt = select(Document, DocumentRevision).join(DocumentRevision, DocumentRevision.id == Document.current_revision_id).where(read_scope(principal))
            if review_status:
                stmt = stmt.where(DocumentRevision.review_status == review_status)
            rows = (await session.execute(stmt.order_by(Document.updated_at.desc()).limit(250))).all()
            return {"items": [document_dict(d, r) for d, r in rows]}

    async def detail(self, principal, revision_id):
        async with self.sessions() as session:
            repo = DocumentRepository(session)
            rev, doc = await repo.revision(principal, revision_id)
            passages = await repo.passages(rev.id, include_excluded=True)
            reviews = list((await session.scalars(select(ReviewDecision).where(ReviewDecision.source_revision_id == rev.id).order_by(ReviewDecision.created_at))).all())
            return {"id": rev.id, "documentId": doc.id, "title": doc.title, "content": rev.content,
                    "metadata": rev.metadata_json, "metadataVersion": rev.metadata_version,
                    "reviewStatus": rev.review_status, "indexStatus": rev.index_status,
                    "readScope": rev.read_scope, "revision": rev.revision,
                    "passages": [{"id": p.id, "ordinal": p.ordinal, "text": p.text, "locator": p.locator,
                                  "excluded": p.excluded, "exclusionReason": p.exclusion_reason} for p in passages],
                    "reviewHistory": [{"decision": r.decision, "reason": r.reason, "at": r.created_at.isoformat()} for r in reviews] if is_reviewer(principal) else []}

    async def review(self, principal, revision_id, request):
        principal.require("documents:review")
        from knowledge.ontology.entities import ConceptSourceView
        async with self.sessions() as session, session.begin():
            rev, doc = await DocumentRepository(session).revision(principal, revision_id, for_update=True)
            if doc.visibility != "shared_candidate":
                raise AppError(409, "private_source", "비공개 자료는 공용 검토 대상이 아닙니다.")
            states = {"approve": "approved", "reject": "rejected", "hold": "held", "withdraw": "withdrawn"}
            previous_status = rev.review_status
            rev.review_status = states[request.decision]
            doc.updated_at = utcnow()
            session.add(ReviewDecision(source_revision_id=rev.id, reviewer_id=principal.id,
                                       decision=request.decision, reason=request.reason))
            if request.decision == "withdraw":
                doc.withdrawn = True
                await session.execute(update(ConceptSourceView).where(ConceptSourceView.source_revision_id == rev.id,
                    ConceptSourceView.status == "active").values(status="withdrawn"))
            elif request.decision == "approve":
                doc.withdrawn = False
            if request.decision != "approve" or previous_status != "approved":
                rev.index_status = "pending"
                if doc.active_revision_id == rev.id:
                    doc.active_revision_id = None
            await session.flush()
            return document_dict(doc, rev)

    async def patch_metadata(self, principal, revision_id, request):
        principal.require("documents:review")
        from knowledge.ontology.entities import ConceptSourceView
        async with self.sessions() as session, session.begin():
            rev, doc = await DocumentRepository(session).revision(principal, revision_id, for_update=True)
            patch = request.model_dump(mode="json", by_alias=True, exclude_unset=True)
            updated = {**rev.metadata_json, **patch}
            if updated == rev.metadata_json:
                return {"metadataVersion": rev.metadata_version, "changed": False}
            session.add(MetadataHistory(source_revision_id=rev.id, version=rev.metadata_version,
                                        metadata_json=rev.metadata_json, changed_by=principal.id))
            views = list((await session.scalars(select(ConceptSourceView).where(
                ConceptSourceView.source_revision_id == rev.id, ConceptSourceView.status == "active"))).all())
            rev.metadata_json, rev.metadata_hash = updated, metadata_digest(updated)
            rev.metadata_version += 1
            for view in views:
                view.status = "superseded"
                await JobRepository(session).enqueue("source_view",
                    f"view:{rev.id}:{view.concept_id}:{view.aspect}:{rev.metadata_version}",
                    {"sourceRevisionId": rev.id, "conceptId": view.concept_id, "aspect": view.aspect,
                     "metadataVersion": rev.metadata_version})
            return {"metadataVersion": rev.metadata_version, "changed": True,
                    "invalidatedViews": len(views), "reembeddingRequired": False}

    async def attach(self, principal, revision_id, conversation_id):
        from knowledge.conversations.repository import ConversationRepository
        async with self.sessions() as session, session.begin():
            await ConversationRepository(session).owned(conversation_id, principal.id, lock=True)
            return await DocumentRepository(session).attach(principal, revision_id, conversation_id)
