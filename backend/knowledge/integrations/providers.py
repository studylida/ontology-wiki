"""Provider ports and explicit adapters. Fixtures are never a live-provider fallback."""
from __future__ import annotations
import asyncio
import hashlib
import json
import math
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import AsyncIterator, Protocol
import httpx
from knowledge.core.errors import AppError


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: list[list[float]]
    usage: dict


@dataclass(frozen=True)
class ProviderDelta:
    text: str = ''
    usage: dict | None = None
    model: str | None = None
    provider_event_type: str | None = None


class EmbeddingClient(Protocol):
    profile_id: str
    async def embed(self, texts: list[str]) -> EmbeddingBatch: ...


class GenerationClient(Protocol):
    model: str
    def stream(self, messages: list[dict], *, effort: str | None = None,
               cancel_event: asyncio.Event | None = None) -> AsyncIterator[ProviderDelta]: ...


def unknown_usage(model: str, *, source: str = 'provider') -> dict:
    return {'provider': 'openai' if source == 'provider' else source, 'model': model,
            'inputTokens': None, 'outputTokens': None, 'totalTokens': None,
            'costUsd': None, 'costStatus': 'fixture' if source == 'fixture' else 'unknown',
            'calls': 0 if source == 'fixture' else 1, 'fixtureCalls': 1 if source == 'fixture' else 0,
            'pricingDate': None, 'source': source}


def _token_count(value):
    return type(value) is int and value >= 0


def _luna_cost(raw, service_tier, *, cache_write_ttl=None, cache_ttl_source=None):
    """Existing billing estimate policy, not account invoice data or a model benchmark."""
    if service_tier != 'default':
        return {'costUnknownReason': 'unverified_service_tier'}
    input_tokens, output_tokens = raw.get('input_tokens'), raw.get('output_tokens')
    if not all(_token_count(n) for n in (input_tokens, output_tokens)):
        return {'costUnknownReason': 'missing_or_invalid_token_counts'}
    total = raw.get('total_tokens')
    if total is not None and (not _token_count(total) or total != input_tokens + output_tokens):
        return {'costUnknownReason': 'inconsistent_token_counts'}
    details = raw.get('input_tokens_details')
    if not isinstance(details, dict):
        return {'costUnknownReason': 'missing_cache_usage'}
    cached, written = details.get('cached_tokens'), details.get('cache_write_tokens')
    if not all(_token_count(n) for n in (cached, written)):
        return {'costUnknownReason': 'missing_or_invalid_cache_usage'}
    if cached + written > input_tokens:
        return {'costUnknownReason': 'inconsistent_cache_usage'}
    lifetimes = details.get('cache_write_tokens_details')
    lifetime_source = 'provider_usage'
    if written == 0 and lifetimes is None:
        write_30m, write_12h = 0, 0
    elif isinstance(lifetimes, dict):
        write_30m, write_12h = lifetimes.get('ttl_30m_tokens'), lifetimes.get('ttl_12h_tokens')
        if not all(_token_count(n) for n in (write_30m, write_12h)):
            return {'costUnknownReason': 'missing_or_invalid_cache_write_lifetimes'}
        if write_30m + write_12h != written:
            return {'costUnknownReason': 'inconsistent_cache_write_lifetimes'}
    elif lifetimes is None and cache_write_ttl in ('30m', '12h') and cache_ttl_source in ('request', 'response_configuration'):
        write_30m, write_12h = (written, 0) if cache_write_ttl == '30m' else (0, written)
        lifetime_source = cache_ttl_source
    else:
        return {'costUnknownReason': 'missing_cache_write_lifetimes'}
    ordinary = input_tokens - cached - written
    long_context = input_tokens > 272000
    input_multiplier = Decimal(2 if long_context else 1)
    output_multiplier = Decimal('1.5') if long_context else Decimal(1)
    buckets = (('ordinaryInput', ordinary, Decimal('0.10') * input_multiplier),
               ('cachedInput', cached, Decimal('0.01') * input_multiplier),
               ('cacheWrite30m', write_30m, Decimal('0.125') * input_multiplier),
               ('cacheWrite12h', write_12h, Decimal('0.25') * input_multiplier),
               ('output', output_tokens, Decimal('0.50') * output_multiplier))
    costs = {name: {'tokens': count, 'usdPerMillion': float(rate),
                    'costUsd': float(Decimal(count) * rate / 1000000)} for name, count, rate in buckets}
    cost = sum(Decimal(count) * rate for _, count, rate in buckets) / 1000000
    return {'costUsd': float(cost), 'costStatus': 'estimated', 'pricingDate': '2026-10-26',
            'pricingSource': 'https://developers.openai.com/api/docs/models/gpt-6-luna',
            'cachePricingSource': 'https://developers.openai.com/api/docs/guides/prompt-caching',
            'pricingBasis': 'published_standard_text_rates', 'longContextPricing': long_context,
            'cacheWriteLifetimeSource': lifetime_source, 'costBreakdown': costs}


