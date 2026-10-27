"""Optional graph retrieval over an immutable, approved public-source snapshot."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from uuid import uuid4

from ..core.usage import summarize_usage, unknown_usage


def snapshot_manifest(revisions: list[dict], embedding_profile_id: str) -> dict:
    """Fingerprint all searchable revisions, including same-revision metadata edits.

    Callers provide only currently authorized public/approved/active revisions.
    The graph's indexed subset is separate from this complete eligibility snapshot.
    """
    rows = []
    for revision in revisions:
        required = ("sourceRevisionId", "contentHash", "metadataHash", "metadataVersion")
        if any(key not in revision or revision[key] is None for key in required):
            raise ValueError("Incomplete graph snapshot revision")
        rows.append({key: revision.get(key) for key in (
            *required, "documentId", "titleHash", "visibility", "withdrawn", "reviewStatus",
            "activeRevisionId", "parserProfile", "chunkProfile", "documentForm", "passagesHash")})
    rows.sort(key=lambda row: row["sourceRevisionId"])
    if len({row["sourceRevisionId"] for row in rows}) != len(rows):
        raise ValueError("Duplicate graph snapshot revision")
    value = {"schemaVersion": 1, "embeddingProfileId": embedding_profile_id, "revisions": rows}
    value["fingerprint"] = hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return value


def validate_index(index: dict, current: dict) -> str | None:
    if not isinstance(index, dict) or not isinstance(current, dict):
        return "invalid_manifest"
    if index.get("status") != "ready" or index.get("storage") != "postgresql":
        return "index_not_ready"
    stored_snapshot = index.get("snapshot")
    if not isinstance(stored_snapshot, dict) or not current.get("fingerprint"):
        return "invalid_manifest"
    if stored_snapshot.get("fingerprint") != current.get("fingerprint"):
        return "snapshot_changed"
    allowed = {row["sourceRevisionId"] for row in current.get("revisions", [])}
    indexed = set(index.get("indexedRevisionIds", []))
    if not indexed or not indexed.issubset(allowed):
        return "index_scope_mismatch"
    if not index.get("chunkMap"):
        return "missing_source_mapping"
    for links in index["chunkMap"].values():
        if not links or any(link.get("sourceRevisionId") not in indexed or not link.get("passageId")
                            or not link.get("textHash") for link in links):
            return "invalid_source_mapping"
    return None


def mapped_passages(index: dict, chunks: list[dict]) -> list[str]:
    """Return only exact stored text matches; one chunk may name duplicate passages."""
    result = []
    for chunk in chunks:
        links = index.get("chunkMap", {}).get(chunk.get("chunk_id"), [])
        content = chunk.get("content")
        if not isinstance(content, str):
            continue
        digest = hashlib.sha256(content.encode()).hexdigest()
        for link in links:
            if link["textHash"] == digest and link["passageId"] not in result:
                result.append(link["passageId"])
    return result


def activate_index(index_path: Path, index: dict, current_snapshot: dict) -> None:
    reason = validate_index(index, current_snapshot)
    if reason:
        raise ValueError(reason)
    index_path.mkdir(parents=True, exist_ok=True)
    temporary = index_path / f"active-{uuid4().hex}.tmp"
    temporary.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(index_path / "active.json")


def prepare_build_extension(request: dict, current: dict, documents: list[dict], active: dict | None) -> tuple[dict, dict]:
    """Append only new approved revisions to an inactive, unchanged build scope."""
    index = request["index"]
    if request.get("action") != "build" or index.get("storage") != "postgresql" or not index.get("workspace"):
        raise ValueError("invalid_extension_build")
    if active is not None:
        if not isinstance(active, dict) or not active.get("workspace"):
            raise ValueError("invalid_active_index")
        if active["workspace"] == index["workspace"]:
            raise ValueError("cannot_extend_active_workspace")
    previous = index["snapshot"]
    if previous.get("schemaVersion") != current.get("schemaVersion") or previous.get("embeddingProfileId") != current.get("embeddingProfileId"):
        raise ValueError("extension_profile_changed")
    for manifest in (previous, current):
        calculated = snapshot_manifest(manifest["revisions"], manifest["embeddingProfileId"])
        if calculated["fingerprint"] != manifest.get("fingerprint"):
            raise ValueError("invalid_extension_fingerprint")
    old_rows = {row["sourceRevisionId"]: row for row in previous["revisions"]}
    new_rows = {row["sourceRevisionId"]: row for row in current["revisions"]}
    if not old_rows.keys() <= new_rows.keys():
        raise ValueError("extension_removed_revisions")
    if any(row != new_rows[revision_id] for revision_id, row in old_rows.items()):
        raise ValueError("extension_changed_existing_revision")
    added = sorted(new_rows.keys() - old_rows.keys())
    if not added:
        raise ValueError("extension_requires_additions")
    old_docs = {doc["sourceRevisionId"]: doc for doc in request["documents"]}
    new_docs = {doc["sourceRevisionId"]: doc for doc in documents}
    if (set(old_docs) != set(old_rows) or set(index["indexedRevisionIds"]) != set(old_rows)
            or len(old_docs) != len(request["documents"]) or set(new_docs) != set(new_rows)
            or len(new_docs) != len(documents)):
        raise ValueError("extension_document_scope_mismatch")
    if any(doc != new_docs[revision_id] for revision_id, doc in old_docs.items()):
        raise ValueError("extension_changed_existing_document")
    expanded = deepcopy(request)
    expanded["index"]["snapshot"] = deepcopy(current)
    expanded["index"]["indexedRevisionIds"] = list(index["indexedRevisionIds"]) + added
    expanded["index"]["sourceForms"] = {revision_id: doc.get("documentForm", "unknown") for revision_id, doc in new_docs.items()}
    expanded["documents"] += [deepcopy(new_docs[revision_id]) for revision_id in added]
    audit = {"workspace": index["workspace"], "oldFingerprint": previous["fingerprint"],
        "newFingerprint": current["fingerprint"], "addedSourceRevisionIds": added,
        "previousRevisionCount": len(old_rows), "expandedRevisionCount": len(new_rows)}
    return expanded, audit


def _request_hash(request: dict) -> str:
    return hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save_build_extension(run_path: Path, base_path: Path, request: dict, audit: dict) -> Path:
    """Atomically persist a separate request+audit envelope; original stays intact."""
    original = run_path / "build-request.json"
    if base_path.resolve().parent != run_path.resolve():
        raise ValueError("extension_request_outside_build")
    record = {"request": request, "audit": {**audit,
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "originalRequestSha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "baseRequestFile": base_path.name, "baseRequestSha256": hashlib.sha256(base_path.read_bytes()).hexdigest(),
        "extendedRequestSha256": _request_hash(request)}}
    target = run_path / f"extension-{uuid4().hex}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    return target


def load_build_request(path: Path) -> dict:
    stored = json.loads(path.read_text(encoding="utf-8"))
    if "audit" not in stored:
        return stored
    request, audit = stored["request"], stored["audit"]
    base_name = audit["baseRequestFile"]
    if Path(base_name).name != base_name:
        raise ValueError("invalid_extension_base_path")
    if (hashlib.sha256((path.parent / "build-request.json").read_bytes()).hexdigest() != audit["originalRequestSha256"]
            or hashlib.sha256((path.parent / base_name).read_bytes()).hexdigest() != audit["baseRequestSha256"]
            or _request_hash(request) != audit["extendedRequestSha256"]):
        raise ValueError("extension_audit_hash_mismatch")
    if request["index"]["snapshot"]["fingerprint"] != audit["newFingerprint"]:
        raise ValueError("extension_audit_snapshot_mismatch")
    return request


class LightRAGSearchAdapter:
    def __init__(self, python_path: str, index_path: str, timeout_seconds: float = 45):
        self.python_path = python_path
        self.index_path = Path(index_path)
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, current_snapshot: dict) -> dict:
        start = time.monotonic()
        empty = {"passageIds": [], "usage": summarize_usage([])}
        try:
            index = json.loads((self.index_path / "active.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {**empty, "status": "unavailable", "reason": "index_missing"}
        reason = validate_index(index, current_snapshot)
        if reason:
            return {**empty, "status": "unavailable", "reason": reason}
        if not self.python_path or not Path(self.python_path).is_file():
            return {**empty, "status": "unavailable", "reason": "runtime_missing"}
        run_id = uuid4().hex
        usage_path = self.index_path / "query-usage" / f"{run_id}.json"
        usage_path.parent.mkdir(parents=True, exist_ok=True)
        backend = Path(__file__).resolve().parents[2]
        env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONIOENCODING": "utf-8"}
        request = {"action": "query", "index": index, "query": query,
                   "usagePath": str(usage_path), "workingDirectory": str(self.index_path / "runtime")}
        try:
            process = await asyncio.create_subprocess_exec(
                self.python_path, "-m", "knowledge.integrations.lightrag_runner",
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE, env=env,
                creationflags=0x08000000 if os.name == "nt" else 0)
        except OSError:
            return {**empty, "status": "unavailable", "reason": "runtime_start_failed"}
        try:
            stdout, _ = await asyncio.wait_for(
                process.communicate(json.dumps(request, ensure_ascii=False).encode()), self.timeout_seconds)
        except (TimeoutError, asyncio.CancelledError) as exc:
            if process.returncode is None:
                process.kill()
            await process.communicate()
            if isinstance(exc, asyncio.CancelledError):
                exc.usage = _read_usage(usage_path, interrupted=True)
                raise
            return {**empty, "status": "unavailable", "reason": "query_timeout",
                    "usage": _read_usage(usage_path, interrupted=True)}
        try:
            response = json.loads(stdout)
            if not isinstance(response, dict):
                raise ValueError("Invalid runtime response")
        except (ValueError, UnicodeDecodeError):
            return {**empty, "status": "unavailable", "reason": "runtime_protocol_error",
                    "usage": _read_usage(usage_path, interrupted=True)}
        if process.returncode or response.get("status") != "ready":
            return {**empty, "status": "unavailable", "reason": response.get("reason", "query_failed"),
                    "usage": response.get("usage", _read_usage(usage_path, interrupted=True))}
        # Re-read after model work: a concurrent rebuild must not mix two mappings.
        try:
            active = json.loads((self.index_path / "active.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            active = {}
        if active.get("workspace") != index.get("workspace"):
            return {**empty, "status": "unavailable", "reason": "index_changed_during_query",
                    "usage": response.get("usage", empty["usage"])}
        chunks = response.get("chunks", [])
        passage_ids = mapped_passages(index, chunks)
        return {"status": "ready", "passageIds": passage_ids,
                "usage": response.get("usage", empty["usage"]),
                "diagnostics": {"workspace": index["workspace"], "snapshotFingerprint": current_snapshot["fingerprint"],
                    "indexedRevisions": len(index["indexedRevisionIds"]), "returnedChunks": len(chunks),
                    "mappedPassages": len(passage_ids), "elapsedMs": round((time.monotonic() - start) * 1000, 2),
                    "generationSkipped": True, "mode": "hybrid"}}


def _read_usage(path: Path, *, interrupted: bool = False) -> dict:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        parts = report["components"]
    except (OSError, ValueError, KeyError):
        report, parts = {}, []
    if interrupted:
        pending = max(0, report.get("startedCalls", 0) - len(parts))
        for _ in range(pending):
            parts.append(unknown_usage("graph_query_interrupted"))
    return summarize_usage(parts)
