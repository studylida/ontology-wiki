import copy
import asyncio
import hashlib
import json
from pathlib import Path
import sys

import pytest

from knowledge.integrations.lightrag import (
    LightRAGSearchAdapter, activate_index, mapped_passages, snapshot_manifest, validate_index,
    prepare_build_extension, save_build_extension, load_build_request,
)


def snapshot():
    return snapshot_manifest([{"sourceRevisionId": "r1", "contentHash": "body1",
        "metadataHash": "metadata1", "metadataVersion": 1, "visibility": "shared_candidate",
        "withdrawn": False, "reviewStatus": "approved", "activeRevisionId": "r1",
        "parserProfile": "text-v1", "chunkProfile": "chunks-v1", "documentForm": "edited_summary",
        "passagesHash": "p1"}], "embedding-v1")


def ready_index():
    return {"status": "ready", "storage": "postgresql", "workspace": "test_graph",
        "snapshot": snapshot(), "indexedRevisionIds": ["r1"],
        "chunkMap": {"c1": [{"passageId": "p1", "sourceRevisionId": "r1",
            "textHash": hashlib.sha256("조건이 있는 원문 구간".encode()).hexdigest()}]}}


def extension_inputs():
    document = {"documentId": "d1", "sourceRevisionId": "r1", "title": "original",
        "documentForm": "edited_summary", "content": "original body", "passages": [
            {"passageId": "p1", "text": "body", "embeddingText": "original body", "locator": "section 1"}]}
    request = {"action": "build", "index": {**ready_index(), "status": "building"}, "documents": [document]}
    second_row = {**snapshot()["revisions"][0], "sourceRevisionId": "r2", "activeRevisionId": "r2"}
    current = snapshot_manifest([snapshot()["revisions"][0], second_row], "embedding-v1")
    second_document = {**copy.deepcopy(document), "documentId": "d2", "sourceRevisionId": "r2", "title": "new source"}
    second_document["passages"][0]["passageId"] = "p2"
    return request, current, [document, second_document]


