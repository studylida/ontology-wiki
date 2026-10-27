"""Explicit developer evaluation against a frozen approved corpus; never reads login tokens.

Run with the application virtualenv. Private environment values stay in this process.
The existing user's active role and the application's access checks are used; results
are dedicated regression artifacts, not user conversations or independent holdout scores.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from time import perf_counter


ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = [
    {"id": "tsv_wire", "mode": "analysis", "query": "TSV와 와이어 본딩을 연결 경로, 전력, 지연, 적용 한계별로 표로 비교해 주세요. 동일한 조건에서 전력 차이를 수치로 비교할 수 있는지 확인하고, 비교 조건과 출처가 부족하면 그 점을 명확히 표시해 주세요."},
    {"id": "thermocompression", "mode": "wiki", "query": "열압착 본딩의 원리와 적용 조건을 설명해 줘."},
]


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def usage_components(usage: dict | None) -> list[dict]:
    return usage.get("components", [usage]) if usage else []


def validate_manifest(current: list[dict], frozen: list[dict]) -> list[dict]:
    current_by_id = {item["revisionId"]: item for item in current}
    ids = [item["revisionId"] for item in frozen]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Frozen manifest must contain distinct source revisions.")
    changed = [item["revisionId"] for item in frozen if current_by_id.get(item["revisionId"]) != item]
    if changed:
        raise ValueError("Frozen source revisions are no longer active or changed: " + ", ".join(changed))
    return frozen


def prepare_code(ref: str | None, output: Path) -> tuple[Path, str]:
    revision = subprocess.check_output(["git", "rev-parse", ref or "HEAD"], cwd=ROOT, text=True).strip()
    if ref is None:
        return ROOT / "backend", revision
    target = output / "baseline-code"
    if target.exists():
        raise SystemExit("Baseline snapshot already exists; choose a fresh output directory.")
    archive = subprocess.check_output(["git", "archive", revision, "backend"], cwd=ROOT)
    target.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(target, filter="data")
    return target / "backend", revision


async def evaluate(args, code_revision):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from knowledge.registry import load_entities
    from knowledge.core.config import Settings
    from knowledge.core.errors import AppError
    from knowledge.core.usage import summarize_usage, unknown_usage
    from knowledge.documents.entities import Document, DocumentRevision
    from knowledge.documents.repository import DocumentRepository
    from knowledge.identity.repository import UserRepository
    from knowledge.identity.service import principal_from_user
    from knowledge.integrations.providers import get_embedding_client, get_generation_client
    from knowledge.rag.service import RetrievalService
    from knowledge.rag.dto import AnswerRequest
    from knowledge.answers.prompt import build_messages
    import knowledge
    try:
        from knowledge.answers.citations import CitationTextDecoder, citation_aliases, decode_citation_deltas
    except ModuleNotFoundError as exc:
        if not args.baseline_ref or exc.name != "knowledge.answers.citations":
            raise
        CitationTextDecoder = None  # Archived baseline code used original IDs directly.

    load_entities()
    settings = Settings()
    if settings.provider_mode != "live":
        raise SystemExit("Real evaluation requires OW_PROVIDER_MODE=live; no fixture fallback.")
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    retrieval = None

    async def current_manifest(principal):
        async with sessions() as session:
            allowed = await DocumentRepository(session).resolve_snapshot(principal, None, [])
            rows = (await session.execute(select(DocumentRevision, Document).join(Document).where(DocumentRevision.id.in_(allowed)))).all()
            return sorted([{"revisionId": r.id, "documentId": d.id, "title": d.title,
                            "contentHash": r.content_hash, "metadataHash": r.metadata_hash,
                            "metadataVersion": r.metadata_version} for r, d in rows], key=lambda item: item["revisionId"])

    try:
        async with sessions() as session:
            user = await UserRepository(session).by_username(args.owner)
            if user is None or not user.is_active or user.kind != "user":
                raise SystemExit("The named active user account is required.")
            principal = principal_from_user(user)
            principal.require("rag:answer")
        manifest = await current_manifest(principal)
        if not manifest:
            raise SystemExit("No approved indexed sources available.")
        if args.manifest:
            frozen = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            manifest = validate_manifest(manifest, frozen)
        dump(args.output / "corpus-manifest.json", manifest)
        digest = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        embedding, generation = get_embedding_client(settings), get_generation_client(settings)
        retrieval = RetrievalService(sessions, embedding, settings)
        code_root = Path(knowledge.__file__).resolve().parent
        code_files = {path.relative_to(code_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in sorted(code_root.rglob("*.py"))}
        questions = [question for question in QUESTIONS if not args.question or question["id"] in args.question]
        run = {"label": args.label, "codeRevision": code_revision, "baselineFromGit": bool(args.baseline_ref),
               "questionIds": [question["id"] for question in questions],
               "harnessHash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "citationDecoding": "short_keys_to_original_ids" if CitationTextDecoder else "legacy_source_ids",
               "runtimeConfig": args.runtime_config_record,
               "codeFiles": code_files,
               "codeHash": hashlib.sha256(json.dumps(code_files, sort_keys=True).encode()).hexdigest(),
               "provenance": "explicit_developer_evaluation_as_existing_active_user", "owner": args.owner,
               "evaluationSplit": "user_regression_not_holdout", "corpusHash": digest,
               "sourceCount": len(manifest), "generationModel": settings.generation_model,
               "effort": settings.generation_effort, "embeddingProfile": embedding.profile_id,
               "pipelineConfig": {name: getattr(settings, name, None) for name in (
                   "reranker_mode", "reranker_model_revision", "reranker_device", "reranker_max_length",
                   "reranker_batch_size", "retrieval_candidate_limit", "retrieval_graph_mode",
                   "retrieval_limit", "extended_max_queries", "extended_seconds",
                   "context_max_characters", "prompt_max_characters")},
               "extended": True, "results": []}
        dump(args.output / "results.json", run)
        for question in questions:
            request = AnswerRequest(message=question["query"], response_mode=question["mode"], extended=True,
                                    source_revision_ids=[item["revisionId"] for item in manifest],
                                    client_request_id=f"eval-{args.label}-{question['id']}")
            result = {"id": question["id"], "query": question["query"], "responseMode": question["mode"],
                      "response": "", "status": "running"}
            run["results"].append(result)
            started = perf_counter()
            generation_usage, generation_started = None, False
            decoder = None
            try:
                validate_manifest(await current_manifest(principal), manifest)
                found = await retrieval.search(principal, request, for_answer=True)
                result["retrieval"] = found
                if set(found["appliedFilters"]["sourceRevisionIds"]) != {item["revisionId"] for item in manifest}:
                    raise ValueError("Retrieved source snapshot differs from the frozen manifest.")
                validate_manifest(await current_manifest(principal), manifest)
                messages = build_messages(request, found, [], max_characters=settings.prompt_max_characters)
                result["messages"] = messages
                result["promptHash"] = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                generation_start, first_delta = perf_counter(), None
                generation_started = True
                stream = generation.stream(messages, effort=settings.generation_effort)
                decoder = None
                if CitationTextDecoder:
                    result["citationAliases"] = citation_aliases(found)
                    decoder = CitationTextDecoder(result["citationAliases"])
                    stream = decode_citation_deltas(stream, found, decoder=decoder)
                async for delta in stream:
                    if delta.text:
                        if first_delta is None:
                            first_delta = perf_counter()
                        result["response"] += delta.text
                    if delta.usage is not None:
                        generation_usage = delta.usage
                result["generationUsage"] = generation_usage
                if decoder and decoder.unknown_references:
                    result["unknownCitationReferences"] = sorted(decoder.unknown_references)
                    error = AppError(502, "SOURCE_REFERENCE_INVALID", "Generated source reference is outside the supplied evidence set.")
                    error.usage = generation_usage
                    raise error
                parts = list(found["usage"]["components"])
                parts.append({**(generation_usage or unknown_usage("answer_generation", settings.generation_model)), "operation": "answer_generation"})
                result["usage"] = summarize_usage(parts)
                result["timings"] = {"retrievalMs": found["timings"]["totalMs"],
                                     "generationMs": round((perf_counter() - generation_start) * 1000, 2),
                                     "firstTextMs": round((first_delta - started) * 1000, 2) if first_delta else None,
                                     "totalMs": round((perf_counter() - started) * 1000, 2)}
                result["citedIds"] = sorted({item.strip() for group in re.findall(r"\[출처:\s*([^\]]+)\]", result["response"])
                                             for item in re.split(r"[,;]", group) if item.strip()})
                result["status"] = "completed"
            except Exception as exc:
                if decoder is not None:
                    result["response"] += decoder.finish()
                result["status"] = "failed"
                result["errorCode"] = getattr(exc, "code", type(exc).__name__)
                result["failureUsage"] = getattr(exc, "usage", None)
                parts = list(result.get("retrieval", {}).get("usage", {}).get("components", []))
                if generation_started:
                    parts.extend(usage_components(getattr(exc, "usage", None) or generation_usage or unknown_usage("answer_generation", settings.generation_model)))
                elif getattr(exc, "usage", None):
                    parts.extend(usage_components(exc.usage))
                result["usage"] = summarize_usage(parts)
                result["timings"] = {"totalMs": round((perf_counter() - started) * 1000, 2)}
            dump(args.output / "results.json", run)
            (args.output / f"{question['id']}.md").write_text(result["response"], encoding="utf-8")
            print(json.dumps({"id": question["id"], "status": result["status"], "timings": result["timings"],
                              "retrievalRunId": result.get("retrieval", {}).get("retrievalRunId")}, ensure_ascii=False), flush=True)
    finally:
        if retrieval is not None and hasattr(retrieval, "aclose"):
            await retrieval.aclose()
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--owner", default="my-reviewer")
    parser.add_argument("--baseline-ref")
    parser.add_argument("--manifest")
    parser.add_argument("--question", action="append", choices=[question["id"] for question in QUESTIONS],
                        help="Run only this regression question for a bounded diagnostic; omitted runs both.")
    parser.add_argument("--graph-mode", choices=["disabled", "lightrag"],
                        help="Explicit graph ablation override applied after the runtime configuration.")
    parser.add_argument("--runtime-config", type=Path, help="Optional non-secret RAG runtime settings; generation/identity settings are excluded.")
    args = parser.parse_args()
    args.output = args.output.resolve()
    if (args.output / "results.json").exists():
        raise SystemExit("Output already contains results; choose a fresh directory.")
    code, revision = prepare_code(args.baseline_ref, args.output)
    from dotenv import dotenv_values
    for key, value in dotenv_values(ROOT / ".env").items():
        if value is not None:
            os.environ.setdefault(key, value)
    args.runtime_config_record = None
    if args.runtime_config:
        config_file = args.runtime_config.resolve(strict=True)
        config = {key: value for key, value in dotenv_values(config_file, encoding="utf-8-sig").items()
                  if value is not None and key.startswith(("OW_RERANKER_", "OW_RETRIEVAL_", "OW_LIGHTRAG_"))}
        os.environ.update(config)
        args.runtime_config_record = {"path": str(config_file), "sha256": hashlib.sha256(config_file.read_bytes()).hexdigest(),
                                      "loadedKeys": sorted(config)}
    if args.graph_mode:
        os.environ["OW_RETRIEVAL_GRAPH_MODE"] = args.graph_mode
    sys.path.insert(0, str(code))
    asyncio.run(evaluate(args, revision))


if __name__ == "__main__":
    main()
