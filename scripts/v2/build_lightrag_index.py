"""Build a separate PostgreSQL graph from approved active source passages."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from knowledge.core.config import Settings
from knowledge.documents.entities import Document, DocumentRevision
from knowledge.documents.repository import public_scope
from knowledge.integrations.lightrag_manifest import capture_graph_snapshot
from knowledge.integrations.lightrag import (
    activate_index, _read_usage, load_build_request, prepare_build_extension, save_build_extension,
)
from knowledge.integrations.lightrag_runner import write_json
from knowledge.integrations.providers import get_embedding_client
from knowledge.registry import load_entities


async def export_sources(settings, source_manifest: Path | None):
    engine = create_async_engine(settings.database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            if source_manifest:
                expected = json.loads(source_manifest.read_text(encoding="utf-8"))
                revision_ids = [row["revisionId"] for row in expected]
            else:
                expected = None
                revision_ids = list((await session.scalars(select(DocumentRevision.id).join(Document).where(
                    Document.active_revision_id == DocumentRevision.id, public_scope(),
                    DocumentRevision.index_status == "ready"))).all())
            manifest, documents = await capture_graph_snapshot(session, revision_ids,
                get_embedding_client(settings).profile_id, include_documents=True)
            if expected:
                by_id = {row["sourceRevisionId"]: row for row in manifest["revisions"]}
                for row in expected:
                    actual = by_id[row["revisionId"]]
                    if any(actual[key] != row[key] for key in ("contentHash", "metadataHash", "metadataVersion")):
                        raise ValueError("Frozen evaluation source has changed")
        return manifest, documents
    finally:
        await engine.dispose()


async def ensure_database(settings, name: str):
    import asyncpg
    if not re.fullmatch(r"ontology_lightrag_[a-z0-9_]+_dev|ontology_lightrag_dev", name):
        raise ValueError("Dedicated LightRAG development database name required")
    url = make_url(settings.database_url)
    if url.database == name or not (url.database.endswith("_dev") or "test" in url.database):
        raise ValueError("Separate application development database required")
    connection = await asyncpg.connect(host=url.host, port=url.port or 5432,
        user=url.username, password=url.password, database="postgres")
    try:
        if not await connection.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", name):
            await connection.execute(f'CREATE DATABASE "{name}"')
    finally:
        await connection.close()


async def main(args):
    load_dotenv(ROOT / ".env", override=False)
    load_entities()
    settings = Settings()
    if settings.provider_mode != "live":
        raise ValueError("An explicitly configured live provider is required")
    if args.max_model_calls is not None and args.max_model_calls <= 0:
        raise ValueError("Model call budget must be positive")
    if args.generation_concurrency is not None and not 1 <= args.generation_concurrency <= 8:
        raise ValueError("Graph generation concurrency must be between 1 and 8")
    index_root = args.index_path.resolve()
    if (args.extend or args.request_file) and not args.resume:
        raise ValueError("Build extension/request selection requires --resume")
    extension_audit = None
    if args.resume:
        run_path = args.resume.resolve()
        if run_path.parent != index_root / "builds":
            raise ValueError("Resume build must belong to the selected index path")
        request_path = (args.request_file or run_path / "build-request.json").resolve()
        if request_path.parent != run_path:
            raise ValueError("Resume request must belong to its build directory")
        request = load_build_request(request_path)
        manifest, documents = await export_sources(settings, args.source_manifest)
        if args.extend:
            active_path = index_root / "active.json"
            active = json.loads(active_path.read_text(encoding="utf-8")) if active_path.exists() else None
            request, extension_audit = prepare_build_extension(request, manifest, documents, active)
        elif manifest["fingerprint"] != request["index"]["snapshot"]["fingerprint"]:
            raise ValueError("Cannot resume a changed source snapshot")
        if args.max_model_calls is not None:
            request["maxModelCalls"] = args.max_model_calls
        if args.generation_concurrency is not None:
            request["index"]["generationMaxAsync"] = args.generation_concurrency
    else:
        manifest, documents = await export_sources(settings, args.source_manifest)
        if args.include_title:
            documents = [doc for doc in documents if any(term.casefold() in doc["title"].casefold()
                for term in args.include_title)]
        if not documents:
            raise ValueError("No approved documents selected")
        run_id = uuid4().hex
        run_path = index_root / "builds" / run_id
        index = {"schemaVersion": 1, "status": "building", "storage": "postgresql",
            "runtimeVersion": "lightrag-hku==1.5.7", "databaseName": args.database_name,
            "workspace": f"ow_{manifest['fingerprint'][:16]}_{run_id[:8]}", "snapshot": manifest,
            "indexedRevisionIds": [doc["sourceRevisionId"] for doc in documents],
            "sourceForms": {doc["sourceRevisionId"]: doc["documentForm"] for doc in documents},
            "generationModel": settings.generation_model, "generationEffort": settings.generation_effort,
            "generationMaxAsync": args.generation_concurrency or 2,
            "embeddingModel": settings.embedding_model, "embeddingDimensions": settings.embedding_dimensions,
            "embeddingApiDimensions": settings.embedding_api_dimensions, "embeddingTransform": settings.embedding_transform}
        request = {"action": "build", "index": index, "documents": documents,
            "maxModelCalls": args.max_model_calls or 1000, "workingDirectory": str(run_path / "runtime"),
            "usagePath": str(run_path / "usage.json"), "progressPath": str(run_path / "progress.json")}
        request_path = run_path / "build-request.json"
        write_json(request_path, request)
    if extension_audit is not None:
        request_path = save_build_extension(run_path, request_path, request, extension_audit)
    brief = {"runPath": str(run_path), "snapshotFingerprint": request["index"]["snapshot"]["fingerprint"],
        "snapshotRevisions": len(request["index"]["snapshot"]["revisions"]),
        "indexedRevisions": len(request["documents"]),
        "passages": sum(len(doc["passages"]) for doc in request["documents"]),
        "characters": sum(len(p["embeddingText"]) for doc in request["documents"] for p in doc["passages"]),
        "maxModelCalls": request["maxModelCalls"],
        "generationMaxAsync": request["index"].get("generationMaxAsync", 2),
        "resumeRequestFile": str(request_path)}
    write_json(run_path / "summary.json", brief)
    print(json.dumps({"status": "prepared", **brief}, ensure_ascii=False), flush=True)
    if args.export_only:
        return
    active_path = index_root / "active.json"
    if active_path.exists():
        active = json.loads(active_path.read_text(encoding="utf-8"))
        if active.get("workspace") == request["index"]["workspace"]:
            raise ValueError("Cannot build into the active graph workspace")
    await ensure_database(settings, request["index"]["databaseName"])
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend"), "PYTHONIOENCODING": "utf-8"}
    process = subprocess.Popen([str(args.runtime_python), "-m", "knowledge.integrations.lightrag_runner"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, cwd=ROOT, creationflags=0x08000000 if os.name == "nt" else 0)
    try:
        stdout, _ = process.communicate(json.dumps(request, ensure_ascii=False).encode(), timeout=args.timeout_seconds)
        try:
            result = json.loads(stdout)
            if not isinstance(result, dict):
                raise ValueError("Invalid runtime response")
        except (ValueError, UnicodeDecodeError):
            result = {"status": "failed", "reason": "runtime_protocol_error",
                "usage": _read_usage(Path(request["usagePath"]), interrupted=True)}
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        process.kill()
        process.communicate()
        result = {"status": "failed", "reason": "build_timeout" if isinstance(exc, subprocess.TimeoutExpired) else "build_cancelled",
            "usage": _read_usage(Path(request["usagePath"]), interrupted=True)}
    write_json(run_path / "result.json", result)
    if process.returncode or result.get("status") != "ready":
        print(json.dumps({"status": "failed", "reason": result.get("reason"), "runPath": str(run_path)}, ensure_ascii=False))
        raise SystemExit(1)
    current, _ = await export_sources(settings, args.source_manifest)
    if current["fingerprint"] != request["index"]["snapshot"]["fingerprint"]:
        print(json.dumps({"status": "stale", "runPath": str(run_path)}, ensure_ascii=False))
        raise SystemExit(1)
    activate_index(index_root, result, current)
    print(json.dumps({"status": "ready", **brief, "elapsedSeconds": result["elapsedSeconds"],
        "usage": {field: result["usage"][field] for field in (
            "calls", "costUsd", "knownCostUsd", "unknownCostCalls", "inputTokens", "outputTokens", "totalTokens")}}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-python", type=Path, required=True)
    parser.add_argument("--index-path", type=Path, default=ROOT / "var/lightrag")
    parser.add_argument("--database-name", default="ontology_lightrag_dev")
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--include-title", action="append", default=[])
    parser.add_argument("--max-model-calls", type=int)
    parser.add_argument("--generation-concurrency", type=int)
    parser.add_argument("--timeout-seconds", type=float, default=3600)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--extend", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    try:
        asyncio.run(main(parser.parse_args()))
    except Exception as exc:
        print(json.dumps({"status": "failed", "reason": type(exc).__name__}))
        raise SystemExit(1)