def test_inactive_build_extension_adds_only_new_sources_and_preserves_audit(tmp_path):
    request, current, documents = extension_inputs()
    original = copy.deepcopy(request)
    expanded, audit = prepare_build_extension(request, current, documents, {"workspace": "other_active"})
    assert request == original
    assert expanded["index"]["workspace"] == request["index"]["workspace"]
    assert expanded["documents"][0] == request["documents"][0]
    assert expanded["index"]["indexedRevisionIds"] == ["r1", "r2"]
    assert audit["addedSourceRevisionIds"] == ["r2"]
    path = tmp_path / "build-request.json"
    path.write_text(json.dumps(request), encoding="utf-8")
    original_bytes = path.read_bytes()
    extended_path = save_build_extension(tmp_path, path, expanded, audit)
    stored = json.loads(extended_path.read_text(encoding="utf-8"))
    assert path.read_bytes() == original_bytes
    assert stored["audit"]["originalRequestSha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert stored["audit"]["oldFingerprint"] == request["index"]["snapshot"]["fingerprint"]
    assert stored["audit"]["newFingerprint"] == current["fingerprint"]
    assert load_build_request(extended_path) == expanded
    stored["request"]["documents"][0]["content"] = "tampered"
    extended_path.write_text(json.dumps(stored), encoding="utf-8")
    with pytest.raises(ValueError, match="audit_hash_mismatch"):
        load_build_request(extended_path)


@pytest.mark.parametrize("field,value", [
    ("contentHash", "changed"), ("metadataHash", "changed"), ("metadataVersion", 2),
    ("parserProfile", "new-parser"), ("chunkProfile", "new-chunker"), ("passagesHash", "changed"),
])
def test_build_extension_rejects_changes_to_existing_rows(field, value):
    request, current, documents = extension_inputs()
    current["revisions"][0][field] = value
    current = snapshot_manifest(current["revisions"], current["embeddingProfileId"])
    with pytest.raises(ValueError, match="changed_existing_revision"):
        prepare_build_extension(request, current, documents, None)


def test_build_extension_rejects_removed_rows_profile_changes_and_active_workspace():
    request, current, documents = extension_inputs()
    removed = snapshot_manifest([current["revisions"][1]], "embedding-v1")
    with pytest.raises(ValueError, match="removed_revisions"):
        prepare_build_extension(request, removed, documents[1:], None)
    changed_profile = snapshot_manifest(current["revisions"], "embedding-v2")
    with pytest.raises(ValueError, match="profile_changed"):
        prepare_build_extension(request, changed_profile, documents, None)
    with pytest.raises(ValueError, match="cannot_extend_active_workspace"):
        prepare_build_extension(request, current, documents, ready_index())
    documents[0] = {**documents[0], "content": "changed without hash update"}
    with pytest.raises(ValueError, match="changed_existing_document"):
        prepare_build_extension(request, current, documents, None)


@pytest.mark.parametrize("field,value", [
    ("metadataHash", "metadata2"), ("metadataVersion", 2), ("contentHash", "body2"),
    ("parserProfile", "parser-v2"), ("chunkProfile", "chunks-v2"), ("passagesHash", "excluded-p1"),
    ("withdrawn", True), ("visibility", "private"), ("activeRevisionId", "r2"),
])
def test_graph_snapshot_detects_same_revision_changes(field, value):
    before = snapshot()
    changed = copy.deepcopy(before["revisions"])
    changed[0][field] = value
    after = snapshot_manifest(changed, before["embeddingProfileId"])
    assert validate_index(ready_index(), after) == "snapshot_changed"


def test_graph_mapping_requires_exact_content_and_keeps_duplicate_source_links():
    index = ready_index()
    second = {**index["chunkMap"]["c1"][0], "passageId": "p2"}
    index["chunkMap"]["c1"].append(second)
    assert mapped_passages(index, [{"chunk_id": "c1", "content": "조건이 있는 원문 구간"}]) == ["p1", "p2"]
    assert mapped_passages(index, [{"chunk_id": "c1", "content": "다르게 합쳐진 설명"}]) == []
    assert mapped_passages(index, [{"chunk_id": "missing", "content": "조건이 있는 원문 구간"}]) == []


def test_failed_or_stale_build_does_not_replace_active_index(tmp_path):
    previous = ready_index()
    activate_index(tmp_path, previous, snapshot())
    failed = {**previous, "status": "failed", "workspace": "partial_graph"}
    with pytest.raises(ValueError, match="index_not_ready"):
        activate_index(tmp_path, failed, snapshot())
    assert json.loads((tmp_path / "active.json").read_text()) == previous
    changed = snapshot_manifest([], "embedding-v1")
    with pytest.raises(ValueError, match="snapshot_changed"):
        activate_index(tmp_path, {**previous, "workspace": "stale_graph"}, changed)
    assert json.loads((tmp_path / "active.json").read_text()) == previous


@pytest.mark.asyncio
async def test_stale_graph_does_not_start_runtime(tmp_path, monkeypatch):
    activate_index(tmp_path, ready_index(), snapshot())
    async def unexpected(*args, **kwargs):
        pytest.fail("A stale graph must not call a model or start a runtime")
    monkeypatch.setattr("asyncio.create_subprocess_exec", unexpected)
    result = await LightRAGSearchAdapter("missing-python", str(tmp_path)).search("질문", snapshot_manifest([], "embedding-v1"))
    assert result["status"] == "unavailable"
    assert result["reason"] == "snapshot_changed"
    assert result["usage"]["calls"] == 0


@pytest.mark.asyncio
async def test_cancellation_stops_runtime_and_preserves_inflight_usage(tmp_path, monkeypatch):
    activate_index(tmp_path, ready_index(), snapshot())
    started = asyncio.Event()
    class Process:
        returncode = None
        killed = False
        async def communicate(self, body=None):
            if body is not None:
                request = json.loads(body)
                Path(request["usagePath"]).write_text(json.dumps({"startedCalls": 2, "components": [
                    {"calls": 1, "costUsd": 0.1, "inputTokens": 4, "outputTokens": 2, "totalTokens": 6}]}))
                started.set()
                await asyncio.Event().wait()
            return b"", b""
        def kill(self):
            self.killed = True
            self.returncode = -9
    process = Process()
    async def create(*args, **kwargs):
        return process
    monkeypatch.setattr("asyncio.create_subprocess_exec", create)
    task = asyncio.create_task(LightRAGSearchAdapter(sys.executable, str(tmp_path)).search("질문", snapshot()))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError) as stopped:
        await task
    assert process.killed
    assert stopped.value.usage["calls"] == 2
    assert stopped.value.usage["knownCostUsd"] == 0.1
    assert stopped.value.usage["unknownCostCalls"] == 1


