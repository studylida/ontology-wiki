"""One manifest contract shared by graph building and authorized query snapshots."""
import hashlib
import json

from sqlalchemy import select

from ..documents.entities import Document, DocumentRevision, Passage
from .lightrag import snapshot_manifest


async def capture_graph_snapshot(session, revision_ids: list[str], embedding_profile_id: str,
                                 *, include_documents: bool = False) -> tuple[dict, list[dict]]:
    requested = set(revision_ids)
    revisions = (await session.execute(select(Document, DocumentRevision).join(
        DocumentRevision, DocumentRevision.document_id == Document.id).where(
        DocumentRevision.id.in_(requested), Document.visibility == "shared_candidate",
        Document.withdrawn.is_(False), DocumentRevision.review_status == "approved",
        DocumentRevision.index_status == "ready", Document.active_revision_id == DocumentRevision.id
    ))).all() if requested else []
    if {revision.id for _, revision in revisions} != requested:
        raise ValueError("Graph snapshot includes unavailable or non-public revisions")
    passages = (await session.scalars(select(Passage).where(
        Passage.source_revision_id.in_(requested)).order_by(Passage.source_revision_id, Passage.ordinal))).all() if requested else []
    grouped = {revision: [] for revision in requested}
    for passage in passages:
        grouped[passage.source_revision_id].append(passage)
    rows, documents = [], []
    for document, revision in revisions:
        metadata = revision.metadata_json or {}
        document_passages = grouped[revision.id]
        signature = [{"id": p.id, "inputHash": p.input_hash, "excluded": p.excluded,
                      "textHash": hashlib.sha256(p.text.encode()).hexdigest()} for p in document_passages]
        rows.append({"sourceRevisionId": revision.id, "documentId": document.id,
            "contentHash": revision.content_hash, "metadataHash": revision.metadata_hash,
            "metadataVersion": revision.metadata_version, "visibility": document.visibility,
            "withdrawn": document.withdrawn, "reviewStatus": revision.review_status,
            "activeRevisionId": document.active_revision_id,
            "titleHash": hashlib.sha256(document.title.encode()).hexdigest(),
            "parserProfile": metadata.get("parserProfile", "stored-text:v1"),
            "chunkProfile": metadata.get("chunkProfile", "markdown-char1400-overlap150:v1"),
            "documentForm": metadata.get("documentForm", "unknown"),
            "passagesHash": hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()})
        if include_documents:
            documents.append({"documentId": document.id, "sourceRevisionId": revision.id,
                "title": document.title, "documentForm": metadata.get("documentForm", "unknown"),
                "content": revision.content, "passages": [
                    {"passageId": p.id, "text": p.text, "embeddingText": p.embedding_text,
                     "inputHash": p.input_hash, "locator": p.locator} for p in document_passages if not p.excluded]})
    documents.sort(key=lambda value: value["sourceRevisionId"])
    return snapshot_manifest(rows, embedding_profile_id), documents
