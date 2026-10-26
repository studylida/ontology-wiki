"""Import the frozen evaluation corpus and cached vectors into a DEV database only.

No model calls occur. Cached embedding inputs are preserved byte-for-byte; parser
improvements apply to new documents, never silently to these cached vectors.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from sqlalchemy import select
from sqlalchemy.engine import make_url

from knowledge.core.errors import AppError
from knowledge.core.ids import new_id
from knowledge.documents.entities import Document, DocumentRevision, EmbeddingRecord, Passage, PassageEmbedding, ReviewDecision
from knowledge.documents.parsing import digest, frontmatter, metadata_digest, save_raw
from knowledge.identity.entities import User

ZIP_SHA = "2b4c1e438414d10f997b7460112270329547d1c5fea97fd925453e4caac9117d"
CHUNK_SHA = "8e57dd5ef4d81cf8b2d4c3b6c88115b43f79973eb03db9a1ad962ae08fff563c"
FILTER_SHA = "40f212a2d1c3f6a711bc1d5c8250bb3da37ce387cc1501d033b6dada3fd511f1"


def stable(prefix, value):
    return f"{prefix}_{uuid5(NAMESPACE_URL, value).hex}"


def publisher_id(name):
    normalized = re.sub(r"[^a-z0-9가-힣]", "", (name or "").casefold())
    known = {"samsungsemiconductor": "samsung_semiconductor", "samsungelectronics": "samsung_semiconductor",
             "skhynix": "sk_hynix", "sk하이닉스": "sk_hynix", "lamresearch": "lam_research"}
    return known.get(normalized, normalized or None)


async def attach_cached_vector(session, passage_id, input_hash, profile, vector_values):
    existing = await session.scalar(select(PassageEmbedding).where(
        PassageEmbedding.passage_id == passage_id, PassageEmbedding.profile_id == profile))
    if existing:
        return False
    vector = await session.scalar(select(EmbeddingRecord).where(EmbeddingRecord.scope == "shared",
        EmbeddingRecord.profile_id == profile, EmbeddingRecord.input_hash == input_hash))
    if vector is None:
        vector = EmbeddingRecord(id=new_id("vec"), scope="shared", profile_id=profile,
            input_hash=input_hash, vector=vector_values)
        session.add(vector)
        await session.flush()
    session.add(PassageEmbedding(passage_id=passage_id, profile_id=profile, embedding_id=vector.id))
    await session.flush()
    return True


async def import_evaluation(sessions, settings, args):
    database = make_url(settings.database_url).database or ""
    if not args.approve_for_development or not database.endswith(("_dev", "_test")):
        raise ValueError("Evaluation approval is restricted to an explicitly named _dev or _test database")
    root, archive_path = Path(args.evaluation_dir), Path(args.corpus_zip)
    chunk_path, filter_path = root / "data/chunks.jsonl", root / "navigation_chunk_filter_v1.json"
    for path, expected in ((archive_path, ZIP_SHA), (chunk_path, CHUNK_SHA), (filter_path, FILTER_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen input hash mismatch: {path.name}")
    chunks = [json.loads(line) for line in chunk_path.read_text().splitlines()]
    exclusions = set(json.loads(filter_path.read_text())["excluded_chunk_ids"])
    vectors_file = root / "cache" / f"corpus-{args.model}.npz"
    cached = np.load(vectors_file, allow_pickle=False)
    if list(cached["ids"]) != [c["chunk_id"] for c in chunks]:
        raise ValueError("Cached vector row identity mismatch")
    api_dimensions = 3072 if args.model.endswith("large") else 1536
    transform = "prefix_l2" if api_dimensions == 3072 else "native"
    profile = f"openai:{args.model}:api{api_dimensions}:stored1536:{transform}:v1"
    if cached["vectors"].shape != (len(chunks), api_dimensions):
        raise ValueError("Cached vector dimensions do not match the declared model profile")
    matrix = cached["vectors"][:, :1536].astype(np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if not np.isfinite(matrix).all() or not np.isfinite(norms).all() or (norms == 0).any():
        raise ValueError("Cached embeddings must be finite nonzero vectors")
    matrix /= norms
    grouped = defaultdict(list)
    for index, chunk in enumerate(chunks):
        if digest(chunk["embedding_text"]) != chunk["embedding_input_sha256"]:
            raise ValueError("Embedding input changed")
        grouped[chunk["source_path"]].append((index, chunk))
    imported, reused, included = 0, 0, 0
    async with sessions() as session, session.begin():
        owner = await session.scalar(select(User).where(User.username == args.owner))
        if not owner:
            raise ValueError("Create the named development reviewer account first")
        with zipfile.ZipFile(archive_path) as archive:
            for source_path, rows in grouped.items():
                origin = f"evaluation:{ZIP_SHA}:{source_path}"
                doc = await session.scalar(select(Document).where(Document.origin_key == origin))
                if doc:
                    expected_revision = stable("rev", origin + ":1")
                    if doc.current_revision_id != expected_revision:
                        raise ValueError("Imported source has a newer revision; cached inputs cannot overwrite it")
                    for index, chunk in rows:
                        p_id = stable("psg", ZIP_SHA + chunk["chunk_id"])
                        passage = await session.get(Passage, p_id)
                        if passage is None or passage.input_hash != chunk["embedding_input_sha256"]:
                            raise ValueError("Stored passage no longer matches the frozen embedding input")
                        if not passage.excluded:
                            included += int(await attach_cached_vector(session, p_id, passage.input_hash,
                                profile, matrix[index].tolist()))
                    reused += 1
                    continue
                body = archive.read(source_path)
                text = body.decode("utf-8")
                declared = frontmatter(text)
                metadata = {"url": declared.get("source_url"), "publisher": declared.get("publisher"),
                    "publisherId": publisher_id(declared.get("publisher")), "author": declared.get("author"),
                    "attributedTo": None, "attributionBasis": "provided_metadata_unverified",
                    "sourceType": declared.get("type", "unknown"), "publishedAt": None,
                    "sourcePath": source_path, "originalMetadata": json.loads(json.dumps(declared, default=str)),
                    "authenticity": "not_verified_in_import", "developmentEvaluationCorpus": True}
                doc_id, rev_id = stable("doc", origin), stable("rev", origin + ":1")
                doc = Document(id=doc_id, owner_id=owner.id, title=rows[0][1]["title"],
                    visibility="shared_candidate", origin_key=origin)
                session.add(doc)
                await session.flush()
                rev = DocumentRevision(id=rev_id, document_id=doc_id, revision=1, content=text,
                    content_hash=digest(text), raw_path=save_raw(settings.storage_path, body),
                    metadata_json=metadata, metadata_hash=metadata_digest(metadata),
                    review_status="approved", index_status="ready", index_snapshot_id=stable("idx", origin + profile))
                session.add(rev)
                await session.flush()
                doc.current_revision_id = doc.active_revision_id = rev_id
                for ordinal, (index, chunk) in enumerate(rows):
                    p_id = stable("psg", ZIP_SHA + chunk["chunk_id"])
                    excluded = chunk["chunk_id"] in exclusions
                    passage = Passage(id=p_id, source_revision_id=rev_id, ordinal=ordinal, text=chunk["text"],
                        locator=chunk["section_path"] or "본문", start_offset=chunk["start"], end_offset=chunk["end"],
                        embedding_text=chunk["embedding_text"], input_hash=chunk["embedding_input_sha256"],
                        excluded=excluded, exclusion_reason="frozen_navigation_filter_v1" if excluded else None)
                    session.add(passage)
                    if excluded:
                        continue
                    await session.flush()
                    included += int(await attach_cached_vector(session, p_id, passage.input_hash,
                        profile, matrix[index].tolist()))
                session.add(ReviewDecision(source_revision_id=rev_id, reviewer_id=owner.id,
                    decision="approve", reason="명시적 개발 평가용 반입. 운영 승인·전문가 검증·출처 진위 인증이 아닙니다."))
                imported += 1
                await session.flush()
    return {"documentsImported": imported, "documentsAlreadyPresent": reused, "indexedPassages": included,
            "excludedPassages": len(exclusions), "profileId": profile, "modelCalls": 0,
            "corpusSha256": ZIP_SHA, "developmentOnly": True}
