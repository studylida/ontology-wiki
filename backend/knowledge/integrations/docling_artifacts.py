"""Content-addressed originals and derived conversion artifacts; no DB mutation."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from knowledge.documents.parsing import save_raw


def model_fingerprint(artifacts_path: str) -> str:
    root = Path(artifacts_path).resolve(strict=True)
    digest = hashlib.sha256()
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and ".cache" not in p.relative_to(root).parts and p.suffix != ".lock")
    if not files:
        raise ValueError("Docling models are not prefetched")
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
    return digest.hexdigest()


def conversion_key(body: bytes, *, max_pages: int, max_characters: int, ocr: bool,
                   model_artifacts_hash: str) -> str:
    profile = {"engine": "docling", "version": "2.143.0", "coreVersion": "2.104.0",
               "layoutModelsVersion": "4.0.4", "pdfBackend": "pypdfium2", "pdfBackendVersion": "5.14.0",
               "modelArtifactsHash": model_artifacts_hash,
               "serialization": "hybrid-markdown-v3", "chunker": "HybridChunker", "maxTokens": 768,
               "tokenizer": "cl100k_base", "tokenizerVersion": "0.12.0", "repeatTableHeader": True,
               "mergePeers": True, "maxPages": max_pages,
               "maxCharacters": max_characters, "ocr": ocr,
               "sourceSha256": hashlib.sha256(body).hexdigest()}
    return hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def preserve_conversion(storage_path: str, key: str, body: bytes, result: dict):
    root = Path(storage_path).resolve()
    metadata = result["metadata"]
    metadata["rawPath"] = save_raw(storage_path, body)
    metadata["structuredDocumentPath"] = save_raw(storage_path, _json_bytes(result["structuredDocument"]))
    metadata["sourceMapPath"] = save_raw(storage_path, _json_bytes(result["sourceMap"]))
    metadata["preparedPassagesArtifact"] = save_raw(storage_path, _json_bytes(result["preparedPassages"]))
    metadata["extractedTextPath"] = save_raw(storage_path, result["content"].encode("utf-8"))
    metadata["conversionKey"] = key
    result_path = save_raw(storage_path, _json_bytes(result))
    target = root / "derived" / "docling" / (key + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(_json_bytes({"resultPath": result_path}))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def load_conversion(storage_path: str, key: str, body: bytes) -> dict | None:
    root = Path(storage_path).resolve()
    target = root / "derived" / "docling" / (key + ".json")
    if not target.exists():
        return None
    # A corrupt cache is rejected, rather than silently replacing its original.
    manifest = json.loads(target.read_text(encoding="utf-8"))
    stored = (root / manifest["resultPath"]).resolve()
    if not stored.is_relative_to(root):
        raise ValueError("Conversion cache path escapes storage")
    payload = stored.read_bytes()
    if hashlib.sha256(payload).hexdigest() != stored.stem:
        raise ValueError("Conversion cache hash mismatch")
    result = json.loads(payload)
    if result["metadata"]["conversionKey"] != key:
        raise ValueError("Conversion profile mismatch")
    if result["metadata"]["sourceSha256"] != hashlib.sha256(body).hexdigest():
        raise ValueError("Conversion source hash mismatch")
    for field in ("rawPath", "structuredDocumentPath", "sourceMapPath", "extractedTextPath", "preparedPassagesArtifact"):
        artifact = (root / result["metadata"][field]).resolve()
        if not artifact.is_relative_to(root) or hashlib.sha256(artifact.read_bytes()).hexdigest() != artifact.stem:
            raise ValueError("Conversion artifact hash mismatch")
    return result
