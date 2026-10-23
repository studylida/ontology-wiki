"""Research flow assertions: mocked external services, in-memory DB, no operational writes."""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from httpx import ASGITransport,AsyncClient
import httpx
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from backend.app.api import research,comparison
from backend.app.api import review_tickets
from backend.app.core.database import Base,get_db
from backend.app.core.security import get_current_user_optional
from backend.app.core.config import settings
from backend.app.core import llm_gateway as gateway_module
from backend.app.core.circuit_breaker import CircuitBreaker
from backend.app.repositories.research_repo import research_repo
from backend.app.models.entities import ConceptModel,ResearchSessionModel,ReviewTicketModel,ComparisonSessionModel
from backend.app.services.research_service import research_service
from backend.app.services.comparison_service import comparison_service
from backend.app.core.security import mask_tier3_perspective
from backend.app.models.entities import EvidenceSourceModel,PerspectiveCaseModel
from copy import deepcopy

async def comparison_spec_checks():
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    quotes={'heading':'QA company / product heading','value':'QA temperature -60 °C under QA verified condition.',
        'other':'QA temperature -60 °C under another condition.','unicode':'QA temperature −60 °C.',
        'positive':'QA temperature 60 °C.','unit':'QA temperature -60 °F.','private':'QA temperature -60 °C.'}
    specs=[];expected={}
    def spec(label,ids,expected_source=None,flags=None,value='-60',case_id=None,criteria='QA verified condition'):
        item=dict(parameter=label,value=value,unit='°C',criteria=criteria,**({'isConfidential':False} if flags is None else flags))
        if ids:item.update(evidenceId=ids[0],evidenceIds=ids[1:])
        specs.append((item,case_id))
        if expected_source:expected[label]=expected_source
    spec('public',['value'],'value')
    spec('camel-restricted',['value'],flags={'isConfidential':True})
    spec('snake-restricted',['value'],flags={'is_confidential':True})
    spec('unmarked',['value'],flags={})
    spec('snake-public',['value'],'value',flags={'is_confidential':False})
    spec('heading-first',['heading','value'],'value')
    spec('missing-first',['missing','heading','value'],'value')
    spec('private-first',['private','value'],'value')
    spec('case-fallback',['heading'],'value',case_id='value')
    spec('case-only',[],'value',case_id='value')
    spec('no-valid',['missing','heading','private'],case_id='heading')
    spec('several-valid',['value','value','other'],'value',case_id='other')
    spec('unsigned-mismatch',['value'],value='60')
    spec('negative-mismatch',['positive'])
    spec('plus-mismatch',['value'],value='+60')
    spec('unicode-source',['unicode'],'unicode')
    spec('unicode-value',['value'],'value',value='−60')
    spec('unit-mismatch',['unit'])
    spec('unknown-condition',['value'],'value',criteria='not in excerpt')
    originals=deepcopy(specs)
    try:
        async with engine.begin() as connection:await connection.run_sync(Base.metadata.create_all)
        async with factory() as db:
            db.add_all([ConceptModel(id=cid,title=cid,eng_name=cid,summary='',purpose='',principles=[],limitations=[],relations={},domain_facet='unit_process',process_category='QA',scale_level=3) for cid in ('spec-a','spec-b')])
            db.add_all([EvidenceSourceModel(id=eid,source_name=eid,source_type='academic_peer_reviewed',publisher='QA',quote=quote,external_url='',url_label='QA',credibility_tier='internal confidential' if eid=='private' else '공개 학술',referenced_concepts=[]) for eid,quote in quotes.items()])
            await db.flush()
            db.add_all([PerspectiveCaseModel(id=f'spec-case-{i}',concept_id='spec-a',perspective_id=f'case-{i}',perspective_title='QA',perspective_badge='QA',context_narrative='QA case 709',caution='',evidence_id=eid,specifications=[item]) for i,(item,eid) in enumerate(specs)])
            await db.commit()
            session=ComparisonSessionModel(id='spec-comparison',query='QA compare',context_params={'targetA':'spec-a','targetB':'spec-b'},snapshots=[{},{},{'deepDiveHistory':[]}])
            knowledge,_=await comparison_service.knowledge(db,session)
            actual={s['label']:s['evidenceId'] for c in knowledge[0]['cases'] for s in c['specifications']}
            leaked=sorted(set(actual)-set(expected));missing=sorted(set(expected)-set(actual))
            print('Comparison spec reproduction:',json.dumps({'unexpected_specs':leaked,'missing_public_specs':missing}),flush=True)
            # Compare the existing wiki mask with the expected public-only comparison input.
            for item,_ in specs:
                raw={'specifications':[deepcopy(item)],'context_narrative':'QA case 709','caution':''}
                masked=mask_tier3_perspective(raw,False);authorized=mask_tier3_perspective(raw,True)
                restricted=item.get('isConfidential',item.get('is_confidential',True)) is not False
                assert masked['specifications'][0]['value']==('***' if restricted else item['value'])
                assert masked['isMasked']==restricted and authorized['specifications']==raw['specifications'] and not authorized['isMasked']
            assert actual==expected,(leaked,missing,actual)
            assert len(knowledge[0]['cases'])==len(expected)
            with patch('backend.app.services.comparison_service.llm_gateway.generate_text',new=AsyncMock(return_value='QA mock explanation')) as model:
                await comparison_service.refresh(db,session)
            sent=json.loads(model.call_args.kwargs['prompt'])['wiki']
            assert {s['label'] for c in sent[0]['cases'] for s in c['specifications']}==set(expected)
            rows=[r for r in session.snapshots[2]['matrix'] if r['axisCategory']=='specification']
            assert len(rows)==len(expected) and {r['axis']:r['evidenceA'] for r in rows}==expected
            criteria={s['label']:s['criteria'] for c in sent[0]['cases'] for s in c['specifications']}
            assert criteria['public']=='QA verified condition' and criteria['heading-first']=='QA verified condition'
            assert criteria['unknown-condition']=='공개 발췌의 측정 조건 확인 필요'
            assert specs==originals
        print('PASS comparison public/legacy L3 policy, all evidence candidates, single spec rows, signed/Unicode/unit/condition checks, unchanged wiki masking; memory DB and mock AI only',flush=True)
    finally:await engine.dispose()