@pytest.mark.asyncio
async def test_manifest_rechecks_public_active_approval_and_passage_exclusions(sessions, reviewer):
    from knowledge.documents.entities import Document, DocumentRevision, Passage
    from knowledge.integrations.lightrag_manifest import capture_graph_snapshot
    async with sessions() as session, session.begin():
        document = Document(id="graph-doc", owner_id=reviewer.id, title="검증 문헌",
            visibility="shared_candidate", active_revision_id="graph-rev", current_revision_id="graph-rev")
        session.add(document)
        await session.flush()
        revision = DocumentRevision(id="graph-rev", document_id=document.id, content="원문",
            content_hash="body1", raw_path="test-fixture-only", metadata_json={"documentForm": "text_extraction"},
            metadata_hash="m1", metadata_version=1, review_status="approved", index_status="ready")
        session.add(revision)
        await session.flush()
        passage = Passage(id="graph-passage", source_revision_id=revision.id, ordinal=0,
            text="원문", locator="p. 1", embedding_text="검증 문헌 원문", input_hash="input1")
        session.add(passage)
    async with sessions() as session:
        before, documents = await capture_graph_snapshot(session, ["graph-rev"], "embedding-v1", include_documents=True)
        assert documents[0]["passages"][0]["passageId"] == "graph-passage"
        assert documents[0]["documentForm"] == "text_extraction"
    async with sessions() as session, session.begin():
        (await session.get(Passage, "graph-passage")).excluded = True
    async with sessions() as session:
        after, documents = await capture_graph_snapshot(session, ["graph-rev"], "embedding-v1", include_documents=True)
        assert before["fingerprint"] != after["fingerprint"]
        assert documents[0]["passages"] == []
    async with sessions() as session, session.begin():
        (await session.get(Document, "graph-doc")).withdrawn = True
    async with sessions() as session:
        with pytest.raises(ValueError, match="unavailable or non-public"):
            await capture_graph_snapshot(session, ["graph-rev"], "embedding-v1")


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["cancel", "rate_limit", "parallel_failure"])
async def test_query_disables_shared_prompt_cache_and_records_failed_call_usage(tmp_path, monkeypatch, failure):
    """Exercise the runtime callback without installing LightRAG or calling a provider."""
    import importlib.metadata
    import types
    import dotenv
    from knowledge.integrations import lightrag_runner, providers
    from knowledge.core.errors import AppError
    options = {}
    started_calls = 0
    all_started = asyncio.Event()
    class FakeRAG:
        def __init__(self, **kwargs):
            options.update(kwargs)
            self.pending = []
            async def queue():
                pass
            queue.shutdown = self.shutdown
            self.role_llm_funcs = {"extract": queue}
        async def shutdown(self, *, graceful, timeout):
            for task in self.pending:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self.pending, return_exceptions=True)
        async def initialize_storages(self):
            pass
        async def finalize_storages(self):
            pass
        async def aquery_data(self, query, param):
            if failure == "parallel_failure":
                self.pending = [asyncio.create_task(options["llm_model_func"](str(index))) for index in range(8)]
                await all_started.wait()
                await self.pending[0]
                return
            await options["llm_model_func"](query)
    class FakeGeneration:
        def __init__(self, model, **kwargs):
            self.model = model
        async def stream(self, messages, **kwargs):
            nonlocal started_calls
            if failure == "rate_limit":
                raise AppError(502, "provider_rate_limit", "fixture", details={"upstreamStatus": 429}, retryable=True)
            if failure == "parallel_failure":
                started_calls += 1
                if started_calls == 8:
                    all_started.set()
                await all_started.wait()
                if messages[-1]["content"] != "0":
                    await asyncio.Event().wait()
            yield types.SimpleNamespace(text="", usage={"calls": 1, "costUsd": 0.02,
                "inputTokens": 20, "outputTokens": 2, "totalTokens": 22})
            if failure == "parallel_failure":
                raise AppError(502, "provider_error", "fixture", details={"upstreamStatus": 500}, retryable=True)
            raise asyncio.CancelledError()
    class FakeEmbedding:
        profile_id = "embedding-v1"
        def __init__(self, model, *args):
            self.model = model
    monkeypatch.setitem(sys.modules, "numpy", types.SimpleNamespace(asarray=lambda value: value))
    monkeypatch.setitem(sys.modules, "lightrag", types.SimpleNamespace(LightRAG=FakeRAG, QueryParam=lambda **kwargs: kwargs))
    monkeypatch.setitem(sys.modules, "lightrag.utils", types.SimpleNamespace(
        EmbeddingFunc=lambda **kwargs: kwargs, sanitize_text_for_encoding=lambda value: value))
    monkeypatch.setitem(sys.modules, "lightrag.utils_pipeline", types.SimpleNamespace(make_custom_chunk_id=lambda *args: "unused"))
    monkeypatch.setattr(importlib.metadata, "version", lambda _: "1.5.7")
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(lightrag_runner.logging, "disable", lambda _: None)
    monkeypatch.setattr(lightrag_runner, "configure_database", lambda *args: None)
    monkeypatch.setattr(providers, "OpenAIGenerationClient", FakeGeneration)
    monkeypatch.setattr(providers, "OpenAIEmbeddingClient", FakeEmbedding)
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-never-sent")
    result = await lightrag_runner.execute({"action": "query", "query": "private question",
        "usagePath": str(tmp_path / "usage.json"), "workingDirectory": str(tmp_path / "runtime"),
        "index": {"databaseName": "ontology_lightrag_dev", "workspace": "test",
            "generationMaxAsync": 8,
            "snapshot": {"embeddingProfileId": "embedding-v1"}, "generationModel": "test-generation",
            "generationEffort": "medium", "embeddingModel": "test-embedding", "embeddingDimensions": 2,
            "embeddingApiDimensions": 2, "embeddingTransform": "direct"}})
    assert options["enable_llm_cache"] is False
    assert options["enable_llm_cache_for_entity_extract"] is False
    assert options["llm_model_max_async"] == 8
    assert options["max_parallel_insert"] == 1
    assert result["status"] == "failed"
    assert result["usage"]["knownCostUsd"] == (0 if failure == "rate_limit" else 0.02)
    assert result["usage"]["unknownCostCalls"] == {"cancel": 0, "rate_limit": 1, "parallel_failure": 7}[failure]
    ledger = json.loads((tmp_path / "usage.json").read_text())
    assert ledger["generationMaxAsync"] == 8
    assert ledger["callErrors"] == ({"provider_error": 1, "CancelledError": 7} if failure == "parallel_failure"
        else {"CancelledError" if failure == "cancel" else "provider_rate_limit": 1})
    assert result["usage"]["calls"] == ledger["calls"] == (8 if failure == "parallel_failure" else 1)
    if failure == "rate_limit":
        assert ledger["components"][0]["upstreamStatus"] == 429
