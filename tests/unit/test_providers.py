import asyncio
import json

import httpx
import pytest

from knowledge.core.errors import AppError
from knowledge.core.usage import summarize_usage
from knowledge.integrations.providers import (OpenAIEmbeddingClient, OpenAIGenerationClient,
    ProviderDelta, generate_json, usage_from_provider)
from knowledge.documents.parsing import segment


class Stream(httpx.AsyncByteStream):
    def __init__(self, events):
        self.events, self.closed = events, False
    async def __aiter__(self):
        for event in self.events:
            yield ("event: message\r\ndata: " + json.dumps(event) + "\r\n\r\n").encode()
    async def aclose(self):
        self.closed = True


@pytest.mark.asyncio
async def test_actual_sse_delta_boundaries_and_usage():
    stream = Stream([
        {"type": "response.output_text.delta", "delta": "반"},
        {"type": "response.output_text.delta", "delta": "도체\n"},
        {"type": "response.completed", "response": {"id": "resp_test", "model": "configured-test-model",
            "usage": {"input_tokens": 10, "output_tokens": 3, "total_tokens": 13}}},
    ])
    requests = []
    async def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, stream=stream, headers={"x-request-id": "request_test"})
    client = OpenAIGenerationClient("configured-test-model", api_key="test-only", transport=httpx.MockTransport(handle))
    chunks = [chunk async for chunk in client.stream([{"role": "user", "content": "test"}])]
    assert [c.text for c in chunks if c.text] == ["반", "도체\n"]
    assert chunks[-1].usage["totalTokens"] == 13
    assert chunks[-1].usage["costUsd"] is None
    assert requests[0]["store"] is False and requests[0]["stream"] is True
    assert requests[0]["service_tier"] == "default"
    assert "reasoning" not in requests[0]
    assert stream.closed


@pytest.mark.asyncio
async def test_eof_without_provider_completion_is_failure():
    stream = Stream([{"type": "response.output_text.delta", "delta": "부분 답변"}])
    client = OpenAIGenerationClient("configured-test-model", api_key="test-only",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)))
    seen = []
    with pytest.raises(AppError, match="완료 이벤트"):
        async for delta in client.stream([]):
            seen.append(delta.text)
    assert seen == ["부분 답변"] and stream.closed


@pytest.mark.asyncio
async def test_cancel_closes_upstream_without_success():
    stream = Stream([{"type": "response.output_text.delta", "delta": "A"}, {"type": "response.output_text.delta", "delta": "B"}])
    client = OpenAIGenerationClient("configured-test-model", api_key="test-only",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)))
    event = asyncio.Event()
    iterator = client.stream([], cancel_event=event)
    assert (await anext(iterator)).text == "A"
    event.set()
    with pytest.raises(asyncio.CancelledError):
        await anext(iterator)
    assert stream.closed


@pytest.mark.asyncio
async def test_embedding_order_dimension_profile_and_actual_usage():
    async def handle(request):
        data = json.loads(request.content)
        assert data["dimensions"] == 1536
        return httpx.Response(200, json={"model": "text-embedding-3-small", "data": [
            {"index": 1, "embedding": [0.0, 2.0] + [0.0] * 1534},
            {"index": 0, "embedding": [3.0] + [0.0] * 1535}], "usage": {"prompt_tokens": 8, "total_tokens": 8}})
    client = OpenAIEmbeddingClient("text-embedding-3-small", 1536, 1536, api_key="test-only", transport=httpx.MockTransport(handle))
    batch = await client.embed(["first", "second"])
    assert batch.vectors[0][0] == 1.0 and batch.vectors[1][1] == 1.0
    assert batch.usage["inputTokens"] == 8 and batch.usage["costStatus"] == "estimated"
    derived = OpenAIEmbeddingClient("text-embedding-3-large", 1536, 3072, "prefix_l2", api_key="test-only")
    native = OpenAIEmbeddingClient("text-embedding-3-large", 1536, 1536, "native", api_key="test-only")
    assert derived.profile_id != native.profile_id