def usage_from_provider(model, raw, *, embedding=False, service_tier=None,
                        cache_write_ttl=None, cache_ttl_source=None):
    result = unknown_usage(model)
    if raw is None:
        return result
    result.update(inputTokens=raw.get('input_tokens', raw.get('prompt_tokens')),
                  outputTokens=raw.get('output_tokens', raw.get('completion_tokens')),
                  totalTokens=raw.get('total_tokens'))
    result['raw'] = raw
    embedding_rates = {'text-embedding-3-small': .02, 'text-embedding-3-large': .13}
    if embedding and model in embedding_rates and _token_count(result['inputTokens']):
        result.update(costUsd=result['inputTokens'] * embedding_rates[model] / 1000000,
            costStatus='estimated', pricingDate='2026-10-26',
            pricingSource='https://developers.openai.com/api/docs/pricing', inputUsdPerMillion=embedding_rates[model])
    elif not embedding and model == 'gpt-6-luna':
        result.update(_luna_cost(raw, service_tier, cache_write_ttl=cache_write_ttl, cache_ttl_source=cache_ttl_source))
    return result


def _generation_usage(response, *, requested_model, requested_effort, request_id,
                      requested_cache_ttl=None, has_cache_breakpoints=False):
    returned_model = response.get('model')
    verified_model = isinstance(returned_model, str) and bool(returned_model)
    actual_model = returned_model if verified_model else requested_model
    service_tier = response.get('service_tier')
    service_tier = service_tier if isinstance(service_tier, str) else None
    cache_options = response.get('prompt_cache_options')
    returned_ttl = cache_options.get('ttl') if isinstance(cache_options, dict) else None
    ttl_returned = isinstance(cache_options, dict) and 'ttl' in cache_options
    pricing_ttl = returned_ttl if ttl_returned else requested_cache_ttl
    if has_cache_breakpoints:
        pricing_ttl = None
    usage = usage_from_provider(actual_model, response.get('usage'),
        service_tier=service_tier if verified_model else None, cache_write_ttl=pricing_ttl,
        cache_ttl_source='response_configuration' if ttl_returned else 'request')
    if not verified_model and actual_model == 'gpt-6-luna':
        usage['costUnknownReason'] = 'unverified_model'
    reasoning = response.get('reasoning')
    effective_effort = reasoning.get('effort') if isinstance(reasoning, dict) else None
    effective_effort = effective_effort if isinstance(effective_effort, str) else None
    usage.update(requestId=request_id, responseId=response.get('id'), requestedModel=requested_model,
        modelSource='provider' if verified_model else 'request', requestedServiceTier='default', serviceTier=service_tier,
        requestedPromptCacheTtl=requested_cache_ttl,
        returnedPromptCacheTtl=returned_ttl if isinstance(returned_ttl, str) else None,
        requestedEffort=requested_effort, effectiveEffort=effective_effort, effort=requested_effort, effortSource='request')
    usage['responseMetadata'] = {k: response[k] for k in ('model', 'service_tier', 'reasoning', 'prompt_cache_options') if k in response}
    return usage


def _has_cache_breakpoint(value):
    if isinstance(value, dict):
        return 'prompt_cache_breakpoint' in value or any(_has_cache_breakpoint(v) for v in value.values())
    return isinstance(value, list) and any(_has_cache_breakpoint(v) for v in value)


