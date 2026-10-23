"""Chat routing and grounded fallback assertions; in-memory DB and no model requests."""
import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import AsyncMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.core.database import Base, get_db
from backend.app.models.entities import ConceptModel, PerspectiveCaseModel, EvidenceSourceModel, CausalEdgeModel
from backend.app.api import chatbot, concepts
from backend.app.agents.clarifier_agent import clarifier_agent

async def checks():
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as connection:await connection.run_sync(Base.metadata.create_all)
    async def db():
        async with factory() as session:yield session
    app=FastAPI();app.include_router(chatbot.router,prefix='/api/v1');app.include_router(concepts.router,prefix='/api/v1');app.dependency_overrides[get_db]=db
    values=[('unrelated','무관한 공정',[]),('glass-real','유리 관통 전극',['TGV','유리기판']),
            ('muf-real','몰디드 언더필',['MR-MUF']),('film-real','비전도성 필름',['TC-NCF']),('memory-real','고대역폭 메모리',['HBM'])]
    async with factory() as session:
        for cid,title,aliases in values:
            session.add(ConceptModel(id=cid,title=title,eng_name=title,aliases=aliases,domain_facet='materials_infra',
                process_category='검증 분류',scale_level=4,summary=title+'의 저장된 정의',purpose='',principles=[],limitations=[],relations={}))
        for eid,cid in [('glass-source','glass-real'),('wrong-source','unrelated')]:
            title=next(title for key,title,_ in values if key==cid)
            session.add(EvidenceSourceModel(id=eid,source_name=title+' 공개 원문',source_type='source_document',publisher='fixture',
                quote='홀 직경은 25 µm이다.',external_url='https://example.org/'+eid,url_label='원문',credibility_tier='공개 원문',
                referenced_concepts=[{'conceptId':cid,'bodyFields':{'summary':title+'의 저장된 정의'}}]))
        session.add(PerspectiveCaseModel(id='public-case',concept_id='glass-real',perspective_id='public',perspective_title='공개 측정',
            perspective_badge='공개',context_narrative='공개 측정 조건',caution='',evidence_id='glass-source',
            specifications=[{'parameter':'홀 직경','value':'25','unit':'µm','isConfidential':False}]))
        session.add(PerspectiveCaseModel(id='private-case',concept_id='glass-real',perspective_id='private',perspective_title='비공개 사례',
            perspective_badge='비공개',context_narrative='비공개 987654 조건',caution='',
            specifications=[{'parameter':'비공개 압력','value':'987654','unit':'N'}]))
        session.add(CausalEdgeModel(source_concept_id='glass-real',target_concept_id='unrelated',relation_type='causes',mechanism_label='등록된 검증 메커니즘',evidence_id='glass-source'))
        await session.commit()
    prompts=[]
    async def unavailable(**kwargs):prompts.append(kwargs['prompt']);return None
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://memory') as client:
            response=await client.get('/api/v1/concepts/glass-real');response.raise_for_status()
            detail=response.json()
            assert {'TGV','유리기판','MR-MUF','유리 관통 전극'} <= set(detail['selectionTerms'])
            assert '987654' not in json.dumps(detail)
            assert detail['selectionTerms']==sorted(set(detail['selectionTerms']))
            with patch('backend.app.agents.clarifier_agent.llm_gateway.generate_text',new=unavailable):
                for question in ('💡 차세대 유리기판 TGV 공정 및 물성 표준','HBM 방열 대안: MR-MUF','HBM 방열 대안: MR-MUF vs TC-NCF 비교','TGV 관련 백서에 기록된 표준을 설명해줘','TGV 원인이 뭐야?'):
                    response=await client.post('/api/v1/chatbot/messages',json={'message':question});response.raise_for_status()
                    result=response.json();assert result['pathType']=='factoid' and not result.get('actionCard'),result
                    assert all(text not in result['answerMarkdown'] for text in ('145N','180N','285℃','계면 응력 불균일','계면 마이크로 보이드','987654'))
                result=(await client.post('/api/v1/chatbot/messages',json={'message':'TGV 표준'})).json()
                assert '홀 직경: 25 µm' in result['answerMarkdown']
                assert '유리 관통 전극 → 무관한 공정' in result['answerMarkdown'] and '등록된 검증 메커니즘' in result['answerMarkdown']
                assert {source['id'] for source in result['sourceEvidences']}=={'glass-source'}
                assert all('987654' not in prompt and 'wrong-source' not in prompt for prompt in prompts if 'glass-real' in prompt)
                unknown=(await client.post('/api/v1/chatbot/messages',json={'message':'미등록새개념XYZ 원인'})).json()
                assert '확인하지 못했습니다' in unknown['answerMarkdown'] and '무관한 공정' not in unknown['answerMarkdown']
                research=(await client.post('/api/v1/chatbot/messages',json={'message':'TGV 공인 백서 조사실로 이동해줘'})).json()
                assert research['actionCard']['actionType']=='navigate_research'
                assert parse_qs(urlsplit(research['actionCard']['targetUrl']).fragment.split('?',1)[1])['topic']==['TGV 공인 백서 조사실로 이동해줘']
                compare=(await client.post('/api/v1/chatbot/messages',json={'message':'MR-MUF와 TC-NCF 비교분석실을 열어줘'})).json()
                assert set(value[0] for value in parse_qs(urlsplit(compare['actionCard']['targetUrl']).query).values())=={'muf-real','film-real'}
                incomplete=(await client.post('/api/v1/chatbot/messages',json={'message':'MR-MUF 비교분석실을 열어줘'})).json()
                assert not incomplete.get('actionCard') and '두 개' in incomplete['answerMarkdown']
                negative=(await client.post('/api/v1/chatbot/messages',json={'message':'TGV 조사실로 이동하지 말고 여기서 설명해줘'})).json()
                assert not negative.get('actionCard')
                context=(await client.get('/api/v1/chatbot/context')).json()
                assert context['quickQuestionChips']==[] and context.get('scaleLevel') is None and context['engineMode']=='wiki'
                contextual=(await client.get('/api/v1/chatbot/context',params={'conceptId':'glass-real'})).json()
                assert contextual['quickQuestionChips']==['유리 관통 전극: 등록된 정의 설명해줘']
                stream=await client.post('/api/v1/chatbot/messages/stream',json={'message':'TGV 표준'})
                assert 'event: done' in stream.text and 'glass-source' in stream.text and 'navigate_research' not in stream.text
                # A missing topic must not inherit the open page as its answer.
                async with factory() as session:
                    glass=await session.get(ConceptModel,'glass-real')
                    glass.title='별도 샘플';glass.eng_name='Different fixture';glass.aliases=[]
                    await session.commit()
                missing=(await client.post('/api/v1/chatbot/messages',json={'message':'차세대 유리기판 TGV 공정 및 물성 표준을 설명해줘.','conceptId':'unrelated'})).json()
                assert '확인하지 못했습니다' in missing['answerMarkdown'] and '무관한 공정' not in missing['answerMarkdown']
                assert not missing['sourceEvidences'] and missing['knowledgeScope']=='local'
                contextual=(await client.post('/api/v1/chatbot/messages',json={'message':'이 공정의 정의를 알려줘','conceptId':'unrelated'})).json()
                assert '무관한 공정' in contextual['answerMarkdown']
            general=json.dumps({'domain':'semiconductor','answerMarkdown':'TGV는 유리 기판을 관통하는 전기적 연결 구조입니다. 표준 번호와 최신 개정은 원문 확인이 필요합니다.'},ensure_ascii=False)
            with patch('backend.app.agents.clarifier_agent.llm_gateway.generate_text',new=AsyncMock(return_value=general)) as gateway:
                response=await client.post('/api/v1/chatbot/messages',json={'message':'차세대 유리기판 TGV 공정 및 물성 표준을 설명해줘.','conceptId':'unrelated','knowledgeScope':'global'})
                response.raise_for_status();result=response.json()
                assert result['knowledgeScope']=='global' and 'TGV' in result['answerMarkdown']
                assert '웹 검색이나 원문 확인 결과가 아닙니다' in result['answerMarkdown']
                assert not result['sourceEvidences'] and not result.get('actionCard')
                assert '무관한 공정' not in gateway.call_args.kwargs['prompt']
                stream=await client.post('/api/v1/chatbot/messages/stream',json={'message':'새 반도체 소재의 역할은?','knowledgeScope':'global'})
                done=json.loads(stream.text.split('event: done\ndata: ')[-1].strip())
                assert done['knowledgeScope']=='global' and not done['sourceEvidences']
            outside=json.dumps({'domain':'out_of_domain','answerMarkdown':'This must not be used as an answer.'})
            with patch('backend.app.agents.clarifier_agent.llm_gateway.generate_text',new=AsyncMock(return_value=outside)):
                result=(await client.post('/api/v1/chatbot/messages',json={'message':'오늘 날씨 알려줘','knowledgeScope':'global'})).json()
                assert result['pathType']=='out_of_domain' and 'This must not' not in result['answerMarkdown']
            # Reproduced BSPDN response: valid JSON with answer fields inside schema properties.
            schema_wrapped=json.dumps({'properties':{'domain':'semiconductor','answerMarkdown':'BSPDN 설명'},
                'required':['domain','answerMarkdown'],'title':'GlobalChatAnswer','type':'object'},ensure_ascii=False)
            for valid_global in (general,'```json\n'+general+'\n```'):
                with patch('backend.app.agents.clarifier_agent.llm_gateway.generate_text',new=AsyncMock(return_value=valid_global)) as gateway:
                    result=(await client.post('/api/v1/chatbot/messages',json={'message':'TGV 설명','knowledgeScope':'global'})).json()
                    assert result['pathType']=='factoid' and result['knowledgeScope']=='global'
                    assert not result['sourceEvidences'] and not result.get('actionCard')
                    assert gateway.await_count==1
                    assert '"properties":' not in gateway.call_args.kwargs['system_instruction']
            for unavailable_global in (None,'not JSON',schema_wrapped,
                    json.dumps({'domain':'unknown','answerMarkdown':'잘못된 분야'}),
                    json.dumps({'domain':'semiconductor','answerMarkdown':''})):
                with patch('backend.app.agents.clarifier_agent.llm_gateway.generate_text',new=AsyncMock(return_value=unavailable_global)) as gateway, \
                        patch('backend.app.agents.clarifier_agent.logger.warning') as warning:
                    for endpoint in ('/messages','/messages/stream'):
                        response=await client.post('/api/v1/chatbot'+endpoint,json={'message':'TGV 설명','conceptId':'unrelated','knowledgeScope':'global'})
                        response.raise_for_status()
                        result=json.loads(response.text.split('event: done\ndata: ')[-1].strip()) if endpoint.endswith('/stream') else response.json()
                        assert result['pathType']=='error' and result['knowledgeScope']=='global'
                        assert '무관한 공정' not in result['answerMarkdown'] and not result['sourceEvidences']
                        assert not result.get('actionCard') and '일반 지식 기반 설명' not in result['answerMarkdown']
                        warning.assert_called_with('Global chat failed: %s','invalid_response_format' if unavailable_global else 'no_model_response')
                    assert gateway.await_count==2
            assert (await client.post('/api/v1/chatbot/messages',json={'message':'TGV','knowledgeScope':'web'})).status_code==422
            with patch.object(clarifier_agent,'route_chatbot_intent',new=AsyncMock(side_effect=RuntimeError('fixture outage'))):
                failure=await client.post('/api/v1/chatbot/messages/stream',json={'message':'TGV 표준'})
                failed=json.loads(failure.text.split('event: done\ndata: ')[-1].strip())
                assert '생성하지 못했습니다' in failed['answerMarkdown'] and failed['pathType']=='error'
                assert '안정적으로 보존' not in failed['answerMarkdown']
        print('PASS Local grounding/navigation/L3 regressions; unknown TGV cannot become open page; contextual local questions retained; Global semiconductor answer independent of wiki with explicit provenance and no wiki citations; domain refusal, malformed/offline answers, scope validation and SSE contract')
    finally:await engine.dispose()

if __name__=='__main__':asyncio.run(checks())