@pytest.mark.asyncio
async def test_invalid_json_keeps_observed_cost_usage():
    class BadJson:
        model = "test-model"
        async def stream(self, messages, **kwargs):
            yield ProviderDelta(text="This is not JSON.")
            yield ProviderDelta(usage={"totalTokens": 9, "costUsd": None})
    with pytest.raises(AppError) as caught:
        await generate_json(BadJson(), [])
    assert caught.value.usage["totalTokens"] == 9


def test_crlf_frontmatter_and_exact_offsets():
    text = '---\r\ntitle: Sample\r\n---\r\n\r\n# 원리\r\n핵심 조건은 실제 원문에 있다.\r\n'
    passages = segment(text, "Sample")
    assert len(passages) == 1
    p = passages[0]
    assert "title: Sample" not in p.text
    assert text[p.start_offset:p.end_offset] == p.text
    assert p.locator == "원리"


@pytest.mark.asyncio
async def test_first_provider_event_is_observed_without_fake_text():
    stream = Stream([
        {"type": "response.created", "response": {"id": "resp_test"}},
        {"type": "response.output_text.delta", "delta": "실제 본문"},
        {"type": "response.completed", "response": {"model": "configured-test-model", "usage": None}},
    ])
    client = OpenAIGenerationClient("configured-test-model", api_key="test-only",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)))
    chunks = [chunk async for chunk in client.stream([])]
    assert chunks[0].provider_event_type == "response.created" and chunks[0].text == ""
    assert [chunk.text for chunk in chunks if chunk.text] == ["실제 본문"]


@pytest.mark.asyncio
async def test_incomplete_provider_response_retains_observed_usage():
    stream = Stream([{"type": "response.incomplete", "response": {"model": "configured-test-model",
        "usage": {"input_tokens": 20, "output_tokens": 4, "total_tokens": 24}}}])
    client = OpenAIGenerationClient("configured-test-model", api_key="test-only",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)))
    with pytest.raises(AppError) as incomplete:
        await generate_json(client, [])
    assert incomplete.value.usage["totalTokens"] == 24
    assert incomplete.value.usage["costUsd"] is None


def luna_usage(*, input_tokens=12000, output_tokens=1000, cached=4000,
               write_30m=3000, write_12h=4000):
    return {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_tokens_details": {"cached_tokens": cached,
                "cache_write_tokens": write_30m + write_12h,
                "cache_write_tokens_details": {"ttl_30m_tokens": write_30m, "ttl_12h_tokens": write_12h}},
            "output_tokens_details": {"reasoning_tokens": 200}}


def test_luna_prices_disjoint_cache_buckets_and_reasoning_output_once():
    raw = luna_usage()
    usage = usage_from_provider("gpt-6-luna", raw, service_tier="default")
    assert usage["costUsd"] == pytest.approx(0.002015)
    assert usage["costStatus"] == "estimated" and usage["raw"] == raw
    assert usage["costBreakdown"]["ordinaryInput"]["tokens"] == 1000
    assert usage["costBreakdown"]["cacheWrite30m"]["costUsd"] == pytest.approx(0.000375)
    assert usage["costBreakdown"]["cacheWrite12h"]["costUsd"] == pytest.approx(0.001)
    assert usage["costBreakdown"]["output"]["tokens"] == 1000
    assert usage["pricingDate"] == "2026-10-26"


@pytest.mark.parametrize("input_tokens,expected,long_context", [
    (272000, 0.0277, False), (272001, 0.0551502, True),
])
def test_luna_long_context_multiplier_applies_to_entire_request(input_tokens, expected, long_context):
    raw = luna_usage(input_tokens=input_tokens, cached=0, write_30m=0, write_12h=0)
    usage = usage_from_provider("gpt-6-luna", raw, service_tier="default")
    assert usage["costUsd"] == pytest.approx(expected)
    assert usage["longContextPricing"] is long_context


def test_luna_long_context_multiplier_also_applies_to_cache_reads_and_writes():
    usage = usage_from_provider("gpt-6-luna", luna_usage(input_tokens=272001), service_tier="default")
    assert usage["costUsd"] == pytest.approx(0.0557802)


