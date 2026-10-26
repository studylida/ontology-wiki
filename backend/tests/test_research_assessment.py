"""Source acquisition and explanation validation use injected fakes, never APIs."""
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from knowledge.integrations.providers import ProviderDelta
from knowledge.research.dto import FetchRequest
from knowledge.research.entities import ResearchItem
from knowledge.research.service import ResearchService

ORIGINAL = b"Original public-source fixture bytes"
OBSERVED_USAGE = {"provider": "injected-test", "model": "injected-test-generation", "source": "provider",
    "inputTokens": 17, "outputTokens": 31, "totalTokens": 48, "calls": 1, "fixtureCalls": 0,
    "costUsd": None, "costStatus": "unknown"}


class AssessmentClient:
    model = "injected-test-generation"

    def __init__(self, result, *, malformed=False):
        self.result, self.malformed, self.calls = result, malformed, []

    async def stream(self, messages, *, effort=None, cancel_event=None):
        self.calls.append({"messages": messages, "effort": effort})
        yield ProviderDelta(text="not JSON" if self.malformed else json.dumps(self.result, ensure_ascii=False))
        yield ProviderDelta(usage=OBSERVED_USAGE)


def source_fakes(monkeypatch):
    import knowledge.research.service as module
    async def fetch(url, **kwargs):
        return ORIGINAL, "text/plain", url
    async def parse(raw, media_type):
        assert raw == ORIGINAL and media_type == "text/plain"
        return {"title": "주입한 검증 문헌", "content": "검증용 원문 본문", "readScope": "partial",
                "metadata": {}, "limitations": ["원문 일부만 읽은 검증 자료입니다."]}
    monkeypatch.setattr(module, "fetch_public", fetch)
    monkeypatch.setattr(module, "parse_download", parse)
    monkeypatch.setattr(module, "public_fetch_options", lambda _: {})


@pytest.mark.asyncio
async def test_single_sentence_limitation_is_one_item_and_effort_is_forwarded(sessions, settings, principal, monkeypatch):
    source_fakes(monkeypatch)
    sentence = "읽은 범위는 용어 정의이며 실제 공정 조건과 수율을 판단하기에는 부족합니다."
    generator = AssessmentClient({"relevance": "질문의 용어 정의를 확인하는 데 도움이 됩니다.", "limitations": sentence})
    configured = settings.model_copy(update={"provider_mode": "live", "generation_effort": "medium"})
    result = await ResearchService(sessions, configured, generator).fetch(principal,
        FetchRequest(url="https://example.org/source", query="정의와 적용 조건"))
    assert result["limitations"] == ["원문 일부만 읽은 검증 자료입니다.", sentence]
    assert result["relevanceStatus"] == "generated" and result["status"] == "content_available"
    assert result["usage"] == OBSERVED_USAGE and generator.calls[0]["effort"] == "medium"
    schema = json.loads(generator.calls[0]["messages"][0]["content"].split("JSON schema:\n", 1)[1])
    assert schema["properties"]["limitations"]["type"] == "array"
    async with sessions() as session:
        item = await session.scalar(select(ResearchItem))
        assert item.limitations[-1] == sentence and item.usage["totalTokens"] == 48
        assert (Path(settings.storage_path) / item.metadata_json["rawPath"]).read_bytes() == ORIGINAL


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [7, None, {"limitation": "wrong shape"}, [3], "", "first\nsecond"])
async def test_invalid_assessment_preserves_source_and_usage_but_not_partial_summary(sessions, settings, principal, monkeypatch, bad):
    source_fakes(monkeypatch)
    generator = AssessmentClient({"relevance": "검증 실패한 설명을 저장하면 안 됩니다.", "limitations": bad})
    configured = settings.model_copy(update={"provider_mode": "live"})
    result = await ResearchService(sessions, configured, generator).fetch(principal,
        FetchRequest(url="https://example.org/source", query="조건"))
    assert result["status"] == "content_available" and result["content"] == "검증용 원문 본문"
    assert result["relevance"] is None and result["relevanceStatus"] == "failed"
    assert result["limitations"][-1] == "본문은 확보했지만 관련성 설명 생성에 실패했습니다."
    assert result["usage"] == OBSERVED_USAGE and result["usage"]["costUsd"] is None
    async with sessions() as session:
        item = await session.scalar(select(ResearchItem))
        assert item.content and item.relevance is None and item.usage["totalTokens"] == 48


@pytest.mark.asyncio
async def test_invalid_json_also_preserves_observed_usage(sessions, settings, principal, monkeypatch):
    source_fakes(monkeypatch)
    generator = AssessmentClient({}, malformed=True)
    configured = settings.model_copy(update={"provider_mode": "live"})
    result = await ResearchService(sessions, configured, generator).fetch(principal,
        FetchRequest(url="https://example.org/source", query="조건"))
    assert result["relevanceStatus"] == "failed" and result["content"]
    assert result["usage"] == OBSERVED_USAGE


@pytest.mark.asyncio
async def test_valid_unjudged_result_is_not_labelled_generated(sessions, settings, principal, monkeypatch):
    source_fakes(monkeypatch)
    generator = AssessmentClient({"relevance": None, "limitations": ["읽은 본문에서 질문의 조건을 확인하지 못했습니다."]})
    configured = settings.model_copy(update={"provider_mode": "live"})
    result = await ResearchService(sessions, configured, generator).fetch(principal,
        FetchRequest(url="https://example.org/source", query="조건"))
    assert result["relevance"] is None and result["relevanceStatus"] == "not_determined"
    assert result["limitations"][-1] == "읽은 본문에서 질문의 조건을 확인하지 못했습니다."
