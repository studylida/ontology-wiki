import asyncio
from copy import deepcopy
import sys

import pytest

from knowledge.core.errors import AppError
from knowledge.documents.repository import DocumentRepository, select_ranked_hits
from knowledge.integrations import rerank
from test_rag_contract import indexed_source


def hit(pid, document="a", publisher="large", text="본문"):
    return {"passageId": pid, "sourceRevisionId": "rev-" + document, "documentId": document,
            "publisherId": publisher, "text": text, "score": 0.01, "methods": ["vector"]}


def test_selection_preserves_rerank_order_group_opportunity_and_document_diversity():
    hits = [hit(str(i)) for i in range(6)] + [hit("b", "b", "small"), hit("c", "c")]
    hits.insert(1, hits[0])
    original = deepcopy(hits)
    chosen = select_ranked_hits(hits, [{"groupId": "small", "publisherId": "small"}], 5)
    assert [h["passageId"] for h in chosen["hits"]] == ["b", "0", "1", "2", "c"]
    assert chosen["groupCoverage"] == [{"groupId": "small", "hitCount": 1, "status": "available"}]
    assert hits == original


@pytest.mark.asyncio
async def test_candidate_pool_keeps_passages_that_final_diversity_would_drop(
    sessions, settings, principal, reviewer, embedding_client,
):
    first = await indexed_source(sessions, settings, principal, reviewer, embedding_client,
        text="\n\n".join(f"## 측정 {i}\n접합 온도 실험 결과 {i}." for i in range(8)))
    second = await indexed_source(sessions, settings, principal, reviewer, embedding_client,
        publisher="small", text="접합 온도와 압력 조건.")
    vector = (await embedding_client.embed(["접합 온도"])).vectors[0]
    groups = [{"groupId": "small", "publisherId": "small"}]
    async with sessions() as session:
        repo = DocumentRepository(session)
        candidates = await repo.search_candidates(principal, vector, embedding_client.profile_id,
                                                 "접합 온도", candidate_limit=20)
        final = await repo.search(principal, vector, embedding_client.profile_id, "접합 온도", limit=8)
        narrow = await repo.search_candidates(principal, vector, embedding_client.profile_id,
                                             "접합 온도", source_groups=groups, candidate_limit=20)
    assert sum(h["sourceRevisionId"] == first["currentRevisionId"] for h in candidates["hits"]) >= 6
    assert sum(h["sourceRevisionId"] == first["currentRevisionId"] for h in final["hits"]) == 3
    assert {h["sourceRevisionId"] for h in narrow["hits"]} == {second["currentRevisionId"]}


@pytest.fixture
def fake_reranker(tmp_path, monkeypatch):
    worker = tmp_path / "rerank_worker.py"
    worker.write_text('''import json, sys, time
print(json.dumps({"ready": True, "device": "cpu", "modelLoadMs": 1}), flush=True)
for line in sys.stdin:
    data = json.loads(line)
    if data["query"] == "wait": time.sleep(10)
    scores = [float(i) for i in range(len(data["texts"]))]
    if data["query"] == "invalid": scores = [float("nan")]
    print(json.dumps({"id": data["id"], "scores": scores, "inferenceMs": 2,
      "truncatedPairs": 1, "totalPairs": len(data["texts"]),
      "inputTokens": 2000, "processedTokens": 1024}), flush=True)
''', encoding="utf-8")
    monkeypatch.setattr(rerank, "__file__", str(tmp_path / "rerank.py"))
    return rerank.LocalCrossEncoderReranker(sys.executable, str(tmp_path), "test-revision", timeout_seconds=2)


@pytest.mark.asyncio
async def test_adapter_preserves_evidence_and_reuses_process(fake_reranker):
    hits = [hit("first", text="원문 A"), hit("second", text="원문 B")]
    original = deepcopy(hits)
    try:
        result = await fake_reranker.rerank("query", hits)
        process = fake_reranker._process
        assert [h["passageId"] for h in result["hits"]] == ["second", "first"]
        assert [h["text"] for h in result["hits"]] == ["원문 B", "원문 A"]
        assert result["truncatedPairs"] == 1
        assert result["usage"]["providerCostUsd"] == 0
        assert result["usage"]["localHardwareCostUsd"] is None
        assert result["coldStart"] is True
        assert hits == original
        again = await fake_reranker.rerank("query", hits)
        assert fake_reranker._process is process and again["coldStart"] is False
    finally:
        await fake_reranker.aclose()
    assert process.returncode is not None


@pytest.mark.asyncio
async def test_timeout_cancellation_and_bad_scores_terminate_worker(fake_reranker):
    for query, code in [("wait", "RERANKER_TIMEOUT"), ("invalid", "RERANKER_CONTRACT_ERROR")]:
        with pytest.raises(AppError) as exc:
            await fake_reranker.rerank(query, [hit("a")])
        assert exc.value.code == code
        assert fake_reranker._process is None
    task = asyncio.create_task(fake_reranker.rerank("wait", [hit("a")]))
    while fake_reranker._process is None:
        await asyncio.sleep(.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert fake_reranker._process is None


def test_inference_child_environment_excludes_credentials(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("OW_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("HF_TOKEN", "test-secret")
    env = rerank._worker_environment()
    assert not {"OPENAI_API_KEY", "OW_AUTH_SECRET", "HF_TOKEN"}.intersection(env)
    assert env["HF_HUB_OFFLINE"] == "1"
