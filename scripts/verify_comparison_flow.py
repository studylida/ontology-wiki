"""Real registered knowledge, mocked Gateway, actual ClarifierAgent and HTTP; all writes in memory."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select,func,event
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from backend.app.core.database import Base,get_db,engine as configured_engine
from backend.app.api import comparison
from backend.app.models.entities import ConceptModel,ComparisonSessionModel,ResearchSessionModel,ReviewTicketModel
from backend.app.schemas.comparison import ClarifyRequest,ComparisonDraft,ComparisonSessionCreate,ResearchEnrichmentRequest,ExportReviewRequest
from backend.app.services.comparison_service import comparison_service as service
from backend.app.agents.clarifier_agent import clarifier_agent
from verify_research_flow import comparison_spec_checks

def forbidden(*args):raise AssertionError('Configured database connection forbidden')
event.listen(configured_engine.sync_engine,'connect',forbidden)
QUESTION='MR-MUF와 TC-NCF를 HBM 적층에 적용할 때 열 영향과 휨을 중심으로 비교하고 싶어.'
def axis(label):return dict(axisId=label,label=label,category='purpose',categoryLabel='목적별 평가',terms=[label])
DRAFT=dict(targetAName='MR-MUF',targetBName='TC-NCF',purpose='열 영향과 휨을 중심으로 적용 차이 비교',applicationContext='HBM 적층',axes=[axis('열 영향'),axis('휨')])
def response(draft=DRAFT,questions=(),**extra):return json.dumps(dict(recognizedIntent='분석 의도',draft=draft,clarificationQuestions=list(questions),**extra),ensure_ascii=False)

async def checks(knowledge_db):
    engine=create_async_engine('sqlite+aiosqlite:///:memory:');factory=async_sessionmaker(engine,expire_on_commit=False)
    with sqlite3.connect(knowledge_db.resolve().as_uri()+'?mode=ro',uri=True) as source:
        source.execute('PRAGMA query_only=ON')
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            for table in ('concepts','evidence_sources','perspective_cases','causal_edges'):
                fields=[r[1] for r in source.execute('PRAGMA table_info('+table+')')];columns=','.join('"'+f+'"' for f in fields)
                rows=source.execute('SELECT '+columns+' FROM '+table).fetchall()
                if rows:await connection.exec_driver_sql('INSERT INTO '+table+' ('+columns+') VALUES ('+','.join('?' for _ in fields)+')',rows)
    app=FastAPI();app.include_router(comparison.router,prefix='/api/v1')
    async def memory():
        async with factory() as db:yield db
    app.dependency_overrides[get_db]=memory
    model=AsyncMock(return_value=response())
    try:
        with patch('backend.app.agents.clarifier_agent.llm_gateway.generate_text',new=model),patch.object(clarifier_agent,'clarify_comparison',wraps=clarifier_agent.clarify_comparison) as agent:
            async with factory() as db:
                count=(await db.execute(select(func.count(ConceptModel.id)))).scalar();assert count>=494
                result=await service.clarify(db,ClarifyRequest(query=QUESTION))
                assert agent.await_count==1 and model.await_count==1,'Every clarification must reach the actual Agent and Gateway'
                assert result['draft'].model_dump()==DRAFT and result['generationStatus']=='ready'
                assert result['targetA']=='mr-muf' and result['targetB'] is None and result['unresolvedMentions']==['TC-NCF']
                assert not result['clarificationQuestions'] and not result['branches'],'An unregistered label must not become a rejection or fake ID'
                assert model.call_args.kwargs['tier']=='tier1_fast'
                assert all(set(c)=={'id','title','engName','aliases'} for c in json.loads(model.call_args.kwargs['prompt'])['registeredConcepts'])
                assert '공개' not in json.loads(model.call_args.kwargs['prompt']).get('wiki',''),'No private specifications in clarification'
                model.return_value=response({**DRAFT,'targetBName':'TCB'},targetA='made-up-id',targetB='made-up-id')
                linked=await service.clarify(db,ClarifyRequest(query='매스 리플로우 몰디드 언더필과 열압착 본딩을 HBM에서 비교'))
                assert (linked['targetA'],linked['targetB'])==('mr-muf','tcb') and len(linked['branches'])==1
                model.return_value=response({**DRAFT,'targetAName':'신규 접합 A','targetBName':'신규 접합 B'})
                unregistered=await service.clarify(db,ClarifyRequest(query='신규 접합 A/B의 적용을 비교해줘'))
                assert unregistered['targetA'] is unregistered['targetB'] is None and unregistered['draft'].targetAName=='신규 접합 A'
                missing={**DRAFT,'targetBName':''}
                questions=[dict(questionId=field,question=field+' 확인?',options=[]) for field in ('targetAName','targetBName','purpose','axes')]
                model.return_value=response(missing,questions)
                incomplete=await service.clarify(db,ClarifyRequest(query='한 기술과 비교 대상을 정하고 싶어'))
                assert [q.questionId for q in incomplete['clarificationQuestions']]==['targetBName']
                assert incomplete['generationStatus']=='needs_confirmation'
                blank=await service.clarify(db,ClarifyRequest(query='한 기술의 상대를 정해줘',answers={'targetBName':''}))
                assert [q.questionId for q in blank['clarificationQuestions']]==['targetBName'],'Erased answers are still unanswered'
                edited=ComparisonDraft(**{**DRAFT,'targetBName':'사용자가 적은 미등록 기술','purpose':'사용자가 수정한 목적'})
                model.return_value=response(DRAFT,[dict(questionId='constraint',question='기존에 답한 조건?',options=['동일 두께'])])
                preserved=await service.clarify(db,ClarifyRequest(query=QUESTION,draft=edited,answers={'constraint':'동일 두께'}))
                assert preserved['draft']==edited and not preserved['clarificationQuestions']
                prompt=json.loads(model.call_args.kwargs['prompt']);assert prompt['question']==QUESTION and prompt['answers']['constraint']=='동일 두께'
                for invalid in (None,'bad-json','{}','{"recognizedIntent":"schema only"}'):
                    model.return_value=invalid
                    failed=await service.clarify(db,ClarifyRequest(query=QUESTION,draft=edited))
                    assert failed['generationStatus']==('model_unavailable' if invalid is None else 'invalid_response')
                    assert failed['draft']==edited and failed['recognizedIntent']==QUESTION
                model.side_effect=RuntimeError('synthetic provider failure')
                failed=await service.clarify(db,ClarifyRequest(query=QUESTION,draft=edited));assert failed['generationStatus']=='model_unavailable' and failed['draft']==edited
                model.side_effect=None;model.return_value=response(DRAFT)
                confirmed=await service.clarify(db,ClarifyRequest(query=QUESTION,targetA='mr-muf',targetB='tcb',draft=ComparisonDraft(**DRAFT)))
                assert confirmed['targetB']=='tcb' and confirmed['draft'].targetBName=='TC-NCF'
                created=await service.create(db,ComparisonSessionCreate(title='격리 비교',query=QUESTION,contextParams={'targetA':'mr-muf','targetB':'tcb','domain':'HBM 적층','axes':DRAFT['axes'],'draft':DRAFT,'clarificationAnswers':{'constraint':'동일 두께'}}))
                session=await db.get(ComparisonSessionModel,created.id)
                assert session.query==QUESTION and session.context_params['draft']==DRAFT and session.context_params['domain']=='HBM 적층'
                assert [r['axis'] for r in session.snapshots[2]['matrix'] if r['axisCategory']=='purpose']==['열 영향','휨']
                knowledge,allowed=await service.knowledge(db,session)
                session.context_params={**session.context_params,'draft':{**DRAFT,'purpose':'수율 관점으로 수정한 목적'}}
                model.return_value=None
                note=await service.explain(session,knowledge,None)
                assert '비교 목적: 수율 관점으로 수정한 목적' in note and ('원래 질문: '+QUESTION) in note
                sent=json.loads(model.call_args.kwargs['prompt']);assert sent['purpose']=='수율 관점으로 수정한 목적' and sent['originalQuestion']==QUESTION
                exported=await service.export(db,session.id,ExportReviewRequest(conceptId='mr-muf',title='격리 목적 확인',overrideReason='합성 검토',author='격리 QA'),SimpleNamespace(level=2,name='격리 QA',department='QA'))
                ticket=await db.get(ReviewTicketModel,exported['ticketId'])
                assert '비교 목적: 수율 관점으로 수정한 목적' in ticket.ai_merged_draft and ('원래 질문: '+QUESTION) in ticket.ai_merged_draft
                session.context_params={**session.context_params,'draft':DRAFT};model.return_value=response(DRAFT)
                cited=deepcopy(knowledge);cited[0]['summary']='열 설명 [E-QA-public] [E-QA-private]'
                assert service.purpose_rows(cited,{'E-QA-public':object()},['열'])[0]['evidenceIdsA']==['E-QA-public']
                unknown=service.purpose_rows(knowledge,allowed,['존재하지않는평가항목'])[0]
                assert unknown['valA']==unknown['valB']=='공개 근거 미확인'
                before=deepcopy(session.snapshots[2]['matrix'])
                safe=dict(id='qa-selected',sourceName='격리 발췌',quote='선택 자료의 조건을 확인한다.',retrievalStatus='registered_excerpt',sourceType='source_document')
                db.add(ResearchSessionModel(id='qa-research',search_topic='격리 조사',evidence_feed=[safe],synthesis_report={'comparisonContext':{'comparisonSessionId':session.id}}));await db.commit()
                await service.enrich(db,session.id,ResearchEnrichmentRequest(researchSessionId='qa-research',selectedEvidenceIds=['qa-selected']))
                assert session.snapshots[2]['matrix']==before and session.context_params['draft']==DRAFT
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://qa') as client:
                r=await client.post('/api/v1/comparison/clarify',json={'query':QUESTION});r.raise_for_status();assert r.json()['draft']==DRAFT and r.json()['targetB'] is None
                assert (await client.post('/api/v1/comparison/clarify',json={'query':QUESTION,'targetB':'made-up-id'})).status_code==422
                assert (await client.post('/api/v1/comparison/clarify',json={'query':QUESTION,'draft':{'axes':'invalid'}})).status_code==422
                assert (await client.post('/api/v1/comparison/clarify',json={})).status_code==422
                assert (await client.post('/api/v1/comparison-sessions',json={'title':'bad','query':QUESTION,'contextParams':{'targetA':'mr-muf','targetB':'mr-muf'}})).status_code==422
                assert (await client.get('/api/v1/comparison-sessions/missing')).status_code==404
        await comparison_spec_checks()
        print(f'PASS actual ClarifierAgent/Gateway routing; {count} registered concepts; unknown/partial/confirmed drafts, missing-only questions, edits, model failures, HTTP guards, unchanged comparison/research/public specification checks')
    finally:await engine.dispose()

if __name__=='__main__':
    assert len(sys.argv)==2,'Read-only registered SQLite input; all writes in memory'
    asyncio.run(checks(Path(sys.argv[1])))
