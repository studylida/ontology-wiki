"""Extraction model routing assertions using fake HTTP only; no operational database access."""
import ast
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch

import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.core import llm_gateway as gateway_module
from backend.app.core.config import settings
from backend.app.core.circuit_breaker import CircuitBreaker

async def checks():
    assert settings.SOURCE_EXTRACTION_MODEL=='gemini-3.8-flash'
    assert settings.SOURCE_EXTRACTION_PROVIDER=='gemini' and settings.SOURCE_EXTRACTION_REASONING_EFFORT=='medium'
    calls=[];fail_primary=False
    def respond(request):
        payload=json.loads(request.content)
        gemini=request.url.host=='generativelanguage.googleapis.com'
        if gemini:assert 'key' not in request.url.params and request.headers['x-goog-api-key']=='fixture-gemini'
        model=request.url.path.split('/models/')[1].split(':')[0] if gemini else payload['model']
        calls.append({'model':model,'gemini':gemini,'payload':payload})
        if fail_primary and model!=settings.TIER1_MODEL:return httpx.Response(503,json={'error':{'code':'fixture_unavailable'}})
        if gemini:return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'thought':True,'text':'hidden summary'},{'text':'{"ok":'},{'text':'true}'}]}}]})
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'}}]})
    client_type=httpx.AsyncClient
    def client(**kwargs):return client_type(transport=httpx.MockTransport(respond),**kwargs)
    gateway=gateway_module.LLMGateway()
    selected={'tier':'tier2_reasoning','preferred_provider':'gemini','model_override':'gemini-3.8-flash','reasoning_effort':'medium','allow_fallback':False}
    with patch.object(settings,'OPENAI_API_KEY','fixture-openai'),patch.object(settings,'GEMINI_API_KEY','fixture-gemini'),patch.object(gateway_module,'circuit_breaker',CircuitBreaker()),patch.object(gateway_module.httpx,'AsyncClient',new=client):
        result=await gateway.generate_text(prompt='fixture',**selected)
        assert result=='{"ok":true}' and len(calls)==1
        assert calls[0]['gemini'] and calls[0]['model']=='gemini-3.8-flash'
        assert calls[0]['payload']['generationConfig']=={'thinkingConfig':{'thinkingLevel':'medium'}}
        calls.clear();fail_primary=True
        assert await gateway.generate_text(prompt='fixture',**selected) is None
        assert [call['model'] for call in calls]==['gemini-3.8-flash'],'Extraction must not downgrade or switch providers'
        calls.clear()
        with patch.object(settings,'GEMINI_API_KEY',''):
            assert await gateway.generate_text(prompt='fixture',**selected) is None
        assert not calls,'An OpenAI key must not redirect a pinned Gemini extraction'
        fail_primary=False
        await gateway.generate_text(prompt='fixture',tier='tier1_fast')
        assert calls[-1]['model']==settings.TIER1_MODEL and calls[-1]['payload']['temperature']==0.2
        calls.clear();fail_primary=True
        await gateway.generate_text(prompt='fixture',tier='tier2_reasoning')
        assert [call['model'] for call in calls]==[settings.TIER2_MODEL,settings.TIER1_MODEL]
        assert all(call['payload']['temperature']==0.2 and 'reasoning_effort' not in call['payload'] for call in calls)
        calls.clear();fail_primary=False
        with patch.object(settings,'OPENAI_API_KEY',''):
            await gateway.generate_text(prompt='fixture',tier='tier1_fast')
        assert calls[0]['model']=='gemini-2.5-flash' and 'generationConfig' not in calls[0]['payload']
    tree=ast.parse((ROOT/'backend/app/services/source_service.py').read_text(encoding='utf-8'))
    calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='generate_text']
    assert len(calls)==5
    for call in calls:
        keywords={keyword.arg:keyword.value for keyword in call.keywords}
        for key,attribute in [('model_override','SOURCE_EXTRACTION_MODEL'),('preferred_provider','SOURCE_EXTRACTION_PROVIDER'),('reasoning_effort','SOURCE_EXTRACTION_REASONING_EFFORT')]:
            assert ast.unparse(keywords[key])=='settings.'+attribute
        assert ast.literal_eval(keywords['allow_fallback']) is False and ast.literal_eval(keywords['tier'])=='tier2_reasoning'
        assert ast.literal_eval(keywords['timeout_sec'])==180.0 and ast.literal_eval(keywords['slow_call_threshold_ms'])==180000.0
    print('PASS Gemini 3.8 medium routing at all five extraction/review call sites, multipart answer without thoughts, no silent provider/model switch, unrelated OpenAI and Gemini defaults/failover preserved')

if __name__=='__main__':asyncio.run(checks())