@pytest.mark.parametrize("tier", [None, "auto", "priority", "flex", "unrecognized"])
def test_luna_never_assumes_standard_when_returned_tier_is_unverified(tier):
    raw = luna_usage()
    usage = usage_from_provider("gpt-6-luna", raw, service_tier=tier)
    assert usage["costUsd"] is None and usage["costStatus"] == "unknown"
    assert usage["costUnknownReason"] == "unverified_service_tier"
    assert usage["raw"] == raw


@pytest.mark.parametrize("missing", ["input_tokens_details", "cached_tokens", "cache_write_tokens",
    "cache_write_tokens_details", "ttl_30m_tokens", "ttl_12h_tokens"])
def test_luna_missing_cache_information_remains_unknown(missing):
    raw = luna_usage()
    if missing == "input_tokens_details":
        raw.pop(missing)
    elif missing.startswith("ttl_"):
        raw["input_tokens_details"]["cache_write_tokens_details"].pop(missing)
    else:
        raw["input_tokens_details"].pop(missing)
    usage = usage_from_provider("gpt-6-luna", raw, service_tier="default")
    assert usage["costUsd"] is None and usage["raw"] == raw


@pytest.mark.parametrize("field,bad", [("input_tokens", -1), ("output_tokens", True),
    ("output_tokens", 1.5), ("cached_tokens", 50000), ("cache_write_tokens", -1),
    ("ttl_30m_tokens", 0), ("total_tokens", 999)])
def test_luna_rejects_inconsistent_or_noninteger_billing_counts(field, bad):
    raw = luna_usage()
    if field in ("input_tokens", "output_tokens", "total_tokens"):
        raw[field] = bad
    elif field.startswith("ttl_"):
        raw["input_tokens_details"]["cache_write_tokens_details"][field] = bad
    else:
        raw["input_tokens_details"][field] = bad
    usage = usage_from_provider("gpt-6-luna", raw, service_tier="default")
    assert usage["costUsd"] is None and usage["raw"] == raw


def test_luna_observed_zero_writes_need_no_lifetime_guess_and_aliases_are_not_inferred():
    raw = luna_usage(cached=4000, write_30m=0, write_12h=0)
    raw["input_tokens_details"].pop("cache_write_tokens_details")
    usage = usage_from_provider("gpt-6-luna", raw, service_tier="default")
    assert usage["costUsd"] == pytest.approx(0.00134)
    alias = usage_from_provider("gpt-6-luna-unverified-snapshot", raw, service_tier="default")
    assert alias["costUsd"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal", ["response.completed", "response.incomplete"])
async def test_luna_sse_preserves_returned_tier_and_effort_for_success_and_incomplete(terminal):
    raw = luna_usage()
    stream = Stream([{"type": terminal, "response": {"id": "resp_pricing", "model": "gpt-6-luna",
        "service_tier": "default", "reasoning": {"effort": "medium"}, "usage": raw}}])
    requests = []
    async def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, stream=stream)
    client = OpenAIGenerationClient("gpt-6-luna", api_key="test-only", transport=httpx.MockTransport(handle))
    if terminal == "response.completed":
        chunks = [chunk async for chunk in client.stream([], effort="low")]
        usage = chunks[-1].usage
    else:
        with pytest.raises(AppError) as caught:
            _ = [chunk async for chunk in client.stream([], effort="low")]
        usage = caught.value.usage
    assert requests[0]["service_tier"] == "default"
    assert requests[0]["reasoning"]["effort"] == "low"
    assert usage["requestedEffort"] == "low" and usage["effectiveEffort"] == "medium"
    assert usage["requestedServiceTier"] == "default" and usage["serviceTier"] == "default"
    assert usage["responseMetadata"]["reasoning"] == {"effort": "medium"}
    assert usage["raw"] == raw and usage["costUsd"] == pytest.approx(0.002015)
    assert stream.closed


@pytest.mark.asyncio
async def test_luna_requested_configuration_does_not_fill_missing_returned_values():
    stream = Stream([{"type": "response.completed", "response": {"model": "gpt-6-luna", "usage": luna_usage()}}])
    client = OpenAIGenerationClient("gpt-6-luna", api_key="test-only",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)))
    chunks = [chunk async for chunk in client.stream([], effort="low")]
    usage = chunks[-1].usage
    assert usage["requestedEffort"] == "low" and usage["effectiveEffort"] is None
    assert usage["requestedServiceTier"] == "default" and usage["serviceTier"] is None
    assert usage["costUsd"] is None


