import asyncio
from copy import deepcopy
import sys

import pytest

from knowledge.core.errors import AppError
from knowledge.documents.repository import select_ranked_hits
from knowledge.integrations import rerank
from knowledge.rag.service import select_anchors


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


def test_anchors_offer_nearby_documents_space_without_promoting_distant_candidates():
    hits = [hit('a1'), hit('a2'), hit('b1', 'b'), hit('b2', 'b'),
            hit('c1', 'c'), hit('a3'), hit('b3', 'b'), hit('c2', 'c'), hit('d1', 'd')]
    assert [h['passageId'] for h in select_anchors(hits, 4)] == ['a1', 'a2', 'b1', 'c1']
    assert [h['passageId'] for h in select_anchors([hits[0], hits[0], hits[2]], 4)] == ['a1', 'b1']


def test_anchors_preserve_strong_evidence_and_explicit_reranking():
    hits = [hit('a1'), hit('a2'), hit('b1', 'b'), hit('c1', 'c')]
    hits[0]['score'], hits[1]['score'], hits[2]['score'], hits[3]['score'] = .03, .029, .028, .01
    assert [h['passageId'] for h in select_anchors(hits, 3)] == ['a1', 'a2', 'b1']
    hits[3]['score'] = .0288
    assert [h['passageId'] for h in select_anchors(hits, 3)] == ['a1', 'b1', 'c1']
    for item, score in zip(hits, (10, 9, 8, -10)):
        item['rerankScore'] = score
    assert [h['passageId'] for h in select_anchors(hits, 3)] == ['a1', 'a2', 'b1']




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