def _provider_error(status, request_id=None):
    code = 'provider_auth' if status in (401, 403) else 'provider_rate_limit' if status == 429 else 'provider_error'
    return AppError(502, code, '모델 공급자 요청이 실패했습니다.',
                    details={'upstreamStatus': status, 'requestId': request_id},
                    retryable=status in (429, 500, 502, 503, 504))


def normalize_prefix(vector, dimensions):
    result = vector[:dimensions]
    magnitude = math.sqrt(sum(v * v for v in result))
    if len(result) != dimensions or not math.isfinite(magnitude) or magnitude == 0:
        raise AppError(502, 'invalid_embedding', '공급자가 유효하지 않은 벡터를 반환했습니다.')
    return [float(v / magnitude) for v in result]


class OpenAIEmbeddingClient:
    def __init__(self, model, dimensions, api_dimensions, transform='native', *, api_key=None, transport=None):
        self.model, self.dimensions = model, dimensions
        self.api_dimensions, self.transform = api_dimensions, transform
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.transport = transport
        if dimensions != 1536:
            raise AppError(503, 'configuration_blocked', '현재 저장 프로필은 1536차원입니다. 다른 차원은 별도 마이그레이션이 필요합니다.')
        if transform not in ('native', 'prefix_l2') or (transform == 'native' and api_dimensions != dimensions):
            raise AppError(503, 'configuration_blocked', '임베딩 차원과 변환 프로필 설정을 확인하세요.')
        self.profile_id = f'openai:{model}:api{api_dimensions}:stored{dimensions}:{transform}:v1'

    async def embed(self, texts):
        if not self.api_key:
            raise AppError(503, 'configuration_blocked', '서버의 OpenAI API 키가 설정되지 않았습니다.')
        if not texts or len(texts) > 64 or any(not t.strip() for t in texts):
            raise AppError(422, 'invalid_embedding_input', '비어 있지 않은 입력 1~64개가 필요합니다.')
        async with httpx.AsyncClient(timeout=45, transport=self.transport) as client:
            try:
                response = await client.post('https://api.openai.com/v1/embeddings',
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    json={'model': self.model, 'input': texts, 'encoding_format': 'float', 'dimensions': self.api_dimensions})
            except httpx.HTTPError as exc:
                raise AppError(502, 'provider_connection', '임베딩 공급자 연결이 중단되었습니다.', retryable=True) from exc
        if response.status_code != 200:
            raise _provider_error(response.status_code, response.headers.get('x-request-id'))
        raw = response.json()
        ordered = sorted(raw.get('data', []), key=lambda row: row['index'])
        if len(ordered) != len(texts) or [row['index'] for row in ordered] != list(range(len(texts))):
            raise AppError(502, 'invalid_embedding', '임베딩 응답의 입력 대응을 확인할 수 없습니다.')
        vectors = []
        for row in ordered:
            vector = row['embedding']
            if len(vector) != self.api_dimensions:
                raise AppError(502, 'invalid_embedding', '임베딩 차원이 요청한 프로필과 다릅니다.')
            vectors.append(normalize_prefix(vector, self.dimensions))
        usage = usage_from_provider(raw.get('model', self.model), raw.get('usage'), embedding=True)
        usage['requestId'], usage['embeddingProfile'] = response.headers.get('x-request-id'), self.profile_id
        return EmbeddingBatch(vectors, usage)


async def _sse_objects(response):
    data = []
    async for line in response.aiter_lines():
        if not line:
            if data:
                payload = '\n'.join(data)
                data.clear()
                if payload != '[DONE]':
                    yield json.loads(payload)
            continue
        if line.startswith('data:'):
            data.append(line[5:].lstrip(' '))
    if data and '\n'.join(data) != '[DONE]':
        yield json.loads('\n'.join(data))


