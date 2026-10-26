import asyncio
import json

import pytest
from sqlalchemy import func, select

from knowledge.answers.entities import AnswerEventBatch, AnswerRun
from knowledge.answers.repository import AnswerRepository
from knowledge.answers.service import AnswerService
from knowledge.conversations.entities import Conversation, Message
from knowledge.core.errors import AppError
from knowledge.core.usage import summarize_usage
from knowledge.integrations.providers import ProviderDelta
from knowledge.rag.dto import AnswerRequest


class ControlledGeneration:
    model = "test-controlled-provider"

    def __init__(self, *, fail=False, pause=False):
        self.calls, self.fail, self.pause = 0, fail, pause
        self.entered, self.release = asyncio.Event(), asyncio.Event()

    async def stream(self, messages, *, effort=None, cancel_event=None):
        self.calls += 1
        yield ProviderDelta(text="첫 실제 ", model=self.model)
        self.entered.set()
        if self.pause:
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                # Simulate a non-cooperative provider emitting one late fragment.
                yield ProviderDelta(text="취소 후 늦은 토큰", model=self.model)
        if self.fail:
            raise AppError(502, "TEST_PROVIDER_INTERRUPTED", "테스트 스트림이 중단됐습니다.", retryable=True)
        yield ProviderDelta(text="답변", model=self.model)
        yield ProviderDelta(usage={"provider": "test", "model": self.model, "inputTokens": 5,
            "outputTokens": 3, "totalTokens": 8, "costUsd": None, "costStatus": "unknown",
            "calls": 1, "pricingDate": None, "source": "provider"})


async def wait_finished(service, handle):
    runtime = service.runtimes[handle["runId"]]
    await asyncio.wait_for(asyncio.shield(runtime.task), timeout=10)
    assert runtime.finished, "The test run must reach a durable terminal state"
    return runtime


def replace_provider(app, provider):
    app.state.services.answers.executor.generation_client = provider


def test_usage_never_turns_an_unobserved_charge_into_zero():
    known = {"calls": 1, "costUsd": .01, "inputTokens": 5, "outputTokens": 2, "totalTokens": 7, "source": "provider"}
    unknown = {"calls": 1, "costUsd": None, "inputTokens": None, "outputTokens": None, "totalTokens": None, "source": "provider"}
    value = summarize_usage([known, unknown])
    assert value["costUsd"] is None
    assert value["knownCostUsd"] == .01
    assert value["unknownCostCalls"] == 1 and value["calls"] == 2
    assert value["totalTokens"] is None


@pytest.mark.asyncio
async def test_answer_persist_replay_and_idempotency(client, app, auth_headers, sessions, principal):
    provider = ControlledGeneration()
    replace_provider(app, provider)
    body = {"clientRequestId": "one-submit", "message": "DRAM 정의를 설명해 주세요.", "responseMode": "wiki"}
    response = await client.post("/api/v1/answer-runs", json=body, headers=auth_headers)
    assert response.status_code == 202, response.text
    handle = response.json()
    runtime = await wait_finished(app.state.services.answers, handle)
    detail = (await client.get(f"/api/v1/answer-runs/{handle['runId']}", headers=auth_headers)).json()
    assert detail["status"] == "completed", detail
    assert detail["message"]["content"] == "첫 실제 답변"
    assert detail["message"]["id"] == handle["messageId"]
    assert detail["usage"]["calls"] == 1 and detail["usage"]["costUsd"] is None
    assert detail["metrics"]["firstTextMs"] is not None
    duplicate = await client.post("/api/v1/answer-runs", json=body, headers=auth_headers)
    assert duplicate.json()["runId"] == handle["runId"]
    assert provider.calls == 1
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(Message)) == 2
        assert await session.scalar(select(func.count()).select_from(AnswerRun)) == 1
        persisted = await AnswerRepository(session).events(handle["runId"], 0)
    assert [e["data"]["text"] for e in persisted if e["type"] == "text.delta"] == ["첫 실제 ", "답변"]
    assert persisted[-1]["type"] == "run.completed"
    assert detail["lastSeq"] == persisted[-1]["seq"]
    replay = await client.get(handle["eventsUrl"] + "?after=1", headers=auth_headers)
    decoded = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith("data: ")]
    assert decoded == [e for e in persisted if e["seq"] > 1]
    assert provider.calls == 1
    conversation = await app.state.services.conversations.get(principal, handle["conversationId"])
    assert [m["role"] for m in conversation["messages"]] == ["user", "assistant"]
    assert conversation["nextSettings"]["responseMode"] == "wiki"
    assert conversation["nextSettings"]["extended"] is False
    assert conversation["nextSettings"]["conceptIds"] == []
    assert runtime.events[-1]["type"] == "run.completed"


@pytest.mark.asyncio
async def test_concurrent_duplicate_submit_creates_exactly_one_turn(app, principal, sessions):
    provider = ControlledGeneration()
    replace_provider(app, provider)
    service = app.state.services.answers
    request = AnswerRequest(clientRequestId="parallel", message="원리를 설명해 주세요.")
    first, second = await asyncio.gather(service.create(principal, request), service.create(principal, request))
    assert first["runId"] == second["runId"]
    await wait_finished(service, first)
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(Conversation)) == 1
        assert await session.scalar(select(func.count()).select_from(Message)) == 2
    assert provider.calls == 1
    with pytest.raises(AppError) as conflict:
        await service.create(principal, request.model_copy(update={"message": "different question"}))
    assert conflict.value.code == "IDEMPOTENCY_CONFLICT"