@pytest.mark.asyncio
async def test_luna_missing_returned_model_does_not_make_requested_model_a_billing_fact():
    stream = Stream([{"type": "response.completed", "response": {"service_tier": "default", "usage": luna_usage()}}])
    client = OpenAIGenerationClient("gpt-6-luna", api_key="test-only",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)))
    chunks = [chunk async for chunk in client.stream([])]
    usage = chunks[-1].usage
    assert usage["model"] == "gpt-6-luna" and usage["modelSource"] == "request"
    assert usage["costUsd"] is None and usage["costUnknownReason"] == "unverified_model"


def test_usage_summary_keeps_partial_known_cost_and_generation_observations():
    generation = usage_from_provider("gpt-6-luna", luna_usage(), service_tier="default")
    generation.update(requestedEffort=None, effectiveEffort="medium",
                      requestedServiceTier="default", serviceTier="default")
    embedding = usage_from_provider("text-embedding-3-large", {"prompt_tokens": 10, "total_tokens": 10}, embedding=True)
    known = summarize_usage([generation, embedding])
    assert known["costUsd"] == pytest.approx(0.0020163)
    assert known["effectiveEffort"] == "medium" and known["requestedEffort"] is None
    unknown = usage_from_provider("gpt-6-luna", luna_usage())
    combined = summarize_usage([generation, embedding, unknown])
    assert combined["costUsd"] is None and combined["unknownCostCalls"] == 1
    assert combined["knownCostUsd"] == pytest.approx(known["costUsd"])


@pytest.mark.asyncio
@pytest.mark.parametrize("returned_options,expected,source", [
    (None, 0.000698675, "request"),
    ({"ttl": "12h"}, 0.00092455, "response_configuration"),
    ({"ttl": "unrecognized"}, None, None),
])
async def test_luna_observed_write_count_uses_explicit_single_ttl_with_provenance(returned_options, expected, source):
    # Field shape observed in the live extraction run; no network is used here.
    raw = {"input_tokens": 1810, "output_tokens": 945, "total_tokens": 2755,
           "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 1807},
           "output_tokens_details": {"reasoning_tokens": 486}}
    response = {"model": "gpt-6-luna", "service_tier": "default", "usage": raw}
    if returned_options is not None:
        response["prompt_cache_options"] = returned_options
    requests = []
    async def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, stream=Stream([{"type": "response.completed", "response": response}]))
    client = OpenAIGenerationClient("gpt-6-luna", api_key="test-only", transport=httpx.MockTransport(handle))
    chunks = [chunk async for chunk in client.stream([{"role": "user", "content": "source text"}])]
    usage = chunks[-1].usage
    assert requests[0]["prompt_cache_options"] == {"ttl": "30m"}
    if expected is None:
        assert usage["costUsd"] is None
    else:
        assert usage["costUsd"] == pytest.approx(expected)
        assert usage["cacheWriteLifetimeSource"] == source
    assert usage["raw"] == raw
    # Earlier stored calls without an explicit request TTL are not repriced.
    assert usage_from_provider("gpt-6-luna", raw, service_tier="default")["costUsd"] is None


@pytest.mark.asyncio
async def test_luna_request_ttl_does_not_price_unknown_mixed_breakpoint_writes():
    raw = luna_usage()
    raw["input_tokens_details"].pop("cache_write_tokens_details")
    stream = Stream([{"type": "response.completed", "response": {
        "model": "gpt-6-luna", "service_tier": "default", "usage": raw}}])
    client = OpenAIGenerationClient("gpt-6-luna", api_key="test-only",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream)))
    messages = [{"role": "user", "content": [{"type": "input_text", "text": "source",
        "prompt_cache_breakpoint": {"mode": "explicit", "ttl": "12h"}}]}]
    chunks = [chunk async for chunk in client.stream(messages)]
    assert chunks[-1].usage["costUsd"] is None
    assert chunks[-1].usage["costUnknownReason"] == "missing_cache_write_lifetimes"
