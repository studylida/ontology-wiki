import copy
import asyncio
import hashlib
import json
from pathlib import Path
import sys

import pytest

from knowledge.integrations.lightrag import (
    LightRAGSearchAdapter, activate_index, mapped_passages, snapshot_manifest, validate_index,
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
async def test_query_disables_shared_prompt_cache_and_retains_observed_usage_on_cancel(tmp_path, monkeypatch):
    """Exercise the runtime callback without installing LightRAG or calling a provider."""
    import importlib.metadata
    import types
    import dotenv
    from knowledge.integrations import lightrag_runner, providers
    options = {}
    class FakeRAG:
        def __init__(self, **kwargs):
            options.update(kwargs)
        async def initialize_storages(self):
            pass
        async def finalize_storages(self):
            pass
        async def aquery_data(self, query, param):
            await options["llm_model_func"](query)
    class FakeGeneration:
        def __init__(self, model, **kwargs):
            self.model = model
        async def stream(self, messages, **kwargs):
            yield types.SimpleNamespace(text="", usage={"calls": 1, "costUsd": 0.02,
                "inputTokens": 20, "outputTokens": 2, "totalTokens": 22})
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
            "snapshot": {"embeddingProfileId": "embedding-v1"}, "generationModel": "fixture-generation",
            "generationEffort": "medium", "embeddingModel": "fixture-embedding", "embeddingDimensions": 2,
            "embeddingApiDimensions": 2, "embeddingTransform": "direct"}})
    assert options["enable_llm_cache"] is False
    assert options["enable_llm_cache_for_entity_extract"] is False
    assert result["status"] == "failed"
    assert result["usage"]["knownCostUsd"] == 0.02
    assert result["usage"]["unknownCostCalls"] == 0
