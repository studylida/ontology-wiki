"""Contextual popover contracts: in-memory DB, local cache and mocked model only."""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import event
from backend.app.api import concepts
from backend.app.core.cache import CacheManager
from backend.app.core.database import Base, get_db
from backend.app.models.entities import ConceptModel, PerspectiveCaseModel, CausalEdgeModel, EvidenceSourceModel
from backend.app.repositories.concept_repo import concept_repo


async def checks():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    queries = []
    event.listen(engine.sync_engine, 'before_cursor_execute',
        lambda conn, cursor, statement, parameters, context, many: queries.append(statement))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async def db():
        async with factory() as session:
            yield session
    app = FastAPI()
    app.include_router(concepts.router, prefix='/api/v1')
    app.dependency_overrides[get_db] = db
    context_a = '양품을 선별한다.'
    context_b = '양품의 비율을 수율로 관리한다.'
    async with factory() as session:
        for cid, title, aliases in [('eds', 'EDS 공정', []), ('registered', '등록 검사', ['검사 별칭'])]:
            session.add(ConceptModel(id=cid, title=title, eng_name=title, aliases=aliases,
                domain_facet='unit_process', process_category='검사', scale_level=3,
                summary=context_a + ' ' + context_b, purpose='웨이퍼 상태의 전기적 검사',
                principles=[], limitations=[], relations={}))
        session.add(PerspectiveCaseModel(id='private-case', concept_id='eds', perspective_id='private',
            perspective_title='비공개 사례', perspective_badge='비공개',
            context_narrative='비공개 압력 987654', caution='',
            specifications=[{'parameter': '비공개 압력', 'value': 987654, 'unit': 'bar', 'isConfidential': True}]))
        for eid, tier in [('source-real', '공개 원문'), ('source-private', 'L3 대외비')]:
            session.add(EvidenceSourceModel(id=eid, source_name='검사 원문', source_type='source_document',
                publisher='fixture', quote='등록된 검사 근거', external_url='https://example.org/' + eid,
                url_label='원문', credibility_tier=tier, referenced_concepts=[]))
        session.add(CausalEdgeModel(source_concept_id='eds', target_concept_id='registered',
            relation_type='controls', mechanism_label='실제 검사 관계', evidence_id='source-real'))
        session.add(CausalEdgeModel(source_concept_id='eds', target_concept_id='registered',
            relation_type='depends_on', mechanism_label='PRIVATE-MECHANISM-987654', evidence_id='source-private'))
        await session.commit()
    cache = CacheManager()
    seen = []
    async def generate(**kwargs):
        data = json.loads(kwargs['prompt'])
        seen.append(data)
        assert '987654' not in kwargs['prompt'] and 'PRIVATE-MECHANISM' not in kwargs['prompt']
        assert 'E-01' not in kwargs['prompt']
        assert kwargs['tier'] == 'tier1_fast'
        return json.dumps({'definition': '검사 기준을 만족하는 대상을 뜻한다.',
            'contextSentence': '수율을 계산할 때 세는 대상이다.' if '수율' in data['selectionContext']
                else '이 문장에서는 검사 후 선별하는 대상을 가리킨다.'}, ensure_ascii=False)
    try:
        with patch('backend.app.services.concept_service.cache_manager', cache), \
                patch('backend.app.agents.explainer_agent.llm_gateway.generate_text', new=AsyncMock(side_effect=generate)) as gateway:
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://fixture') as client:
                endpoint = '/api/v1/concepts/eds/contextual-explainer'
                await cache.set('explainer:eds:default:양품', {'fake': 'E-01'})
                queries.clear()
                with patch.object(concepts.concept_service, 'get_enriched_concept_detail',
                        side_effect=AssertionError('Popover must not assemble the detail screen')):
                    first = await client.post(endpoint, json={'term_id': '양품', 'selection_context': context_a})
                first.raise_for_status()
                result = first.json()
                assert result['definition'] and result['contextSentence'] and result['cached'] is False
                assert result['title'] == '양품'
                assert not result.get('childConceptId') and not result.get('deepLink') and not result.get('sourceEvidence')
                assert seen[-1]['selectedText'] == '양품' and seen[-1]['selectionContext'] == context_a
                assert seen[-1]['relations'] == [] and seen[-1]['evidences'] == []
                cold_queries = len(queries)
                queries.clear()
                with patch.object(concepts.concept_service, 'get_enriched_concept_detail',
                        side_effect=AssertionError('Cached popover must still avoid detail assembly')):
                    repeated = (await client.post(endpoint, json={'term_id': '양품', 'selection_context': context_a})).json()
                assert repeated['cached'] is True and gateway.await_count == 1
                assert not any('FROM causal_edges' in q and 'WHERE' not in q for q in queries)
                assert not any('FROM evidence_sources' in q and 'WHERE' not in q for q in queries)
                assert sum('FROM concepts' in q and 'WHERE' not in q for q in queries) == 1
                print('Popover SQL queries:', {'miss': cold_queries, 'hit': len(queries), 'hit_model_calls': 0})
                changed = (await client.post(endpoint, json={'term_id': '양품', 'selection_context': context_b})).json()
                assert changed['contextSentence'] != result['contextSentence'] and gateway.await_count == 2
                assert seen[-1]['selectionContext'] == context_b
                literal = '  DrAm + 기묘한 표현  '
                unusual = (await client.post(endpoint, json={'term_id': literal, 'selection_context': context_a})).json()
                assert unusual['title'] == seen[-1]['selectedText'] == literal
                assert not unusual.get('childConceptId')
                registered = (await client.get(endpoint, params={'term_id': '검사 별칭'})).json()
                assert registered['childConceptId'] == 'registered' and registered['deepLink'].endswith('registered')
                assert registered['sourceEvidence']['evidenceIds'] == ['source-real']
                assert seen[-1]['registeredDefinition'] and len(seen[-1]['relations']) == 1
                assert seen[-1]['relations'][0]['type'] == 'controls'
                assert [item['id'] for item in seen[-1]['evidences']] == ['source-real']
                forged = (await client.post(endpoint, json={'term_id': '양품', 'selection_context': '비공개 압력 987654'})).json()
                assert '987654' not in json.dumps(forged, ensure_ascii=False)
                assert seen[-1]['selectionContext'] == ''
                ordinary = '임의 bar 표현'
                assert (await client.post(endpoint, json={'term_id': ordinary})).status_code == 200
                assert seen[-1]['selectedText'] == ordinary
                before = gateway.await_count
                for secret in ('987654', ' 987654 ', '987654\nbar', '압력 987654 bar'):
                    assert (await client.post(endpoint, json={'term_id': secret})).status_code == 403
                assert (await client.get(endpoint, params={'term_id': '987654'})).status_code == 403
                assert (await client.post(endpoint, json={'term_id': '양품', 'selection_context': 'x' * 601})).status_code == 422
                assert (await client.post('/api/v1/concepts/missing/contextual-explainer', json={'term_id': '양품'})).status_code == 404
                assert (await client.get('/api/v1/concepts/missing/contextual-explainer', params={'term_id': '양품'})).status_code == 404
                assert gateway.await_count == before
                detail = (await client.get('/api/v1/concepts/eds')).json()
                private = next(case for case in detail['perspectives'] if case['id'] == 'private-case')
                assert private['isMasked'] and private['specifications'][0]['value'] == '***'
                await cache.delete_prefix('concept:explainer:eds:')
                refreshed = (await client.post(endpoint, json={'term_id': '양품', 'selection_context': context_a})).json()
                assert refreshed['cached'] is False and gateway.await_count == before + 1
                for index, answer in enumerate((None, 'not JSON', '{"properties":{}}',
                        '{"definition":" ","contextSentence":"해설"}',
                        '{"definition":"뜻","contextSentence":"해설","evidenceIds":["E-01"]}')):
                    with patch('backend.app.agents.explainer_agent.llm_gateway.generate_text', new=AsyncMock(return_value=answer)) as failed:
                        response = await client.post(endpoint, json={'term_id': f'실패표현{index}'})
                        assert response.status_code == 503 and not response.json().get('definition')
                        assert response.json()['detail'] == '문맥 해설을 생성하지 못했습니다.'
                        assert failed.await_count == 1
                with patch.object(concept_repo, 'get_by_id', side_effect=RuntimeError('PRIVATE DATABASE ERROR')):
                    for request in (client.post(endpoint, json={'term_id': '양품'}),
                                    client.get(endpoint, params={'term_id': '양품'})):
                        response = await request
                        assert response.status_code == 500
                        assert 'PRIVATE' not in response.text
                        assert response.json()['detail'] == '문맥 해설 요청을 처리하지 못했습니다.'
                with patch('backend.app.agents.explainer_agent.llm_gateway.generate_text', new=AsyncMock(return_value='invalid')) as failed:
                    assert (await client.get(endpoint, params={'term_id': 'GET 실패'})).status_code == 503
                    assert failed.await_count == 1
        print('PASS literal selection/context, separate content, contextual cache/invalidation, GET compatibility, actual public links/edges/evidence, no fabricated IDs or sources, untrusted/L3 isolation, 403/404/422/503 and one model call')
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(checks())
