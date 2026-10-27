"""Hash-checked local corpus intake through the existing document/review/job services.

The named active reviewer authorizes this explicit development administration run.
No browser token is read. Private environment values stay inside this process.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
from time import monotonic
from urllib.parse import unquote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def canonical_lineage(url):
    parsed = urlsplit(url)
    if parsed.hostname in ("doi.org", "dx.doi.org"):
        return "doi:" + unquote(parsed.path).strip("/").lower()
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), unquote(parsed.path).rstrip("/"), parsed.query, ""))


def job_usage_components(job):
    usages = [attempt.get("usage") for attempt in (job.result or {}).get("attemptHistory", [])] + [job.usage]
    return [component for usage in usages if usage for component in usage.get("components", [usage])]


def checked_file(value, expected, manifest_path):
    path = Path(value)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not (path.is_relative_to(ROOT / "var") or path.is_relative_to(manifest_path.parent.resolve())):
        raise ValueError("Corpus files must be under var or the manifest directory")
    if path.name.startswith(".env") or path.name == "login.local.txt":
        raise ValueError("Private configuration is not corpus material")
    body = path.read_bytes()
    if not isinstance(expected, str) or sha(body) != expected:
        raise ValueError(f"Corpus hash mismatch: {path.name}")
    return path, body


def load_manifest(path):
    path = Path(path).resolve()
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Manifest must contain a non-empty source list")
    seen, prepared = set(), []
    from knowledge.documents.dto import NewDocument
    for row in rows:
        ident = row["id"]
        if not isinstance(ident, str) or not ident.strip() or ident in seen:
            raise ValueError("Source IDs must be non-empty and unique")
        seen.add(ident)
        if row.get("decision") not in ("approve", "hold") or not row.get("review_reason") or not row.get("review_scope"):
            raise ValueError(f"Explicit review decision and scope required: {ident}")
        source_path, raw = checked_file(row["source_file"], row["source_sha256"], path)
        content_path, body = checked_file(row["content_file"], row["content_sha256"], path)
        content = body.decode("utf-8")
        form = row.get("document_form")
        if form not in ("editorial_summary", "edited_derivative", "text_extraction", "unknown"):
            raise ValueError(f"Explicit source form required: {ident}")
        request = NewDocument(title=row["title"], content=content, url=row.get("source_url"),
            publisher=row.get("publisher"), publisher_id=row.get("publisher_id"), author=row.get("author"),
            attributed_to=row.get("attributed_to"),
            attribution_basis=row.get("attribution_basis", "provided_source_text_with_recorded_editorial_review"),
            source_type=row.get("source_type", "web_document"), document_form=form,
            published_at=row.get("published_at"), visibility="shared_candidate")
        passages = None
        if row.get("passages_file"):
            _, passage_body = checked_file(row["passages_file"], row["passages_sha256"], path)
            passages = json.loads(passage_body)
            from knowledge.documents.parsing import prepared_passages
            prepared_passages(content, passages)
        lineage = row.get("lineage_key") or (canonical_lineage(row["source_url"]) if row.get("source_url") else "sha256:" + sha(raw))
        metadata = {**row.get("processing_metadata", {}), "lineageKey": lineage,
            "corpusSourceId": ident, "originalFile": str(source_path), "originalSha256": sha(raw),
            "editorialFile": str(content_path), "editorialSha256": sha(body),
            "reviewScope": row["review_scope"], "editorialCorrections": row.get("corrections", []),
            "additionalSources": row.get("additional_sources", []),
            "originalPublisher": row.get("original_publisher", row.get("publisher")),
            "editorialAuthor": row.get("editorial_author", "Codex") if form in ("edited_derivative", "editorial_summary") else None}
        artifacts = []
        for artifact in row.get("artifact_files", []):
            _, artifact_body = checked_file(artifact["path"], artifact["sha256"], path)
            relative = Path(artifact["relative_path"])
            expected_relative = Path(sha(artifact_body)[:2]) / (sha(artifact_body) + ".bin")
            if relative != expected_relative:
                raise ValueError("Artifact must use its content-addressed path")
            artifacts.append((relative, artifact_body))
        prepared.append({**row, "request": request, "raw": raw, "metadata": metadata,
            "passages": passages, "artifacts": artifacts,
            "origin_key": row.get("origin_key") or "corpus-quality:" + ident + ":" + sha(content.encode())})
    return prepared


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


async def register(rows, sessions, settings, principal, embedding, output):
    from sqlalchemy import select
    from knowledge.documents.dto import ReviewRequest
    from knowledge.documents.entities import Document, DocumentRevision
    from knowledge.documents.service import DocumentService
    from knowledge.jobs.service import JobService
    documents, jobs = DocumentService(sessions, settings), JobService(sessions, embedding.profile_id)
    principal.require("documents:write")
    principal.require("documents:review")
    principal.require("jobs:manage")
    report = {"provenance": "explicit_development_intake_as_existing_active_reviewer", "owner": principal.username,
        "embeddingProfile": embedding.profile_id, "items": []}
    for row in rows:
        async with sessions() as session:
            existing = (await session.execute(select(Document, DocumentRevision).join(DocumentRevision,
                Document.current_revision_id == DocumentRevision.id).where(Document.origin_key == row["origin_key"]))).first()
        if existing:
            doc, revision = existing
            if doc.visibility != "shared_candidate":
                raise ValueError("Existing intake origin is not a shared candidate")
            from knowledge.documents.parsing import digest
            if revision.content_hash != digest(row["request"].content):
                raise ValueError("Existing intake origin has different content")
            result = {"id": doc.id, "currentRevisionId": revision.id}
        else:
            from knowledge.documents.parsing import save_raw
            for relative, body in row["artifacts"]:
                if Path(save_raw(settings.storage_path, body)) != relative:
                    raise ValueError("Source artifact path changed during storage")
            result = await documents.create(principal, row["request"], raw_bytes=row["raw"],
                origin_key=row["origin_key"], read_scope_value=row.get("read_scope", "provided_text"),
                media_type=row.get("media_type"), processing_metadata=row["metadata"], passage_records=row["passages"])
        revision_id = result["currentRevisionId"]
        if not existing or revision.review_status != {"approve": "approved", "hold": "held"}[row["decision"]]:
            await documents.review(principal, revision_id, ReviewRequest(decision=row["decision"], reason=row["review_reason"]))
        item = {"sourceId": row["id"], "documentId": result["id"], "revisionId": revision_id,
            "decision": row["decision"], "originKey": row["origin_key"], "sourceSha256": sha(row["raw"]),
            "documentForm": row["request"].document_form, "readScope": row.get("read_scope", "provided_text")}
        if row["decision"] == "approve":
            item["jobId"] = (await jobs.enqueue_index(principal, [revision_id]))["items"][0]["id"]
        report["items"].append(item)
        dump(output, report)
    return report


async def run(args):
    rows = load_manifest(args.manifest)
    if not args.apply:
        print(json.dumps({"validated": len(rows), "apply": False, "decisions": {decision: sum(r["decision"] == decision for r in rows) for decision in ("approve", "hold")}}))
        return
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    from sqlalchemy import select
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from knowledge.core.config import Settings
    from knowledge.documents.entities import DocumentRevision
    from knowledge.jobs.entities import Job
    from knowledge.core.usage import summarize_usage
    from knowledge.identity.repository import UserRepository
    from knowledge.identity.service import principal_from_user
    from knowledge.integrations.providers import get_embedding_client
    from knowledge.registry import load_entities
    load_entities()
    settings = Settings()
    if not (make_url(settings.database_url).database or "").endswith("_dev"):
        raise ValueError("This explicit intake command is limited to a development database")
    if settings.provider_mode != "live":
        raise ValueError("Corpus publication requires the configured live embedding profile")
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    try:
        async with sessions() as session:
            user = await UserRepository(session).by_username(args.owner)
            if user is None or not user.is_active or user.kind != "user":
                raise ValueError("An existing active reviewer user is required")
            principal = principal_from_user(user)
        report = await register(rows, sessions, settings, principal, get_embedding_client(settings), args.output)
        started = monotonic()
        while True:
            async with sessions() as session:
                revisions = list((await session.scalars(select(DocumentRevision).where(DocumentRevision.id.in_(
                    [item["revisionId"] for item in report["items"]])))).all())
                related_jobs = list((await session.scalars(select(Job).where(Job.payload["sourceRevisionId"].astext.in_(
                    [item["revisionId"] for item in report["items"]])))).all())
            statuses = {r.id: {"review": r.review_status, "index": r.index_status} for r in revisions}
            for item in report["items"]:
                item.update(statuses[item["revisionId"]])
            report["allApprovedReady"] = all(item["decision"] == "hold" or item["index"] == "ready" for item in report["items"])
            report["jobs"] = [{"id": j.id, "kind": j.kind, "status": j.status, "usage": j.usage,
                "attemptHistory": (j.result or {}).get("attemptHistory", [])} for j in related_jobs]
            report["usageByJobKind"] = {kind: summarize_usage([component for j in related_jobs if j.kind == kind
                for component in job_usage_components(j)]) for kind in {j.kind for j in related_jobs}}
            report["derivedJobsSettled"] = all(j.status not in ("pending", "running") for j in related_jobs if j.kind != "index")
            dump(args.output, report)
            failed = any(j.kind == "index" and j.status == "failed" for j in related_jobs)
            if report["allApprovedReady"] or failed or monotonic() - started >= args.wait_seconds:
                print(json.dumps({"items": len(report["items"]), "allApprovedReady": report["allApprovedReady"], "report": str(args.output)}))
                if not report["allApprovedReady"]:
                    raise SystemExit(2)
                return
            await asyncio.sleep(2)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner", default="my-reviewer")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=900)
    asyncio.run(run(parser.parse_args()))
