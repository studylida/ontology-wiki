"""Isolated pinned LightRAG runtime. JSON stdin/stdout; credentials stay in process."""
from __future__ import annotations

import asyncio
from collections import Counter
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import unquote, urlsplit


class GraphRuntimeError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def configure_database(database_name: str, workspace: str) -> None:
    if not re.fullmatch(r"ontology_lightrag_[a-z0-9_]+_dev|ontology_lightrag_dev", database_name):
        raise ValueError("Dedicated graph development database required")
    url = urlsplit(os.environ.get("OW_DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://", 1))
    if url.scheme != "postgresql" or not url.hostname or not url.username:
        raise ValueError("PostgreSQL configuration missing")
    if url.path.lstrip("/") == database_name:
        raise ValueError("Graph database must be separate from application database")
    values = {"POSTGRES_HOST": url.hostname, "POSTGRES_PORT": str(url.port or 5432),
        "POSTGRES_USER": unquote(url.username), "POSTGRES_PASSWORD": unquote(url.password or ""),
        "POSTGRES_DATABASE": database_name, "POSTGRES_WORKSPACE": workspace,
        "POSTGRES_MAX_CONNECTIONS": "4", "POSTGRES_VECTOR_INDEX_TYPE": "HNSW"}
    os.environ.update(values)


async def shutdown_model_queues(rag, *, graceful: bool) -> bool:
    """Pinned SDK storage finalization does not stop its provider worker queues."""
    functions = list(getattr(rag, "role_llm_funcs", {}).values())
    functions.append(getattr(getattr(rag, "embedding_func", None), "func", None))
    shutdowns = [function.shutdown(graceful=graceful, timeout=10)
                 for function in dict.fromkeys(functions) if callable(getattr(function, "shutdown", None))]
    outcomes = await asyncio.gather(*shutdowns, return_exceptions=True)
    return not any(isinstance(outcome, BaseException) for outcome in outcomes)


