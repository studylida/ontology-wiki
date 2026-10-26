"""Opt-in paid ontology verification in a fresh, isolated local development schema.

Each --source-revision causes at most one sequential generation call. No retry,
embedding, or public data write is performed. The report contains derived results
and usage, not full source bodies, source file paths, or authentication data.
Use --keep-schema to retain only the newly created schema for later inspection.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from knowledge.core.config import get_settings
from knowledge.core.database import Base
from knowledge.core.errors import AppError
from knowledge.core.ids import utcnow
from knowledge.core.usage import summarize_usage, unknown_usage
from knowledge.documents.entities import Document, DocumentRevision, Passage
from knowledge.identity.entities import User
from knowledge.integrations.providers import get_generation_client
from knowledge.jobs.entities import Job
from knowledge.ontology.entities import Concept, ConceptRelation, ConceptSourceView
from knowledge.ontology.extraction import POLICY, process_ontology_job
from knowledge.ontology.identity import normalize_label
from knowledge.registry import load_entities


def check_target(settings, args):
    if not args.allow_live:
        raise ValueError("Explicit --allow-live is required; no model call was made")
    url = make_url(settings.database_url)
    if (url.get_backend_name() != "postgresql" or url.host not in ("localhost", "127.0.0.1", "::1")
            or not (url.database or "").endswith("_dev")):
        raise ValueError("Verification requires local PostgreSQL with a database name ending in _dev")
    if settings.provider_mode != "live" or settings.generation_model != "gpt-6-luna":
        raise ValueError("Explicit live gpt-6-luna configuration is required; no model call was made")
    if not re.fullmatch(r"ow_live_[a-z0-9_]{1,24}", args.schema_prefix):
        raise ValueError("Schema prefix must start with ow_live_ and contain only lowercase letters, digits and underscores")
    if not args.source_revision or len(args.source_revision) != len(set(args.source_revision)):
        raise ValueError("Provide each selected source revision exactly once")
    if args.output.exists():
        raise ValueError("Output already exists; choose a new report path")


def _row_values(row):
    return {column.key: getattr(row, column.key) for column in row.__table__.columns}


def _safe_error(exc):
    if isinstance(exc, AppError):
        return {"type": type(exc).__name__, "code": exc.code, "message": exc.message,
                "retryable": exc.retryable}
    # Driver/validation messages can include SQL parameters or source text.
    return {"type": type(exc).__name__, "code": "verification_failed", "retryable": False}


def write_report(path: Path, report: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix="ontology-report-", suffix=".tmp", delete=False) as handle:
        tmp = Path(handle.name)
        try:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    os.replace(tmp, path)


async def read_selected_sources(sessions, revision_ids):
    """The caller supplies an engine explicitly mapped to public, never the clone."""
    async with sessions() as session, session.begin():
        await session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        rows = (await session.execute(select(DocumentRevision, Document).join(Document).where(
            DocumentRevision.id.in_(revision_ids)))).all()
        by_id = {revision.id: (revision, document) for revision, document in rows}
        if set(by_id) != set(revision_ids):
            raise AppError(422, "source_not_found", "선택한 판본을 모두 찾지 못했습니다.")
        owners = {document.owner_id for _, document in rows}
        found_owners = set((await session.scalars(select(User.id).where(User.id.in_(owners)))).all())
        if owners != found_owners:
            raise AppError(422, "source_owner_missing", "선택한 문헌의 소유자 참조를 확인할 수 없습니다.")
        sources = []
        for revision_id in revision_ids:
            revision, document = by_id[revision_id]
            if (document.withdrawn or document.visibility != "shared_candidate"
                    or revision.review_status != "approved" or document.active_revision_id != revision.id):
                raise AppError(422, "source_not_public_active", "검증에는 승인된 현재 공용 판본만 사용할 수 있습니다.")
            passages = list((await session.scalars(select(Passage).where(
                Passage.source_revision_id == revision.id).order_by(Passage.ordinal))).all())
            if not any(not passage.excluded for passage in passages):
                raise AppError(422, "source_has_no_passages", "선택한 문헌에 읽을 수 있는 구간이 없습니다.")
            document_values = _row_values(document)
            # Only the explicitly selected active revision exists in the clone.
            document_values.update(current_revision_id=revision.id, active_revision_id=revision.id)
            sources.append({"document": document_values, "revision": _row_values(revision),
                            "passages": [_row_values(passage) for passage in passages]})
        return sources, owners


async def clone_sources(sessions, sources, owners):
    async with sessions() as session, session.begin():
        for owner_id in sorted(owners):
            session.add(User(id=owner_id, username="verification-" + hashlib.sha256(owner_id.encode()).hexdigest()[:24],
                password_hash="!disabled-isolated-verification!", role="user", kind="user", permissions=[],
                is_active=False, auto_wiki=False))
        await session.flush()
        for source in sources:
            session.add(Document(**source["document"]))
        await session.flush()
        for source in sources:
            session.add(DocumentRevision(**source["revision"]))
        await session.flush()
        for source in sources:
            session.add_all(Passage(**values) for values in source["passages"])


class ObservedGeneration:
    """Keep received usage even if a later local persistence step fails."""
    def __init__(self, client):
        self.client, self.model, self.usage, self.invocations = client, client.model, None, 0

    async def stream(self, messages, **kwargs):
        self.invocations += 1
        try:
            async for delta in self.client.stream(messages, **kwargs):
                if delta.usage is not None:
                    self.usage = delta.usage
                yield delta
        except BaseException as exc:
            if getattr(exc, "usage", None) is not None:
                self.usage = exc.usage
            raise

    def observed_usage(self):
        if self.usage is not None:
            return self.usage
        return {**unknown_usage("ontology_extraction", self.model), "calls": self.invocations}


async def collect_derivatives(sessions):
    async with sessions() as session:
        concepts = list((await session.scalars(select(Concept).order_by(Concept.id))).all())
        views = list((await session.scalars(select(ConceptSourceView).order_by(ConceptSourceView.id))).all())
        relations = list((await session.scalars(select(ConceptRelation).order_by(ConceptRelation.id))).all())
        labels = defaultdict(set)
        for concept in concepts:
            for label in [concept.name, *concept.aliases]:
                labels[normalize_label(label)].add(concept.id)
        for view in views:
            if view.status == "active":
                for label in view.extractor.get("sourceLabels", []):
                    labels[normalize_label(label)].add(view.concept_id)
        return {
            "concepts": [{"id": c.id, "name": c.name, "type": c.type, "aliases": c.aliases,
                          "description": c.description, "evidenceRefs": c.evidence_refs} for c in concepts],
            "sourceViews": [{"id": v.id, "conceptId": v.concept_id, "sourceRevisionId": v.source_revision_id,
                "aspect": v.aspect, "summary": v.summary, "conditions": v.conditions, "attribution": v.attribution,
                "status": v.status, "extractionStatus": v.extraction_status, "evidenceRefs": v.evidence_refs,
                "metadataVersion": v.metadata_version, "extractor": v.extractor} for v in views],
            "relations": [{"id": r.id, "fromConceptId": r.from_concept_id, "toConceptId": r.to_concept_id,
                "type": r.type, "summary": r.summary, "conditions": r.conditions, "status": r.status,
                "evidenceRefs": r.evidence_refs, "extractor": r.extractor} for r in relations],
            "duplicateLabels": [{"label": label, "conceptIds": sorted(ids)} for label, ids in sorted(labels.items()) if len(ids) > 1],
            "alternativeRelationsWithoutConditions": [r.id for r in relations if r.type == "alternative_to" and not (r.conditions or "").strip()],
        }


async def verify(args, settings):
    check_target(settings, args)
    load_entities()
    schema = args.schema_prefix + uuid4().hex[:16]
    report = {"checkedAt": datetime.now(timezone.utc).isoformat(), "status": "running",
        "scope": "explicit_live_ontology_in_fresh_development_schema", "schema": schema,
        "model": settings.generation_model, "policy": POLICY, "automaticRetry": False,
        "schemaRetained": False, "plannedGenerationCalls": len(args.source_revision),
        "publicDataWrites": False, "embeddingsCopiedOrCalled": False, "retrievalValidated": False,
        "ownerCredentialsCopied": False, "fullSourcesIncludedInReport": False,
        "semanticValidation": "not_human_reviewed", "jobs": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Claim only a new report path; subsequent atomic writes update our own file.
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write("{}\n")
    os.chmod(args.output, 0o600)
    public_engine = create_async_engine(settings.database_url,
        connect_args={"server_settings": {"search_path": "public"}},
        execution_options={"schema_translate_map": {None: "public"}})
    clone_engine, created = None, False
    try:
        public_sessions = async_sessionmaker(public_engine, expire_on_commit=False, autoflush=False)
        sources, owners = await read_selected_sources(public_sessions, args.source_revision)
        report["sources"] = [{"documentId": s["document"]["id"], "sourceRevisionId": s["revision"]["id"],
            "title": s["document"]["title"], "metadataVersion": s["revision"]["metadata_version"],
            "publisherId": s["revision"]["metadata_json"].get("publisherId"),
            "passageCount": len(s["passages"]), "readPassageLimit": 16} for s in sources]
        async with public_engine.begin() as connection:
            if not await connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')")):
                raise AppError(422, "vector_extension_missing", "개발 DB의 기존 pgvector 확장이 필요합니다.")
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        created = True
        clone_engine = create_async_engine(settings.database_url,
            connect_args={"server_settings": {"search_path": f"{schema},public"}},
            execution_options={"schema_translate_map": {None: schema}})
        async with clone_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            count = await connection.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_schema=:schema"), {"schema": schema})
            if count != len(Base.metadata.tables) or await connection.scalar(select(func.current_schema())) != schema:
                raise AppError(500, "schema_isolation_failed", "검증 schema 격리를 확인하지 못했습니다.")
        sessions = async_sessionmaker(clone_engine, expire_on_commit=False, autoflush=False)
        await clone_sources(sessions, sources, owners)
        # Credential access/provider creation happens only after all opt-in guards.
        generator = get_generation_client(settings)
        for source in sources:
            revision_id = source["revision"]["id"]
            async with sessions() as session, session.begin():
                job = Job(kind="ontology_extract", owner_id=source["document"]["owner_id"],
                    dedupe_key=f"live-verify:{schema}:{revision_id}",
                    payload={"sourceRevisionId": revision_id, "metadataVersion": source["revision"]["metadata_version"]},
                    status="running", attempts=1, started_at=utcnow())
                session.add(job)
                await session.flush()
                job_id = job.id
            observed = ObservedGeneration(generator)
            try:
                result = await process_ontology_job(sessions, observed, job_id, settings)
                item = {"jobId": job_id, "sourceRevisionId": revision_id, **result}
            except (Exception, asyncio.CancelledError) as exc:
                item = {"jobId": job_id, "sourceRevisionId": revision_id, "status": "failed",
                        "error": _safe_error(exc), "usage": getattr(exc, "usage", None) or observed.observed_usage()}
            item["adapterInvocations"] = observed.invocations
            # Write observed usage before another database operation can fail.
            report["jobs"].append(item)
            write_report(args.output, report)
            async with sessions() as session, session.begin():
                job = await session.get(Job, job_id)
                job.status, job.finished_at = item["status"], utcnow()
                job.usage, job.error = item.get("usage"), item.get("error")
                job.result = {k: v for k, v in item.items() if k not in ("usage", "error")}
            if item["status"] != "succeeded":
                break
        report.update(await collect_derivatives(sessions))
        report["status"] = "succeeded" if len(report["jobs"]) == len(sources) and all(j["status"] == "succeeded" for j in report["jobs"]) else "failed"
    except (Exception, asyncio.CancelledError) as exc:
        report["status"], report["error"] = "failed", _safe_error(exc)
    finally:
        report["usage"] = summarize_usage([job["usage"] for job in report["jobs"] if job.get("usage") is not None])
        if clone_engine is not None:
            await clone_engine.dispose()
        if created:
            if args.keep_schema:
                report["schemaRetained"] = True
            else:
                try:
                    async with public_engine.begin() as connection:
                        await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
                except Exception as exc:
                    report["schemaRetained"], report["cleanupError"] = True, _safe_error(exc)
                    report["status"] = "failed"
        await public_engine.dispose()
        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        write_report(args.output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true", required=True)
    parser.add_argument("--source-revision", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema-prefix", default="ow_live_ontology_")
    parser.add_argument("--keep-schema", action="store_true")
    args = parser.parse_args()
    try:
        settings = get_settings()
        check_target(settings, args)
    except Exception as exc:
        parser.error(str(exc) if isinstance(exc, ValueError) and type(exc) is ValueError else "Invalid verification configuration; no model call was made")
    try:
        report = asyncio.run(verify(args, settings))
    except Exception as exc:
        # Never print a traceback containing a DSN, key, or original source input.
        print(json.dumps({"status": "failed", "error": _safe_error(exc)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps({"status": report["status"], "schema": report["schema"],
        "schemaRetained": report["schemaRetained"], "jobs": len(report["jobs"]),
        "report": str(args.output)}, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "succeeded" else 1)


if __name__ == "__main__":
    main()
