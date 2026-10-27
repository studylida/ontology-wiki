import json

import pytest

from knowledge.answers.evidence_plan import evidence_review_messages, parse_evidence_review
from knowledge.answers.prompt import build_messages
from knowledge.integrations.providers import ProviderDelta
from knowledge.rag.dto import AnswerRequest
from test_answers import replace_provider, wait_finished
from test_rag_contract import indexed_source


def test_comparison_review_keeps_only_known_aspects_and_source_ids():
    request = AnswerRequest(clientRequestId="review", message="A와 B의 전력과 지연을 비교해 주세요.")
    retrieval = {"grounding": {"passages": [{"id": "p1", "passageId": "p1", "text": "전력 결과"}]}}
    messages = evidence_review_messages(request, retrieval)
    assert json.loads(messages[1]["content"])["evidence"]["passages"][0]["id"] == "E1"
    review = parse_evidence_review(json.dumps({"aspects": [
        {"id": "power", "facts": [{"text": "비교 결과", "citations": ["E1"]},
                                    {"text": "없는 출처", "citations": ["E99"]}], "missing": "조건"},
        {"id": "invented", "facts": []}]}), request, retrieval)
    assert review == {"aspects": [{"id": "power", "facts": [{"text": "비교 결과", "citations": ["E1"]}], "missing": "조건"}]}
    output = build_messages(request, retrieval, [], evidence_review=review)[-1]["content"]
    assert "EVIDENCE_REVIEW_JSON" in output and "EVIDENCE_JSON" in output
    simple = AnswerRequest(clientRequestId="simple", message="A는 무엇인가요?")
    assert evidence_review_messages(simple, retrieval) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_review", [False, True])
async def test_comparison_review_runs_before_answer_and_counts_both_calls(client, app, auth_headers, sessions, settings, principal, reviewer, embedding_client, invalid_review):
    await indexed_source(sessions, settings, principal, reviewer, embedding_client,
                         text="동일한 전압에서 A의 소비 전력은 10 mW, B는 20 mW다.")

    class Provider:
        model = "review-test"
        def __init__(self):
            self.inputs = []
        async def stream(self, messages, **kwargs):
            self.inputs.append(messages)
            if len(self.inputs) == 1:
                text = "invalid JSON" if invalid_review else json.dumps({"aspects": [{"id": "power", "facts": [
                    {"text": "같은 전압에서 A 10 mW, B 20 mW", "citations": ["E1"]}], "missing": ""}]})
                yield ProviderDelta(text=text)
            else:
                assert ("EVIDENCE_REVIEW_JSON" in messages[-1]["content"]) is not invalid_review
                yield ProviderDelta(text="같은 전압에서 A는 10 mW이고 B는 20 mW입니다 [출처: E1].")
            yield ProviderDelta(usage={"calls": 1, "costUsd": .01, "source": "provider"})

    provider = Provider()
    replace_provider(app, provider)
    executor = app.state.services.answers.executor
    executor.settings = executor.settings.model_copy(update={"provider_mode": "live"})
    response = await client.post("/api/v1/answer-runs", json={"clientRequestId": "review-flow",
        "message": "A와 B의 전력 차이를 수치로 비교해 주세요."}, headers=auth_headers)
    handle = response.json()
    await wait_finished(app.state.services.answers, handle)
    detail = (await client.get(f"/api/v1/answer-runs/{handle['runId']}", headers=auth_headers)).json()
    assert detail["status"] == "completed" and "10 mW" in detail["message"]["content"]
    assert len(provider.inputs) == 2
    assert sum(c.get("operation") == "evidence_review" for c in detail["usage"]["components"]) == 1
    assert detail["usage"]["knownCostUsd"] == pytest.approx(.02)
    assert any("항목별 근거 검토를 완료하지 못해" in warning for warning in detail["warnings"]) is invalid_review