async def execute(request: dict) -> dict:
    # Suppress upstream connection/prompt logs; only sanitized results leave this process.
    logging.disable(logging.CRITICAL)
    from dotenv import load_dotenv
    root = Path(__file__).resolve().parents[3]
    load_dotenv(root / ".env", override=False)
    from importlib.metadata import version
    if version("lightrag-hku") != "1.5.7":
        raise ValueError("Unsupported LightRAG runtime version")
    import numpy as np
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc, sanitize_text_for_encoding
    from lightrag.utils_pipeline import make_custom_chunk_id
    from .providers import OpenAIEmbeddingClient, OpenAIGenerationClient
    from .lightrag import _read_usage
    from ..core.usage import summarize_usage, unknown_usage

    action = request["action"]
    index = request["index"]
    configure_database(index["databaseName"], index["workspace"])
    usage_path = Path(request["usagePath"])
    # A resumed workspace may reuse completed extraction calls; retain their cost.
    parts = _read_usage(usage_path, interrupted=True)["components"] if action == "build" else []
    started_calls = sum(part.get("calls", 1) for part in parts)
    max_calls = int(request.get("maxModelCalls", 1000 if action == "build" else 12))
    generation_concurrency = int(index.get("generationMaxAsync", 2))
    if not 1 <= generation_concurrency <= 8:
        raise ValueError("Graph generation concurrency must be between 1 and 8")
    generation = OpenAIGenerationClient(index["generationModel"], max_output_tokens=12000)
    embedding = OpenAIEmbeddingClient(index["embeddingModel"], index["embeddingDimensions"],
        index["embeddingApiDimensions"], index["embeddingTransform"])
    if embedding.profile_id != index["snapshot"]["embeddingProfileId"]:
        raise ValueError("Embedding profile mismatch")
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Model provider configuration missing")

    def save_usage():
        write_json(usage_path, {**summarize_usage(parts), "startedCalls": started_calls,
            "generationMaxAsync": generation_concurrency,
            "callErrors": dict(Counter(part["errorCode"] for part in parts if part.get("errorCode")))})

    def failed_usage(exc, observed, operation, model):
        details = getattr(exc, "details", None) or {}
        return {**(getattr(exc, "usage", None) or observed or unknown_usage(operation, model)),
            "operation": operation, "errorCode": getattr(exc, "code", type(exc).__name__),
            "upstreamStatus": details.get("upstreamStatus")}

    def reserve_call():
        nonlocal started_calls
        if started_calls >= max_calls:
            raise GraphRuntimeError("graph_model_call_budget")
        started_calls += 1
        save_usage()

    async def llm(prompt, system_prompt=None, history_messages=None, **kwargs):
        reserve_call()
        messages = ([{"role": "system", "content": system_prompt}] if system_prompt else [])
        messages += list(history_messages or []) + [{"role": "user", "content": prompt}]
        output, usage = "", None
        operation = "graph_index_generation" if action == "build" else "graph_query_generation"
        try:
            async for delta in generation.stream(messages, effort=index["generationEffort"]):
                output += delta.text
                if delta.usage:
                    usage = delta.usage
        except BaseException as exc:
            parts.append(failed_usage(exc, usage, operation, generation.model))
            save_usage()
            raise
        parts.append({**(usage or unknown_usage(operation, generation.model)), "operation": operation})
        save_usage()
        if not output.strip():
            raise GraphRuntimeError("graph_empty_model_response")
        return output

    async def embed(texts, **kwargs):
        reserve_call()
        operation = "graph_index_embedding" if action == "build" else "graph_query_embedding"
        try:
            result = await embedding.embed(texts)
        except BaseException as exc:
            parts.append(failed_usage(exc, None, operation, embedding.model))
            save_usage()
            raise
        parts.append({**result.usage, "operation": operation, "inputCount": len(texts)})
        save_usage()
        return np.asarray(result.vectors)

    workdir = Path(request["workingDirectory"])
    workdir.mkdir(parents=True, exist_ok=True)
    rag = LightRAG(working_dir=str(workdir), workspace=index["workspace"],
        kv_storage="PGKVStorage", vector_storage="PGVectorStorage",
        graph_storage="PGTableGraphStorage", doc_status_storage="PGDocStatusStorage",
        llm_model_func=llm, llm_model_name=index["generationModel"],
        embedding_func=EmbeddingFunc(embedding_dim=index["embeddingDimensions"], func=embed,
            model_name=index["embeddingModel"], max_token_size=8000),
        entity_extract_max_gleaning=0, llm_model_max_async=generation_concurrency,
        max_parallel_insert=1, embedding_func_max_async=2,
        embedding_batch_num=32, enable_llm_cache=action == "build",
        enable_llm_cache_for_entity_extract=action == "build",
        addon_params={"language": "Korean"})
    started = time.monotonic()
    result = None
    try:
        await rag.initialize_storages()
        if action == "build":
            chunk_map, completed = {}, []
            for document in request["documents"]:
                revision_id = document["sourceRevisionId"]
                texts = []
                for passage in document["passages"]:
                    content = sanitize_text_for_encoding(passage["embeddingText"])
                    chunk_id = make_custom_chunk_id(revision_id, content)
                    chunk_map.setdefault(chunk_id, []).append({"passageId": passage["passageId"],
                        "sourceRevisionId": revision_id, "textHash": hashlib.sha256(content.encode()).hexdigest()})
                    texts.append(content)
                if not texts:
                    raise ValueError("Document has no searchable passages")
                await rag.ainsert_custom_chunks(document["content"], texts, doc_id=revision_id)
                status = await rag.doc_status.get_by_id(revision_id)
                if not status or status.get("status") != "processed":
                    raise GraphRuntimeError("graph_document_not_processed")
                # Verify exact stored content before exposing the ID mapping.
                expected_ids = [make_custom_chunk_id(revision_id, text) for text in dict.fromkeys(texts)]
                stored = await rag.text_chunks.get_by_ids(expected_ids)
                if len(stored) != len(expected_ids):
                    raise GraphRuntimeError("graph_chunk_count_mismatch")
                for chunk_id, chunk in zip(expected_ids, stored):
                    if not chunk or hashlib.sha256(chunk["content"].encode()).hexdigest() != chunk_map[chunk_id][0]["textHash"]:
                        raise GraphRuntimeError("graph_chunk_mapping_mismatch")
                completed.append(revision_id)
                write_json(Path(request["progressPath"]), {"status": "building", "completedRevisionIds": completed,
                    "totalRevisions": len(request["documents"]), "elapsedSeconds": round(time.monotonic() - started, 3),
                    "usage": summarize_usage(parts)})
            result = {**index, "status": "ready", "chunkMap": chunk_map,
                "indexedRevisionIds": completed, "elapsedSeconds": round(time.monotonic() - started, 3),
                "usage": summarize_usage(parts)}
        elif action == "query":
            data = await rag.aquery_data(request["query"], param=QueryParam(mode="hybrid", top_k=20,
                chunk_top_k=24, max_entity_tokens=4000, max_relation_tokens=4000, max_total_tokens=14000,
                enable_rerank=False, include_references=True, only_need_context=True))
            if data.get("status") != "success":
                raise GraphRuntimeError("graph_query_no_result")
            result = {"status": "ready", "chunks": data.get("data", {}).get("chunks", []),
                "elapsedSeconds": round(time.monotonic() - started, 3), "usage": summarize_usage(parts)}
        else:
            raise ValueError("Unknown graph operation")
    except BaseException as exc:
        result = {"status": "failed", "reason": getattr(exc, "code", type(exc).__name__),
            "elapsedSeconds": round(time.monotonic() - started, 3), "usage": summarize_usage(parts)}
    finally:
        queues_closed = await shutdown_model_queues(rag, graceful=result is not None and result["status"] == "ready")
        if not queues_closed:
            result = {"status": "failed", "reason": "model_queue_shutdown_failed"}
        try:
            await rag.finalize_storages()
        except Exception:
            # Do not activate an index whose durable storage cleanup was incomplete.
            result = {"status": "failed", "reason": "storage_finalize_failed",
                "elapsedSeconds": round(time.monotonic() - started, 3), "usage": summarize_usage(parts)}
        # Provider workers may record charges during queue shutdown, after the
        # first extraction/merge error has already built the provisional result.
        save_usage()
        result["usage"] = summarize_usage(parts)
        result["elapsedSeconds"] = round(time.monotonic() - started, 3)
    return result


if __name__ == "__main__":
    request = None
    try:
        request = json.load(sys.stdin)
        result = asyncio.run(execute(request))
    except Exception as exc:
        result = {"status": "failed", "reason": type(exc).__name__}
    if isinstance(request, dict) and request.get("usagePath"):
        from .lightrag import _read_usage
        result["usage"] = _read_usage(Path(request["usagePath"]), interrupted=True)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result.get("status") == "ready" else 1)
