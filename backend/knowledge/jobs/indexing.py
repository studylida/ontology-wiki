"""Incremental indexing with an atomic activation boundary and reusable vectors."""
from __future__ import annotations

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from knowledge.core.errors import AppError
from knowledge.core.ids import new_id, utcnow
from knowledge.core.usage import summarize_usage, unknown_usage
from knowledge.documents.entities import Document, DocumentRevision, EmbeddingRecord, Passage, PassageEmbedding
from knowledge.jobs.entities import Job, SchedulerState
from knowledge.jobs.repository import JobRepository


async def enqueue_index(session, revision, profile_id, owner_id=None, *, immediate=True):
    fingerprint = hashlib.sha256(profile_id.encode()).hexdigest()[:16]
    key = f"index:{revision.id}:{fingerprint}:meta{revision.metadata_version}"
    job = await JobRepository(session).enqueue("index", key,
        {"sourceRevisionId": revision.id, "profileId": profile_id, "metadataVersion": revision.metadata_version}, owner_id)
    if (immediate and job.status in ("failed", "cancelled", "superseded")) or (job.status == "succeeded" and revision.index_status != "ready"):
        JobRepository.restart(job)
    if immediate and job.status == "pending":
        job.available_at = utcnow()
    return job


async def schedule_daily(sessions, settings, profile_id, *, now=None):
    now = now or utcnow()
    local = now.astimezone(ZoneInfo(settings.index_timezone))
    if local.hour < settings.index_hour_local:
        return 0
    day = local.date().isoformat()
    async with sessions() as session, session.begin():
        await session.execute(insert(SchedulerState).values(key="daily_index", value="").on_conflict_do_nothing())
        state = await session.get(SchedulerState, "daily_index", with_for_update=True)
        if state.value == day:
            return 0
        # Only the latest reviewed revision is enqueued; running jobs keep fixed input.
        revisions = list((await session.scalars(select(DocumentRevision).join(Document).where(
            Document.current_revision_id == DocumentRevision.id, DocumentRevision.review_status == "approved",
            DocumentRevision.index_status != "ready", Document.withdrawn.is_(False),
            Document.visibility == "shared_candidate"))).all())
        for revision in revisions:
            await enqueue_index(session, revision, profile_id, immediate=False)
        state.value, state.updated_at = day, now
        return len(revisions)


