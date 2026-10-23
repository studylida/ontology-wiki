"""Real source text with controlled model output; isolated API/database only."""
import asyncio
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT
sys.path.insert(0,str(REPO))
from fastapi import FastAPI
from httpx import ASGITransport,AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from backend.app.core.database import Base,get_db
from backend.app.core.security import get_current_user_optional
from backend.app.models.entities import ConceptModel,ReviewTicketModel,PerspectiveCaseModel,CausalEdgeModel,EvidenceSourceModel
from backend.app.api import review_tickets,concepts,evidences
from backend.app.agents.directive_agent import directive_agent
from backend.app.repositories.review_repo import review_repo
from backend.app.schemas.review import DirectiveModelProposal

async def checks():
    from backend.app.services.case_explanation_service import case_explanation_service
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    explanation_factory=case_explanation_service.session_factory
    case_explanation_service.session_factory=factory
    async with engine.begin() as connection:await connection.run_sync(Base.metadata.create_all)
    app=FastAPI();app.include_router(review_tickets.router,prefix='/api/v1');app.include_router(concepts.router,prefix='/api/v1');app.include_router(evidences.router,prefix='/api/v1')
    actor=SimpleNamespace(id='fixture',name='검토자',role='reviewer',department='검증',level=3,is_active=True)
    async def auth():return actor
    async def db():
        async with factory() as session:yield session
    app.dependency_overrides.update({get_db:db,get_current_user_optional:auth})
    relative='samsung/samsung_fab_06_deposition_ion.md'
    text=(REPO/'sources'/relative).read_text(encoding='utf-8')
    lines=[line.strip() for line in text.splitlines()]
    definition=next(line for line in lines if line.startswith('이때 회로 간의'))
    principle=next(line for line in lines if line.startswith('물리적 기상증착방법(PVD)는'))
    limitation='웨이퍼 위에 균일하게 박막을 형성하려면 정교하고 세밀한 기술력이 필요하다.'
    situation=next(line for line in lines if line.startswith('현재 반도체 공정에서는'))
    model_calls=[];behavior='normal'
    async def gateway(**kwargs):
        model_calls.append(kwargs)
        if '관계 주체·대상 검토' in kwargs['prompt']:
            if behavior=='relation_fail':return None
            payload=json.JSONDecoder().raw_decode(kwargs['prompt'][kwargs['prompt'].index('{'):])[0]
            return json.dumps({'decisions':[dict(candidateIndex=c['candidateIndex'],supported=True,ownerId='film',targetId='etch',reason='원문에 박막 형성 후 포토·식각 반복이 명시됨') for c in payload['candidates']]})
        if '사례·수치 귀속 검토' in kwargs['prompt']:
            if behavior=='case_fail':return None
            payload=json.JSONDecoder().raw_decode(kwargs['prompt'][kwargs['prompt'].index('[{'):])[0]
            return json.dumps({'decisions':[dict(caseIndex=c['caseIndex'],supported=c['perspectiveTitle']!='삼성 박막 정의',reason='저온 플라즈마 CVD의 적용 조건은 원문에 있고 일반 정의는 회사 사례가 아님',specifications=[dict(specIndex=s['specIndex'],supported=False,reason='원문에 해당 압력 조건 없음') for s in c['specifications']]) for c in payload]})
        request=json.loads(kwargs['prompt'])
        if 'candidates' in request:
            if behavior=='semantic_fail':return None
            decisions=[dict(candidateIndex=c['candidateIndex'],supported=not any(word in json.dumps(c['content'],ensure_ascii=False) for word in ('9999','이온주입 인접 원리','단순 정의 원리','중요성만 설명')),reason='대상 증착 메커니즘과 문맥을 확인했으며 허위 수치 및 인접 공정 설명은 보류') for c in request['candidates']]
            if behavior=='incomplete':decisions=decisions[:-1]
            if behavior=='duplicate':decisions[-1]=decisions[0]
            if behavior=='invalid_bool':decisions[0]['supported']='true'
            return json.dumps({'decisions':decisions},ensure_ascii=False)
        assert json.dumps(DirectiveModelProposal.model_json_schema(),ensure_ascii=False) in kwargs['system_instruction']
        assert 'evidenceLine' not in kwargs['system_instruction']
        if behavior=='fail':return None
        if behavior=='invalid':return 'bad-json'
        if behavior=='invalid_shape':return '[]'
        source=next(source for source in request['sources'] if source.get('localPath')==relative)
        assert request['currentSummary']=='저장 전 직접 편집한 박막 정의'
        assert definition in source['quote'] and principle in source['quote']
        content={'summary':definition,'summaryEvidenceQuote':definition,'purpose':definition,'purposeEvidenceQuote':definition,
            'principles':[{'step':1,'title':'증착 방식','content':principle,'evidenceQuote':'PVD는 화학반응 없이 금속 박막을 형성한다.'}],
            'limitations':[{'title':'균일도','description':limitation,'evidenceQuote':limitation}],
            'perspectiveCases':[{'perspectiveTitle':'플라즈마 CVD 조건','perspectiveBadge':'플라즈마 CVD','narrative':situation,'caution':'',
                'evidenceQuote':situation,'specifications':[]}],
            'nextSteps':[{'id':'etch','name':'식각공정','reason':'원문 공정 흐름','evidenceQuote':next(line for line in lines if line.startswith('이러한 구조를'))}]}
        if behavior=='semantic_rejection':
            content['limitations'].extend([{'title':'거짓 한계','description':'허위 9999 MPa','evidenceQuote':'원문에 없는 문장'}, {'title':'중요성만 설명','description':definition,'evidenceQuote':definition}])
            content['principles'].extend([
                {'step':2,'title':'허위 수식','content':principle,'formula':'E=9999','evidenceQuote':principle},
                {'step':4,'title':'단순 정의 원리','content':definition,'evidenceQuote':definition},
                {'step':3,'title':'이온주입 인접 원리','content':'이온주입 인접 원리 설명','evidenceQuote':next(line for line in lines if line.startswith('이때 불순물을'))}])
            content['perspectiveCases'].append({'perspectiveTitle':'삼성 박막 정의','narrative':definition,'evidenceQuote':definition})
            content['perspectiveCases'][0]['specifications']=[{'parameter':'압력','value':'9999','unit':'MPa','evidenceQuote':situation}]
        if behavior=='invalid_content':content['principles']={'content':'wrong list'}
        result={'contributions':[{'sourceId':source['id'],'content':content}]}
        if behavior in ('rewrite','bad_summary','invalid_summarysource'):
            result.update(summaryDraft=definition if behavior=='rewrite' else '박막 공정은 9999 MPa 조건이다.',summaryEvidence=[{'sourceId':source['id'],'quote':definition}])
        if behavior=='invalid_summarysource':result['summaryEvidence'][0]['sourceId']='unknown'
        return json.dumps(result,ensure_ascii=False)
    async def persisted(session):
        ticket=await session.get(ReviewTicketModel,'review')
        return copy.deepcopy((ticket.ai_merged_draft,ticket.human_edits,ticket.ticket_version,ticket.structured_patches,ticket.directive_history,ticket.integrity_report))
    try:
        async with factory() as session:
            session.add_all([ConceptModel(id='film',title='박막 공정',eng_name='Thin film',summary='기존 정의',purpose='',principles=[],limitations=[],relations={},domain_facet='unit_process',process_category='증착',scale_level=3),
                ConceptModel(id='etch',title='식각공정',eng_name='Etching',summary='식각 정의',purpose='',principles=[],limitations=[],relations={},domain_facet='unit_process',process_category='식각',scale_level=3)])
            session.add(ReviewTicketModel(id='review',concept_id='film',concept_title='박막 공정',title='박막 보강',review_type='파라미터 수정',author='검증',current_content='기존 정의',ai_merged_draft='오래된 AI 초안',human_edits='저장된 직접 편집',status='pending',ticket_version=1,
                structured_patches=[{'op':'add','path':'/concept','value':{'domain_facet':'unit_process','scale_level':3,'process_category':'증착'}}],integrity_report={},directive_history=[]))
            session.add(PerspectiveCaseModel(id='secret-case',concept_id='film',perspective_id='secret',perspective_title='보호된 사례',perspective_badge='기존 사례',context_narrative='비공개12345',caution='',specifications=[{'parameter':'압력','value':'12345','unit':'MPa','isConfidential':True}]))
            await session.commit()
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://isolated') as client:
            body={'directiveText':'등록 자료로 부족한 영역을 보강해줘','editedContent':'저장 전 직접 편집한 박막 정의','ticketVersion':1}
            actor=None
            assert (await client.post('/api/v1/review-tickets/review/directive',json=body)).status_code==401
            actor=SimpleNamespace(id='fixture',name='검토자',role='reviewer',department='검증',level=1,is_active=True)
            assert (await client.post('/api/v1/review-tickets/review/directive',json=body)).status_code==403
            actor.level=3
            with patch('backend.app.agents.directive_agent.llm_gateway.generate_text',new=gateway), patch(
                    'backend.app.agents.explainer_agent.explainer_agent.get_explanation', new=AsyncMock()) as popover_model:
                for behavior in ('fail','invalid','invalid_shape','invalid_content','invalid_summarysource','semantic_fail','incomplete','duplicate','invalid_bool','relation_fail','case_fail'):
                    async with factory() as session:before=await persisted(session)
                    result=await client.post('/api/v1/review-tickets/review/directive',json=body)
                    assert result.status_code==502,result.text
                    async with factory() as session:assert await persisted(session)==before
                behavior='semantic_rejection'
                result=await client.post('/api/v1/review-tickets/review/directive',json=body);assert result.status_code==200,result.text
                ticket=result.json();assert ticket['humanEdits']==body['editedContent'] and ticket['ticketVersion']==2
                assert ticket['structuredPatches'][0]['path']=='/concept'
                assert ticket['integrityReport']['evidenceMatchRate'] is None
                assert '다단 칩 적층' not in ticket['aiMergedDraft'] and '반영 규격' not in ticket['aiMergedDraft']
                pair=(await client.post('/api/v1/review-tickets/review/wiki-preview',json={'editedContent':body['editedContent']})).json()
                baseline=pair['baselineConcept']
                assert baseline['summary']=='기존 정의' and baseline['principles']==[] and baseline['evidences']==[]
                assert baseline['isRegistered'] and len(baseline['perspectives'])==1
                assert not any(baseline['relations'].values()),'Pending contributions must not appear in the public-wiki baseline'
                preview=pair['previewConcept']
                assert preview['summary']==body['editedContent'] and preview['principles'] and len(preview['limitations'])==1
                assert preview['perspectives'] and preview['relations']['next_step'] and preview['evidences']
                assert '9999' not in json.dumps(preview,ensure_ascii=False)
                assert len(preview['principles'])==1 and '이온주입 인접 원리' not in json.dumps(preview,ensure_ascii=False)
                assert all(c['perspectiveTitle']!='삼성 박막 정의' for c in preview['perspectives'])
                assert any('본문 의미 검토 보류' in warning for warning in ticket['integrityReport']['warnings'])
                assert any('회사·제품·상황 귀속 검토 보류' in warning for warning in ticket['integrityReport']['warnings'])
                assert 'PVD는 화학반응 없이 금속 박막을 형성한다.' in json.dumps(preview,ensure_ascii=False),'Semantic approval must survive a paraphrased citation'
                async with factory() as session:
                    assert not list((await session.execute(select(EvidenceSourceModel))).scalars())
                    assert not list((await session.execute(select(CausalEdgeModel))).scalars())
                    assert len(list((await session.execute(select(PerspectiveCaseModel))).scalars()))==1
                assert (await client.post('/api/v1/review-tickets/review/directive',json={**body,'editedContent':'지시 뒤 직접 편집','ticketVersion':2,'undoLast':True})).status_code==409
                actor.level=2
                masked=(await client.post('/api/v1/review-tickets/review/wiki-preview',json={'editedContent':body['editedContent']})).json()
                assert '12345' not in json.dumps(masked,ensure_ascii=False),'Both review panes must keep existing L3 masking'
                assert all('비공개12345' not in call['prompt'] for call in model_calls),'Existing protected cases must not enter cloud prompts'
                actor.level=3
                async with factory() as session:
                    concept=await session.get(ConceptModel,'film');assert concept.summary=='기존 정의' and concept.principles==[]
                # One-step undo restores the unsaved input and prior placement patches.
                undo=await client.post('/api/v1/review-tickets/review/directive',json={**body,'ticketVersion':2,'undoLast':True})
                assert undo.status_code==200,undo.text
                assert len(undo.json()['structuredPatches'])==1 and undo.json()['humanEdits']==body['editedContent']
                behavior='normal';body['ticketVersion']=3
                result=await client.post('/api/v1/review-tickets/review/directive',json=body);assert result.status_code==200,result.text
                assert (await client.post('/api/v1/review-tickets/review/directive',json=body)).status_code==409
                async with factory() as session:
                    concept=await session.get(ConceptModel,'film');concept.purpose='동시 수정';await session.commit()
                assert (await client.post('/api/v1/review-tickets/review/wiki-preview',json={'editedContent':body['editedContent']})).status_code==409
                assert (await client.post('/api/v1/review-tickets/review/approve',json={'ticketVersion':4})).status_code==409
                async with factory() as session:
                    concept=await session.get(ConceptModel,'film');concept.purpose='';await session.commit()
                    ticket=await session.get(ReviewTicketModel,'review');patches=copy.deepcopy(ticket.structured_patches)
                    changed=copy.deepcopy(patches);next(s for p in changed if p['path']=='/wikiDraft' for s in p['value']['sources'] if s.get('localPath')==relative)['sourceHash']='changed'
                    ticket.structured_patches=changed;await session.commit()
                assert (await client.post('/api/v1/review-tickets/review/wiki-preview',json={'editedContent':body['editedContent']})).status_code==409
                assert (await client.post('/api/v1/review-tickets/review/approve',json={'ticketVersion':4})).status_code==409
                async with factory() as session:
                    ticket=await session.get(ReviewTicketModel,'review');ticket.structured_patches=patches;await session.commit()
                # Preview includes latest unsaved edit without saving it, then approval uses that same edit.
                edited='승인 직전 직접 고친 개요'
                result=await client.post('/api/v1/review-tickets/review/wiki-preview',json={'editedContent':edited});assert result.status_code==200,result.text
                preview=result.json()['previewConcept']
                # Reusing a registered evidence must retain unrelated concept references.
                body_evidence=next(e for e in preview['evidences'] if e['quote']==definition)
                async with factory() as session:
                    session.add(EvidenceSourceModel(id=body_evidence['id'],source_name=body_evidence['sourceName'],source_type='source_document',publisher='Samsung',url_label='원문 출처',credibility_tier='등록 원문·발췌',quote=definition,external_url=body_evidence['externalUrl'],referenced_concepts=[{'conceptId':'unrelated','name':'별도 개념'},{'conceptId':'film','name':'박막 공정','bodyFields':{}}]))
                    await session.commit()
                approve=await client.post('/api/v1/review-tickets/review/approve',json={'humanEdits':edited,'ticketVersion':4,'targetVersion':'v1.0.1'})
                assert approve.status_code==200,approve.text
                detail=(await client.get('/api/v1/concepts/film')).json()
                assert detail['summary']==preview['summary'] and detail['purpose']==preview['purpose']
                assert detail['principles']==preview['principles'] and detail['limitations']==preview['limitations']
                assert {c['id']:c['contextNarrative'] for c in detail['perspectives']}=={c['id']:c['contextNarrative'] for c in preview['perspectives']}
                assert detail['evidenceIds'] and set(detail['evidenceIds']) <= {e['id'] for e in preview['evidences']}
                for evidence in preview['evidences']:
                    stored=await client.get('/api/v1/evidences/'+evidence['id']);assert stored.status_code==200,stored.text
                    assert stored.json()['quote']==evidence['quote'] and stored.json()['sourceName']==evidence['sourceName']
                assert detail['relations']=={key:[{k:v for k,v in link.items() if k!='isRegistered'} for link in links] for key,links in preview['relations'].items()}
                async with factory() as session:
                    saved=await session.get(EvidenceSourceModel,body_evidence['id'])
                    assert any(ref['conceptId']=='unrelated' for ref in saved.referenced_concepts)
                    fields=next(ref['bodyFields'] for ref in saved.referenced_concepts if ref['conceptId']=='film')
                    assert fields=={'purpose':detail['purpose']},'Directly edited summary must not inherit AI source claims'
                    edges=list((await session.execute(select(CausalEdgeModel))).scalars())
                    assert any(edge.source_concept_id=='film' and edge.target_concept_id=='etch' for edge in edges)
                assert (await client.post('/api/v1/review-tickets/review/approve',json={})).status_code==409
                # Explicit overview rewriting is grounded and recoverable, while invented quantities are held.
                async with factory() as session:
                    session.add(ReviewTicketModel(id='rewrite',concept_id='film',concept_title='박막 공정',title='개요 정정',review_type='개요 정정',author='검증',current_content=edited,ai_merged_draft=edited,status='pending',ticket_version=1,structured_patches=[],integrity_report={},directive_history=[]))
                    await session.commit()
                behavior='rewrite'
                rewritten=await client.post('/api/v1/review-tickets/rewrite/directive',json={**body,'ticketVersion':1})
                assert rewritten.status_code==200,rewritten.text
                assert rewritten.json()['humanEdits']==definition
                assert rewritten.json()['canUndo'] is True
                assert 'previousDraft' not in rewritten.json()['directiveHistory'][-1]
                behavior='bad_summary'
                held=await client.post('/api/v1/review-tickets/rewrite/directive',json={**body,'editedContent':'저장 전 직접 편집한 박막 정의','ticketVersion':2})
                assert held.status_code==200,held.text
                assert '9999' not in held.json()['humanEdits']
                # A new concept keeps its manually chosen classification and parent through structured approval.
                async with factory() as session:
                    _,empty=await review_repo.content(session,'new-film')
                    saved=await session.get(ReviewTicketModel,'review')
                    pending=copy.deepcopy(next(p for p in saved.structured_patches if p['path']=='/wikiDraft'))
                    pending['value']['baseSignature']=directive_agent.signature(empty)
                    for contribution in pending['value']['contributions']:contribution['content']['conceptId']='new-film'
                    session.add(ReviewTicketModel(id='new-review',concept_id='new-film',concept_title='박막 공정',title='신규 박막',review_type='신규 개념 등록',origin_type='문헌조사',author='검증',current_content='',ai_merged_draft=definition,status='pending',ticket_version=1,structured_patches=[{'op':'add','path':'/concept','value':{'domain_facet':'unit_process','process_category':'증착','scale_level':3,'parent_concept_id':'etch'}},pending],integrity_report={},directive_history=[]))
                    await session.commit()
                new_pair=await client.get('/api/v1/review-tickets/new-review/wiki-preview')
                assert new_pair.status_code==200,new_pair.text
                assert new_pair.json()['baselineConcept']['isRegistered'] is False
                assert new_pair.json()['baselineConcept']['summary']=='' and new_pair.json()['baselineConcept']['principles']==[]
                assert new_pair.json()['previewConcept']['principles'],'New proposal content must remain visible without creating a public concept'
                new_result=await client.post('/api/v1/review-tickets/new-review/approve',json={'ticketVersion':1})
                assert new_result.status_code==422,'Other session classification confirmation must remain required'
                new_result=await client.post('/api/v1/review-tickets/new-review/approve',json={'ticketVersion':1,'conceptPlacement':{'domainFacet':'unit_process','processCategory':'증착','scaleLevel':3}})
                assert new_result.status_code==200,new_result.text
                async with factory() as session:
                    new=await session.get(ConceptModel,'new-film')
                    assert new.process_category=='증착' and new.principles and new.relations['is_a'][0]['id']=='etch'
                popover_model.assert_not_awaited()
        print('PASS real Samsung source excerpts -> directive -> unsaved-edit preview -> approval -> wiki fields/graph/evidence; failed AI preserves draft; semantic rejection applied; paraphrased citations accepted; incomplete/failed reviews preserve draft; source/wiki conflicts rejected; placement preserved; undo, authorization and stale versions checked; no production writes or live AI calls')
    finally:
        case_explanation_service.session_factory=explanation_factory
        await engine.dispose()

asyncio.run(checks())