class OpenAIGenerationClient:
    def __init__(self, model, *, api_key=None, transport=None, max_output_tokens=3000):
        self.model = model or 'unconfigured'
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.transport, self.max_output_tokens = transport, max_output_tokens

    async def stream(self, messages, *, effort=None, cancel_event=None):
        if not self.api_key or self.model == 'unconfigured':
            raise AppError(503, 'configuration_blocked', '서버에서 사용 가능한 생성 모델 ID와 API 키를 설정해야 합니다.')
        payload = {'model': self.model, 'input': messages, 'stream': True, 'store': False,
                   'service_tier': 'default', 'max_output_tokens': self.max_output_tokens}
        requested_cache_ttl = '30m' if self.model == 'gpt-6-luna' else None
        if requested_cache_ttl:
            payload['prompt_cache_options'] = {'ttl': requested_cache_ttl}
        has_cache_breakpoints = _has_cache_breakpoint(messages)
        if effort:
            payload['reasoning'] = {'effort': effort}
        completed, first_event = False, True
        async with httpx.AsyncClient(timeout=httpx.Timeout(90, connect=15), transport=self.transport) as client:
            try:
                async with client.stream('POST', 'https://api.openai.com/v1/responses',
                    headers={'Authorization': f'Bearer {self.api_key}'}, json=payload) as response:
                    if response.status_code != 200:
                        await response.aread()
                        raise _provider_error(response.status_code, response.headers.get('x-request-id'))
                    async for event in _sse_objects(response):
                        if cancel_event and cancel_event.is_set():
                            raise asyncio.CancelledError()
                        kind = event.get('type')
                        initial_kind = kind if first_event else None
                        first_event = False
                        if kind == 'response.output_text.delta':
                            yield ProviderDelta(text=event.get('delta', ''), model=self.model, provider_event_type=initial_kind)
                        elif kind == 'response.completed':
                            result = event.get('response', {})
                            usage = _generation_usage(result, requested_model=self.model, requested_effort=effort,
                                request_id=response.headers.get('x-request-id'), requested_cache_ttl=requested_cache_ttl,
                                has_cache_breakpoints=has_cache_breakpoints)
                            yield ProviderDelta(usage=usage, model=result.get('model', self.model), provider_event_type=initial_kind)
                            completed = True
                        elif kind in ('response.failed', 'response.incomplete', 'error'):
                            if initial_kind:
                                yield ProviderDelta(model=self.model, provider_event_type=initial_kind)
                            error = AppError(502, 'provider_incomplete', '공급자가 답변을 완료하지 못했습니다.',
                                             details={'eventType': kind}, retryable=True)
                            error.usage = _generation_usage(event.get('response', {}), requested_model=self.model,
                                requested_effort=effort, request_id=response.headers.get('x-request-id'),
                                requested_cache_ttl=requested_cache_ttl, has_cache_breakpoints=has_cache_breakpoints)
                            raise error
                        elif kind == 'response.refusal.delta':
                            yield ProviderDelta(text=event.get('delta', ''), model=self.model, provider_event_type=initial_kind)
                        elif initial_kind:
                            yield ProviderDelta(model=self.model, provider_event_type=initial_kind)
            except httpx.HTTPError as exc:
                raise AppError(502, 'provider_connection', '공급자 스트림이 중단되었습니다.', retryable=True) from exc
            except (json.JSONDecodeError, KeyError) as exc:
                raise AppError(502, 'provider_protocol', '공급자 스트림 형식을 읽을 수 없습니다.') from exc
        if not completed:
            raise AppError(502, 'provider_interrupted', '완료 이벤트 전에 공급자 연결이 끝났습니다.', retryable=True)


class FixtureEmbeddingClient:
    profile_id = 'fixture:sha256:1536:v1'
    async def embed(self, texts):
        vectors = []
        for text in texts:
            values = [0.0] * 1536
            for token in text.casefold().split():
                values[int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], 'big') % 1536] += 1
            vectors.append(normalize_prefix(values, 1536))
        return EmbeddingBatch(vectors, unknown_usage('fixture-embedding', source='fixture'))