async def checks():
    await comparison_spec_checks()
    requests=[]
    def respond(request):
        payload=json.loads(request.content);requests.append(payload)
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'}}]})
    client_type=httpx.AsyncClient
    def fake_client(**kwargs):return client_type(transport=httpx.MockTransport(respond),**kwargs)
    with patch.object(settings,'OPENAI_API_KEY','fixture'),patch.object(gateway_module,'circuit_breaker',CircuitBreaker()),patch.object(gateway_module.httpx,'AsyncClient',new=fake_client):
        await gateway_module.llm_gateway.generate_text('fixture',tier='tier2_reasoning',model_override=settings.RESEARCH_MODEL,reasoning_effort='medium',preferred_provider='openai',allow_fallback=False)
        assert requests[-1]['model']=='gpt-6.1-sol' and requests[-1]['reasoning_effort']=='medium' and 'temperature' not in requests[-1]
        await gateway_module.llm_gateway.generate_text('fixture')
        assert requests[-1]['model']==settings.TIER1_MODEL and requests[-1]['temperature']==0.2 and 'reasoning_effort' not in requests[-1]
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as conn:await conn.run_sync(Base.metadata.create_all)
    app=FastAPI();app.include_router(research.router,prefix='/api/v1');app.include_router(review_tickets.router,prefix='/api/v1');app.include_router(comparison.router,prefix='/api/v1')
    level=3
    async def db():
        async with factory() as session:yield session
    async def user():return SimpleNamespace(id='fixture',name='검토관',department='검증',level=level,role='reviewer',is_active=True)
    app.dependency_overrides.update({get_db:db,get_current_user_optional:user})
    async with factory() as session:
        session.add(ConceptModel(id='existing',title='기존 본딩',eng_name='Existing Bonding',aliases=['기존 접합'],domain_facet='unit_process',process_category='본딩',scale_level=3,summary='기존 정의',purpose=''))
        session.add(ComparisonSessionModel(id='cmp',user_id='fixture',title='원래 비교',query='원래 본딩 질문',context_params={'targetA':'existing','targetB':'existing','conditions':['동일 조건']},snapshots=[{},{},{'deepDiveHistory':[]}]))
        await session.commit()
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://fixture') as client:
            with patch.object(research_repo,'crossref',new=AsyncMock(return_value=[])),patch.object(research_repo,'source_documents',return_value=iter([])):
                r=await client.post('/api/v1/research/discover',json={'searchTopic':'전혀 없는 주제'});r.raise_for_status()
                assert r.json()['evidenceFeed']==[] and not r.json()['synthesisReady']
            source='# 본딩 자료\n\n본딩은 칩을 연결한다. 신규 광학 접합은 빛을 사용해 연결하는 기술이다.'
            with patch.object(research_repo,'source_documents',return_value=iter([('fixture/bond.md',source)])),patch.object(research_repo,'crossref',new=AsyncMock(side_effect=httpx.ConnectError('fixture'))):
                r=await client.post('/api/v1/research/discover',json={'searchTopic':'본딩'});r.raise_for_status()
                found=r.json();assert len(found['evidenceFeed'])==1 and '실패' in found['notice']
            sid=found['sessionId'];eid=found['evidenceFeed'][0]['id']
            with patch.object(research_repo,'source_documents',return_value=iter([('fixture/bond.md',source)])),patch.object(research_repo,'crossref',new=AsyncMock(return_value=[])):
                roundtrip=(await client.post('/api/v1/research/discover',json={'searchTopic':'본딩','comparisonContext':{'comparisonSessionId':'cmp','originalQuestion':'브라우저의 잘못된 질문'}})).json()
            assert roundtrip['comparisonContext']['originalQuestion']=='원래 본딩 질문'
            linked_eid=roundtrip['evidenceFeed'][0]['id']
            with patch('backend.app.services.comparison_service.llm_gateway.generate_text',new=AsyncMock(return_value=None)):
                r=await client.post('/api/v1/comparison-sessions/cmp/research-evidence',json={'researchSessionId':roundtrip['sessionId'],'selectedEvidenceIds':[linked_eid]});r.raise_for_status()
                assert r.json()['query']=='원래 본딩 질문' and r.json()['contextParams']['conditions']==['동일 조건']
                assert r.json()['contextParams']['researchEvidence'][0]['id']==linked_eid
            # A full filter string is preserved; "IEEE ECTC" must not match publisher-only "IEEE".
            records=[{'title':['본딩'],'publisher':'IEEE','DOI':'10.fixture/test'}]
            with patch.object(research_repo,'source_documents',return_value=iter([])),patch.object(research_repo,'crossref',new=AsyncMock(return_value=records)):
                filtered=(await client.post('/api/v1/research/discover',json={'searchTopic':'본딩','targetInstitutions':['IEEE ECTC']})).json()
                assert filtered['evidenceFeed']==[]
            def candidate(title,payload,ids=None):return {'candidateId':'temporary','candidateType':'new_concept','title':title,'summary':'검토 제안','draftPayload':payload,'evidenceIds':ids or [eid]}
            proposal={'isNewConcept':True,'title':'신규 광학 접합','engName':None,'content':'빛을 사용해 연결하는 기술이다.','purpose':'칩 연결','domainFacet':None,'scaleLevel':None,'processCategory':''}
            response={'report':{'title':'문헌 분석','narrativeMarkdown':f'본딩 자료의 설명이다. [{eid}]','consensusFacts':['단일 자료 합의로 잘못 분류한 문장'],'tensionGaps':[]},'candidates':[
                candidate('신규 제안',proposal),candidate('중복 이름',{**proposal,'title':'기존 접합'}),candidate('가짜 근거',proposal,['missing'])]}
            async def synth(**kwargs):
                assert kwargs['model_override']=='gpt-6.1-sol' and kwargs['reasoning_effort']=='medium' and kwargs['allow_fallback'] is False
                return json.dumps(response,ensure_ascii=False)
            with patch('backend.app.services.research_service.llm_gateway.generate_text',new=synth):
                r=await client.post(f'/api/v1/research/sessions/{sid}/synthesize',json={'selectedEvidenceIds':[eid]});r.raise_for_status()
            result=r.json();assert len(result['candidates'])==2 and result['synthesisReport']['consensusFacts']==[]
            new=next(c for c in result['candidates'] if c['candidateType']=='new_concept')
            existing=next(c for c in result['candidates'] if c['candidateType']=='concept_enrichment')
            assert existing['draftPayload']['conceptId']=='existing' and new['draftPayload']['scaleLevel'] is None
            # Metadata alone and unknown selected IDs cannot become evidence.
            assert (await client.post(f'/api/v1/research/sessions/{sid}/synthesize',json={'selectedEvidenceIds':['missing']})).status_code==422
            level=1
            assert (await client.post(f"/api/v1/research/candidates/{new['candidateId']}/export-ticket",json={'sessionId':sid,'userNote':'원문 확인 요청'})).status_code==403
            level=3
            tickets=[]
            for item in (new,existing):
                r=await client.post(f"/api/v1/research/candidates/{item['candidateId']}/export-ticket",json={'sessionId':sid,'userNote':'원문 확인 요청'});r.raise_for_status();tickets.append(r.json()['ticketId'])
            async with factory() as session:
                ticket=await session.get(ReviewTicketModel,tickets[0]);new_id=ticket.concept_id
                assert ticket.structured_patches[0]['value']['scale_level'] is None and not ticket.integrity_report['verified']
                pending = next(p['value'] for p in ticket.structured_patches if p.get('path') == '/evidenceSources')
                saved_eid = pending[0]['id']
                assert pending[0]['quote'] == found['evidenceFeed'][0]['quote'] and f'[{saved_eid}]' in ticket.ai_merged_draft
                assert await session.get(ConceptModel,new_id) is None
            assert (await client.post(f'/api/v1/review-tickets/{tickets[0]}/approve',json={})).status_code==422
            preview=(await client.get(f'/api/v1/review-tickets/{tickets[0]}/wiki-preview')).json()['previewConcept']
            assert preview['purpose']=='칩 연결' and any(e['id']==saved_eid for e in preview['evidences'])
            async def directive(**kwargs):
                request=json.loads(kwargs['prompt'])
                if 'candidates' in request:
                    return json.dumps({'decisions':[{'candidateIndex':c['candidateIndex'],'supported':True,'reason':'격리 fixture 판정'} for c in request['candidates']]})
                source=request['sources'][0]
                return json.dumps({'contributions':[{'sourceId':source['id'],'content':{'summary':'','purpose':'','principles':[{'step':1,'title':'원리','content':source['quote'],'evidenceQuote':source['quote']}],'limitations':[],'perspectiveCases':[]}}]})
            with patch('backend.app.agents.directive_agent.llm_gateway.generate_text',new=directive):
                r=await client.post(f'/api/v1/review-tickets/{tickets[0]}/directive',json={'directiveText':'원문으로 원리 보강','ticketVersion':1});r.raise_for_status()
            assert {p['path'] for p in r.json()['structuredPatches']}=={'/concept','/evidenceSources','/wikiDraft'}
            preview=(await client.get(f'/api/v1/review-tickets/{tickets[0]}/wiki-preview')).json()['previewConcept']
            assert preview['purpose']=='칩 연결' and preview['principles']
            with patch('backend.app.core.citation_manager.EvidenceCitationManager.is_deprecation_intended',new=AsyncMock(return_value=False)),patch('backend.app.agents.explainer_agent.explainer_agent.precompile_concept_explainers',new=AsyncMock()),patch.object(review_tickets.cache_manager,'release_presence_lock',new=AsyncMock()),patch.object(review_tickets.cache_manager,'delete',new=AsyncMock()),patch.object(review_tickets.cache_manager,'delete_prefix',new=AsyncMock()):
                r=await client.post(f'/api/v1/review-tickets/{tickets[0]}/approve',json={'conceptPlacement':{'domainFacet':'unit_process','scaleLevel':3,'processCategory':'광학 접합'}});r.raise_for_status()
            async with factory() as session:
                concept=await session.get(ConceptModel,new_id)
                assert concept.process_category=='광학 접합' and concept.purpose=='칩 연결' and saved_eid in concept.summary
                assert (await session.get(ConceptModel,'existing')).summary=='기존 정의'
            with patch('backend.app.services.research_service.llm_gateway.generate_text',new=AsyncMock(return_value=None)):
                r=await client.post(f'/api/v1/research/sessions/{sid}/synthesize',json={'selectedEvidenceIds':[eid]});r.raise_for_status()
                assert r.json()['candidates']==[] and r.json()['synthesisReport']['generationStatus']=='source_only'
                assert '38%' not in r.json()['synthesisReport']['narrativeMarkdown']
        print('PASS honest empty/error/source-only results, exact publisher filters, Sol medium routing, existing/new deduplication, 403/422 guards, source-preserving tickets and reviewer-confirmed new concept approval; in-memory DB only')
    finally:await engine.dispose()

asyncio.run(checks())