async def process_index_job(sessions, embedding_client, job_id):
    async with sessions() as session, session.begin():
        job = await session.get(Job, job_id, with_for_update=True)
        if not job or job.status != "running":
            return {"status": "cancelled"}
        revision = await session.get(DocumentRevision, job.payload["sourceRevisionId"], with_for_update=True)
        document = await session.get(Document, revision.document_id, with_for_update=True)
        expected_meta = job.payload["metadataVersion"]
        if (revision.review_status != "approved" or document.visibility != "shared_candidate" or document.withdrawn or document.current_revision_id != revision.id
            or revision.metadata_version != expected_meta):
            return {"status": "superseded", "reason": "source_changed_before_index"}
        if job.payload["profileId"] != embedding_client.profile_id:
            raise AppError(409, "embedding_profile_changed", "작업의 임베딩 프로필과 현재 설정이 다릅니다.")
        if document.active_revision_id != revision.id:
            revision.index_status = "indexing"
        passages = list((await session.scalars(select(Passage).where(Passage.source_revision_id == revision.id,
            Passage.excluded.is_(False)).order_by(Passage.ordinal))).all())
        inputs = [{"id": p.id, "text": p.embedding_text, "hash": p.input_hash} for p in passages]
        revision_id, document_id, scope = revision.id, document.id, "shared"
    if not inputs:
        raise AppError(422, "no_indexable_passages", "색인할 본문 구간이 없습니다.")
    usage, reused, embedded = [], 0, 0
    # Cache work may commit before activation; it is never visible as active source.
    for offset in range(0, len(inputs), 32):
        batch = inputs[offset:offset + 32]
        async with sessions() as session:
            job = await session.get(Job, job_id)
            if job.status != "running":
                return {"status": "cancelled", "usage": summarize_usage(usage)}
            records = list((await session.scalars(select(EmbeddingRecord).where(
                EmbeddingRecord.scope == scope, EmbeddingRecord.profile_id == embedding_client.profile_id,
                EmbeddingRecord.input_hash.in_([p["hash"] for p in batch])))).all())
            cached = {r.input_hash: r.id for r in records}
        missing_by_hash = {p["hash"]: p["text"] for p in batch if p["hash"] not in cached}
        vectors = None
        if missing_by_hash:
            response = None
            try:
                response = await embedding_client.embed(list(missing_by_hash.values()))
                usage.append(response.usage)
                vectors = dict(zip(missing_by_hash, response.vectors, strict=True))
            except Exception as exc:
                observed = getattr(exc, "usage", None)
                if observed:
                    usage.append(observed)
                elif getattr(exc, "code", None) != "configuration_blocked" and response is None:
                    usage.append(unknown_usage("document_embedding", getattr(embedding_client, "model", None),
                        source="fixture" if embedding_client.profile_id.startswith("fixture:") else "provider"))
                exc.usage = summarize_usage(usage)
                raise
        async with sessions() as session, session.begin():
            job = await session.get(Job, job_id, with_for_update=True)
            if job.status != "running":
                return {"status": "cancelled", "usage": summarize_usage(usage)}
            for item in batch:
                if item["hash"] not in cached:
                    values = dict(id=new_id("vec"), scope=scope, profile_id=embedding_client.profile_id,
                                  input_hash=item["hash"], vector=vectors[item["hash"]])
                    await session.execute(insert(EmbeddingRecord).values(**values).on_conflict_do_nothing(
                        index_elements=["scope", "profile_id", "input_hash"]))
                    record = await session.scalar(select(EmbeddingRecord).where(EmbeddingRecord.scope == scope,
                        EmbeddingRecord.profile_id == embedding_client.profile_id, EmbeddingRecord.input_hash == item["hash"]))
                    cached[item["hash"]] = record.id
                    embedded += 1
                else:
                    reused += 1
                await session.execute(insert(PassageEmbedding).values(id=new_id("pe"), passage_id=item["id"],
                    profile_id=embedding_client.profile_id, embedding_id=cached[item["hash"]]).on_conflict_do_nothing(
                    index_elements=["passage_id", "profile_id"]))
            job.progress = {"processed": min(offset + 32, len(inputs)), "total": len(inputs),
                            "embedded": embedded, "reused": reused}
            job.usage = summarize_usage(usage)
    async with sessions() as session, session.begin():
        job = await session.get(Job, job_id, with_for_update=True)
        revision = await session.get(DocumentRevision, revision_id, with_for_update=True)
        document = await session.get(Document, document_id, with_for_update=True)
        if (job.status != "running" or document.visibility != "shared_candidate" or document.withdrawn or revision.review_status != "approved"
            or document.current_revision_id != revision.id or revision.metadata_version != expected_meta):
            if revision.index_status == "indexing":
                revision.index_status = "pending"
            return {"status": "superseded", "reason": "source_changed_before_activation", "usage": summarize_usage(usage)}
        snapshot_id = new_id("idx")
        revision.index_status, revision.index_snapshot_id = "ready", snapshot_id
        document.active_revision_id, document.updated_at = revision.id, utcnow()
        extraction = await JobRepository(session).enqueue("ontology_extract", f"ontology:{revision.id}:meta{expected_meta}:v1",
            {"sourceRevisionId": revision.id, "metadataVersion": expected_meta})
        from knowledge.ontology.entities import ConceptSourceView
        withdrawn_views = await session.scalar(select(ConceptSourceView.id).where(
            ConceptSourceView.source_revision_id == revision.id, ConceptSourceView.status == "withdrawn").limit(1))
        if withdrawn_views and extraction.status in ("succeeded", "failed", "cancelled", "superseded"):
            JobRepository.restart(extraction)
        return {"status": "succeeded", "sourceRevisionId": revision.id, "indexSnapshotId": snapshot_id,
                "indexedPassages": len(inputs), "embedded": embedded, "reused": reused, "usage": summarize_usage(usage)}