class FixtureGenerationClient:
    """Labelled excerpts for contract tests, not an AI-quality or latency simulation."""
    model = 'fixture-generation'
    async def stream(self, messages, *, effort=None, cancel_event=None):
        if messages[1]['content'].startswith('WIKI_PROPOSAL_INPUT\n'):
            from ..wiki.proposals.fixture import fixture_proposal
            data = json.loads(messages[1]['content'].split('\n', 1)[1])
            yield ProviderDelta(text=json.dumps(fixture_proposal(data), ensure_ascii=False), model=self.model)
            yield ProviderDelta(usage=unknown_usage(self.model, source='fixture'), model=self.model)
            return
        evidence = json.loads(messages[1]['content'].split('\n', 1)[1])
        output = '검증용 fixture 응답입니다. 실제 모델의 해석이나 사내 판단이 아닙니다.\n\n'
        for item in evidence[:3]:
            output += '전달된 원문 구간: ' + item['text'][:220] + ' [[' + item['alias'] + ']]\n\n'
        if not evidence:
            output += '전달된 사내 근거가 없습니다. 회사의 결정 이유나 내부 수치는 확인할 수 없습니다.'
        # Deliberately split markers across chunks to test streaming normalization/cancellation.
        for offset in range(0, len(output), 13):
            if cancel_event and cancel_event.is_set():
                raise asyncio.CancelledError()
            yield ProviderDelta(text=output[offset:offset + 13], model=self.model)
            await asyncio.sleep(.02)
        usage = unknown_usage(self.model, source='fixture')
        usage['promptEvidenceIds'] = [item['passageId'] for item in evidence]
        usage['historyMessages'] = max(0, len(messages) - 3)
        yield ProviderDelta(usage=usage, model=self.model)


class DisabledEmbeddingClient:
    profile_id = 'unconfigured'
    async def embed(self, texts):
        raise AppError(503, 'configuration_blocked', '임베딩 공급자가 설정되지 않았습니다.')


class DisabledGenerationClient:
    model = 'unconfigured'
    async def stream(self, messages, **kwargs):
        raise AppError(503, 'configuration_blocked', '생성 공급자가 설정되지 않았습니다.')
        yield ProviderDelta()


def get_embedding_client(settings=None):
    if settings is None:
        from knowledge.core.config import get_settings
        settings = get_settings()
    if settings.provider_mode == 'fixture':
        return FixtureEmbeddingClient()
    if settings.provider_mode != 'live':
        return DisabledEmbeddingClient()
    return OpenAIEmbeddingClient(settings.embedding_model, settings.embedding_dimensions,
                                 settings.embedding_api_dimensions, settings.embedding_transform)


def get_generation_client(settings=None):
    if settings is None:
        from knowledge.core.config import get_settings
        settings = get_settings()
    if settings.provider_mode == 'fixture':
        return FixtureGenerationClient()
    if settings.provider_mode != 'live':
        return DisabledGenerationClient()
    return OpenAIGenerationClient(settings.generation_model)


async def generate_json(client, messages, *, effort=None, max_characters=60000):
    """Optional structured calls remain separate from the answer execution path."""
    text, usage = '', unknown_usage(client.model, source='fixture' if client.model.startswith('fixture-') else 'provider')
    try:
        async for delta in client.stream(messages, effort=effort):
            text += delta.text
            if len(text) > max_characters:
                raise AppError(502, 'structured_output_too_large', '정리 결과가 허용된 크기를 초과했습니다.')
            if delta.usage is not None:
                usage = delta.usage
    except (Exception, asyncio.CancelledError) as exc:
        if getattr(exc, 'code', None) == 'configuration_blocked':
            usage = {**usage, 'calls': 0}
        if getattr(exc, 'usage', None) is None:
            exc.usage = usage
        raise
    body = text.strip()
    if body.startswith('```'):
        body = body.split('\n', 1)[1].rsplit('```', 1)[0]
    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        error = AppError(502, 'structured_output_invalid', '정리 결과가 요청한 JSON 형식이 아닙니다.')
        error.usage = usage
        raise error from exc
    if not isinstance(result, dict):
        error = AppError(502, 'structured_output_invalid', '정리 결과는 JSON 객체여야 합니다.')
        error.usage = usage
        raise error
    return result, usage