@pytest.mark.asyncio
async def test_cancel_preserves_partial_and_rejects_late_output(app, principal, sessions):
    provider = ControlledGeneration(pause=True)
    replace_provider(app, provider)
    service = app.state.services.answers
    handle = await service.create(principal, AnswerRequest(clientRequestId="cancel", message="설명"))
    await asyncio.wait_for(provider.entered.wait(), 5)
    runtime = service.runtimes[handle["runId"]]
    # First provider text is already observable before provider completion.
    assert [e["data"]["text"] for e in runtime.events if e["type"] == "text.delta"] == ["첫 실제 "]
    result = await service.cancel(principal, handle["runId"])
    assert result["status"] == "cancelled"
    await wait_finished(service, handle)
    detail = await service.get(principal, handle["runId"])
    assert detail["message"]["content"] == "첫 실제 "
    assert detail["status"] == "cancelled"
    assert detail["usage"]["costUsd"] is None
    async with sessions() as session:
        events = await AnswerRepository(session).events(handle["runId"], 0)
    assert events[-1]["type"] == "run.cancelled"
    assert all("취소 후" not in str(event) for event in events)
    assert not any(e["type"] == "run.completed" for e in events)


@pytest.mark.asyncio
async def test_provider_failure_is_partial_and_retry_is_a_distinct_run(app, principal):
    provider = ControlledGeneration(fail=True)
    replace_provider(app, provider)
    service = app.state.services.answers
    first = await service.create(principal, AnswerRequest(clientRequestId="failure", message="설명"))
    await wait_finished(service, first)
    detail = await service.get(principal, first["runId"])
    assert detail["status"] == "failed" and detail["message"]["content"] == "첫 실제 "
    assert detail["error"]["code"] == "TEST_PROVIDER_INTERRUPTED"
    assert detail["usage"]["calls"] == 1 and detail["usage"]["inputTokens"] is None
    provider.fail = False
    retry = await service.create(principal, AnswerRequest(clientRequestId="explicit-retry", message="설명",
        conversationId=first["conversationId"], retryOfRunId=first["runId"], responseMode="analysis"))
    await wait_finished(service, retry)
    assert retry["runId"] != first["runId"]
    final = await service.get(principal, retry["runId"])
    assert final["status"] == "completed" and final["retryOfRunId"] == first["runId"]
    assert (await service.get(principal, first["runId"]))["status"] == "failed"


@pytest.mark.asyncio
async def test_other_owner_cannot_read_replay_or_cancel(app, principal, other_principal):
    service = app.state.services.answers
    handle = await service.create(principal, AnswerRequest(clientRequestId="private-conv", message="내 질문"))
    await wait_finished(service, handle)
    for operation in (service.get(other_principal, handle["runId"]),
                      service.cancel(other_principal, handle["runId"]),
                      service.check_stream(other_principal, handle["runId"], 0)):
        with pytest.raises(AppError) as denied:
            await operation
        assert denied.value.status_code == 404


@pytest.mark.asyncio
async def test_restart_marks_unfinished_run_interrupted_without_generation(app, principal, sessions):
    service = app.state.services.answers
    handle = await service.create(principal, AnswerRequest(clientRequestId="old-run", message="설명"))
    await wait_finished(service, handle)
    async with sessions() as session, session.begin():
        run = await session.get(AnswerRun, handle["runId"])
        run.status, run.finished_at = "running", None
        # Simulated crash has only the durably saved partial/events, no active task.
        assistant = await session.get(Message, run.message_id)
        assistant.status, assistant.content = "running", "저장된 부분"
    replacement = AnswerService(sessions, app.state.services.identity, app.state.services.conversations,
        app.state.services.rag, ControlledGeneration(), app.state.settings)
    assert await replacement.recover() == 1
    detail = await replacement.get(principal, handle["runId"])
    assert detail["status"] == "interrupted" and detail["message"]["content"] == "저장된 부분"
    assert replacement.executor.generation_client.calls == 0
    with pytest.raises(AppError) as cursor:
        await replacement.check_stream(principal, handle["runId"], detail["lastSeq"] + 2)
    assert cursor.value.code == "REPLAY_CURSOR_AHEAD"


@pytest.mark.asyncio
async def test_client_metric_is_owner_scoped_first_value_and_survives_final_commit(app, principal, other_principal):
    provider = ControlledGeneration(pause=True)
    replace_provider(app, provider)
    service = app.state.services.answers
    handle = await service.create(principal, AnswerRequest(clientRequestId="client-metric", message="설명"))
    await asyncio.wait_for(provider.entered.wait(), 5)
    with pytest.raises(AppError):
        await service.record_client_metrics(other_principal, handle["runId"], 10)
    await service.record_client_metrics(principal, handle["runId"], 312.5)
    await service.record_client_metrics(principal, handle["runId"], 1)
    provider.release.set()
    await wait_finished(service, handle)
    detail = await service.get(principal, handle["runId"])
    assert detail["metrics"]["clientFirstVisibleTextMs"] == 312.5
    assert detail["metrics"]["clientTimingSource"] == "browser_untrusted"


@pytest.mark.asyncio
async def test_idle_provider_partial_is_flushed_before_next_delta(app, principal):
    provider = ControlledGeneration(pause=True)
    replace_provider(app, provider)
    service = app.state.services.answers
    service.executor.settings = app.state.settings.model_copy(update={"stream_flush_seconds": .05})
    handle = await service.create(principal, AnswerRequest(clientRequestId="idle-provider", message="설명"))
    await asyncio.wait_for(provider.entered.wait(), 5)
    await asyncio.sleep(.15)
    detail = await service.get(principal, handle["runId"])
    assert detail["status"] == "running" and detail["message"]["content"] == "첫 실제 "
    await service.cancel(principal, handle["runId"])
