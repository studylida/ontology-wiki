"""Isolated file DB and HTTP fixture. The configured application engine cannot connect."""
import asyncio, copy, json, os, sys, uuid, socket, tempfile
from pathlib import Path
from types import SimpleNamespace
_temporary=tempfile.TemporaryDirectory(prefix='wiki-review-')
ROOT=Path(sys.argv[sys.argv.index('--artifacts-dir')+1]) if '--artifacts-dir' in sys.argv else Path(_temporary.name)
ROOT.mkdir(parents=True,exist_ok=True)
REPO=Path(__file__).resolve().parents[1]
os.chdir(REPO);sys.path=[str(REPO)]+[p for p in sys.path if Path(p or '.').resolve()!=ROOT]
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from backend.app.core.database import Base,get_db,engine as configured_engine
def forbidden(*args):raise AssertionError('Operational DB connections are forbidden')
event.listen(configured_engine.sync_engine,'connect',forbidden)
from fastapi import FastAPI,Request
from fastapi.responses import FileResponse,HTMLResponse
from httpx import AsyncClient,ASGITransport
from backend.app.core.security import get_current_user_optional
from backend.app.models.entities import ConceptModel,ReviewTicketModel,PerspectiveCaseModel,EvidenceSourceModel,CausalEdgeModel
from backend.app.api import review_tickets,concepts,evidences
from backend.app.services import review_service as service_module
from backend.app.services.review_service import review_service
from backend.app.services.case_explanation_service import case_explanation_service
from backend.app.agents.directive_agent import directive_agent
from backend.app.core.llm_gateway import llm_gateway
from backend.app.repositories.review_repo import review_repo
from backend.app.schemas.review import DirectiveModelProposal

class PrivateCache:
    def __init__(self):self.holders={}
    async def get_presence_holder(self,key):return self.holders.get(key)
    async def acquire_presence_lock(self,key,user,**kw):self.holders[key]=user;return True
    async def renew_presence_lock(self,key,user,**kw):return True,''
    async def steal_presence_lock(self,key,user,**kw):self.holders[key]=user;return True
    async def release_presence_lock(self,key,*args):self.holders.pop(key,None);return True
    async def get(self,*args):return None
    async def set(self,*args,**kw):pass
    async def delete(self,*args):pass
    async def delete_prefix(self,*args):pass

async def fixture():
    dbfile=ROOT/('isolated-'+uuid.uuid4().hex+'.sqlite')
    engine=create_async_engine('sqlite+aiosqlite:///'+dbfile.as_posix())
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as c:await c.run_sync(Base.metadata.create_all)
    cache=PrivateCache();review_tickets.cache_manager=service_module.cache_manager=cache
    case_explanation_service.session_factory=factory
    case_explanation_service.schedule=lambda *a,**kw:None
    # Reuse the bounded Samsung fixture and semantic model responses from the product regression.
    script=(REPO/'scripts/verify_review_directive.py').read_text(encoding='utf-8')
    block=script[script.index("    relative='samsung/"):script.index('    async def persisted')]
    block='\n'.join(line[4:] for line in block.splitlines())
    block=block.replace("assert request['currentSummary']=='저장 전 직접 편집한 박막 정의'", "assert isinstance(request['currentSummary'],str)")
    ns=dict(REPO=REPO,json=json,DirectiveModelProposal=DirectiveModelProposal)
    exec(block,ns);llm_gateway.generate_text=ns['gateway']
    async with factory() as db:
        db.add_all([ConceptModel(id='film',title='박막 공정',eng_name='Thin film',summary='저장 전 직접 편집한 박막 정의',purpose='기존 목적',principles=[dict(step=1,title='기준 원리',content=ns['principle'],formula=None)],limitations=[],relations={'part_of':[{'id':'unregistered-legacy','name':'기존 미등록 참조'}]},domain_facet='unit_process',process_category='증착',scale_level=3),
            ConceptModel(id='etch',title='식각공정',eng_name='Etching',summary='식각 정의',purpose='',principles=[],limitations=[],relations={},domain_facet='unit_process',process_category='식각',scale_level=3)])
        for key in ('fixture-review','fixture-other','fixture-rival'):
            db.add(ReviewTicketModel(id=key,concept_id='film',concept_title='박막 공정',title=key,review_type='파라미터 수정',author='격리 검증',current_content='저장 전 직접 편집한 박막 정의',ai_merged_draft='저장 전 직접 편집한 박막 정의',status='pending',ticket_version=1,structured_patches=[],directive_history=[],integrity_report={}))
        db.add(PerspectiveCaseModel(id='secret-fixture',concept_id='film',perspective_id='secret-fixture',perspective_title='보호된 사례',perspective_badge='L3',context_narrative='기밀 조건 SECRET-12345',caution='',specifications=[dict(parameter='압력',value='SECRET-12345',unit='MPa',isConfidential=True)]))
        db.add(PerspectiveCaseModel(id='legacy-fixture',concept_id='film',perspective_id='legacy-fixture',perspective_title='레거시 사례',perspective_badge='',context_narrative='보호된 99887 조건',caution='',specifications=[]))
        db.add(EvidenceSourceModel(id='fixture-body',source_name='등록 삼성 자료',source_type='source_document',publisher='Samsung',quote=ns['definition'],external_url='',url_label='원문',credibility_tier='등록 원문·발췌',referenced_concepts=[dict(conceptId='film',bodyFields={'purpose':'기존 목적'}),dict(conceptId='unrelated',bodyFields={'summary':'다른 개념 설명'})]))
        db.add(EvidenceSourceModel(id='fixture-private',source_name='보호 출처',source_type='source_document',publisher='',quote='PRIVATE-SOURCE-9981',external_url='',url_label='',credibility_tier='대외비',referenced_concepts=[dict(conceptId='film')]))
        await db.commit()
    app=FastAPI()
    for router in (review_tickets.router,concepts.router,evidences.router):app.include_router(router,prefix='/api/v1')
    actor=SimpleNamespace(id='fixture',username='fixture',name='격리 검토자',department='검증',role='reviewer',level=3,is_active=True)
    async def auth(request:Request):
        level=int(request.headers.get('X-Fixture-Level','3'))
        return SimpleNamespace(**{**vars(actor),'level':level}) if level else None
    async def db():
        async with factory() as session:yield session
    app.dependency_overrides.update({get_db:db,get_current_user_optional:auth})
    @app.get('/')
    async def index():return HTMLResponse('<!doctype html><html lang="ko"><meta charset="utf-8"><link rel="stylesheet" href="/app.css"><div id="root"></div><script src="/app.js"></script></html>')
    @app.get('/app.js')
    async def js():return FileResponse(ROOT/'app.js',media_type='text/javascript')
    @app.get('/app.css')
    async def css():return FileResponse(ROOT/'app.css',media_type='text/css')
    return app,engine,factory,ns

async def checks():
    app,engine,factory,ns=await fixture()
    trace=[]
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://isolated') as client:
        async def call(method,path,body=None,expected=200,level=3):
            response=await client.request(method,'/api/v1/review-tickets/fixture-review'+path,json=body,headers={'X-Fixture-Level':str(level)})
            trace.append(dict(method=method,path=path,status=response.status_code))
            assert response.status_code==expected,response.text
            return response.json()
        detail=await call('GET','');draft=detail['workingDraft']['content'];version=1
        public_case=await client.put('/api/v1/review-tickets/fixture-other/human-edits',headers={'X-Fixture-Level':'2'},json={'ticketVersion':1,'changes':{'perspectiveCases':{'upsert':[dict(editorId='public-no-spec',perspectiveTitle='공개 설명 사례',narrative='공개 설명',caution='')]}}})
        assert public_case.status_code==200,public_case.text
        public_row=next(c for c in public_case.json()['workingDraft']['content']['perspectiveCases'] if c['editorId']=='public-no-spec')
        assert public_row['isMasked'] is False
        for v,changes in [(2,{'upsert':[dict(editorId='public-no-spec',narrative='공개 설명 수정')]}),(3,{'remove':['public-no-spec']})]:
            r=await client.put('/api/v1/review-tickets/fixture-other/human-edits',headers={'X-Fixture-Level':'2'},json={'ticketVersion':v,'changes':{'perspectiveCases':changes}})
            assert r.status_code==200,r.text
        assert detail['editingMode']=='legacy' and draft['partOf'][0]['id']=='unregistered-legacy'
        assert (await call('GET','',expected=401,level=0))
        for change in ({'perspectiveCases':{'remove':[draft['perspectiveCases'][0]['editorId']]}},
                       {'perspectiveCases':{'upsert':[{'editorId':draft['perspectiveCases'][1]['editorId'],'narrative':'overwrite hidden'}]}}):
            await call('PUT','/human-edits',{'ticketVersion':version,'changes':change},403,2)
        masked=await call('GET','',level=2)
        assert 'SECRET-12345' not in json.dumps(masked) and '99887' not in json.dumps(masked)
        await call('PUT','/human-edits',{'ticketVersion':version,'changes':{'evidences':{'remove':['fixture-private']}}},403,2)
        # Full manual edit, retaining the legacy unresolved relation and unrelated body source.
        body={'ticketVersion':version,'changes':{'purpose':'기존 목적','principles':{'upsert':[{'editorId':draft['principles'][0]['editorId'],'title':'직접 수정한 원리','content':ns['principle']}]},
            'limitations':{'upsert':[dict(editorId='limit-new',title='균일도',description=ns['limitation'])]},
            'perspectiveCases':{'upsert':[dict(editorId='case-new',perspectiveTitle='플라즈마 CVD 적용',perspectiveBadge='저온 조건',narrative=ns['situation'],caution='',specifications={'upsert':[dict(editorId='param-new',parameter='운영 조건',value='저온 형성',unit=None,isConfidential=False)]}),dict(editorId='case-no-spec',perspectiveTitle='공개 원문 조건',narrative=ns['situation'],caution='')]},
            'nextSteps':{'upsert':[dict(editorId='relation-new',id='etch',name='식각공정',reason='원문 순서')]} }}
        saved=await call('PUT','/human-edits',body);version=saved['ticketVersion'];assert version==2
        masked_preview=await call('POST','/wiki-preview',{'ticketVersion':version},level=2)
        assert 'PRIVATE-SOURCE-9981' not in json.dumps(masked_preview)
        async with factory() as db:
            public=await db.get(ConceptModel,'film');assert public.limitations==[] and public.principles[0]['title']=='기준 원리'
            ticket=await db.get(ReviewTicketModel,'fixture-review');snap=review_service.working(ticket)
            assert next(e for e in snap['evidences'] if e['id']=='fixture-body')['referenced_concepts'][0]['bodyFields']=={'purpose':'기존 목적'}
        await call('PUT','/human-edits',body,409)
        await call('PUT','/human-edits',{'editedContent':'old client','ticketVersion':version},409)
        # Delete the principle, verify simple rendering does not replay it, then ask AI to add it again.
        detail=await call('GET','');key=detail['workingDraft']['content']['principles'][0]['editorId']
        saved=await call('PUT','/human-edits',{'ticketVersion':version,'changes':{'principles':{'remove':[key]}}});version=saved['ticketVersion']
        preview=await call('POST','/wiki-preview',{'ticketVersion':version});assert not preview['previewConcept']['principles']
        before=copy.deepcopy(saved['workingDraft'])
        for mode in ('fail','invalid','semantic_fail','relation_fail','case_fail'):
            ns['behavior']=mode
            await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'등록 자료로 원리 보강'},502)
            assert (await call('GET',''))['workingDraft']==before
        ns['behavior']='normal'
        # Empty is a valid manually saved value and must survive a different-section directive.
        cleared=await call('PUT','/human-edits',{'ticketVersion':version,'changes':{'summary':''}});version=cleared['ticketVersion']
        result=await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'자료로 원리 보강','targetSections':['principles']});version=result['ticketVersion']
        assert (await call('GET',''))['workingDraft']['content']['summary']==''
        saved=await call('PUT','/human-edits',{'ticketVersion':version,'changes':{'summary':'저장 전 직접 편집한 박막 정의','principles':{'remove':[(await call('GET',''))['workingDraft']['content']['principles'][0]['editorId']]}}});version=saved['ticketVersion']
        result=await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'자료에 있는 원리를 보강해줘','targetSections':['principles']});version=result['ticketVersion']
        detail=await call('GET','');content=detail['workingDraft']['content'];assert content['principles'] and content['limitations'][0]['title']=='균일도'
        original_gateway=llm_gateway.generate_text
        async def replace_gateway(**kwargs):
            raw=await original_gateway(**kwargs)
            try:request=json.loads(kwargs['prompt'])
            except json.JSONDecodeError:return raw
            if request.get('currentDraft'):
                proposal=json.loads(raw);item=proposal['contributions'][0];item['content']['principles'][0]['title']='지시문으로 수정한 원리'
                return json.dumps(dict(contributions=[],replacements=[dict(sourceId=item['sourceId'],field='principles',editorId=content['principles'][0]['editorId'],content=item['content'])]),ensure_ascii=False)
            return raw
        llm_gateway.generate_text=replace_gateway
        updated=await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'현재 원리 설명을 등록 자료로 수정해줘','targetSections':['principles']});version=updated['ticketVersion']
        assert (await call('GET',''))['workingDraft']['content']['principles'][0]['title']=='지시문으로 수정한 원리'
        llm_gateway.generate_text=original_gateway
        assert all('SECRET-12345' not in c['prompt'] and '99887' not in c['prompt'] for c in ns['model_calls'])
        assert all('previousWorking' not in e and 'previousPatches' not in e for e in detail['directiveHistory'])
        assert not any(p['path']=='/workingDraft' for p in detail['structuredPatches'])
        # Undo the replacement, then undo its preceding add to recover the saved deletion.
        result=await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'되돌리기','undoLast':True});version=result['ticketVersion']
        result=await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'되돌리기','undoLast':True});version=result['ticketVersion']
        assert not (await call('GET',''))['workingDraft']['content']['principles']
        result=await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'자료로 원리 보강'});version=result['ticketVersion']
        saved=await call('PUT','/human-edits',{'ticketVersion':version,'changes':{'summary':'직접 정리한 박막 개요'}});version=saved['ticketVersion']
        await call('POST','/directive',{'ticketVersion':version,'structuredDraft':True,'directiveText':'되돌리기','undoLast':True},409)
        # New source and field reference can be saved together; public original is never changed.
        saved=await call('PUT','/human-edits',{'ticketVersion':version,'changes':{'evidences':{'upsert':[dict(editorId='new-source',sourceName='삼성 원문 발췌',publisher='Samsung',quote=ns['definition'],externalUrl='')]},'limitations':{'upsert':[dict(editorId='limit-new',evidenceIds=['draft:new-source'])]}}});version=saved['ticketVersion']
        content=saved['workingDraft']['content'];evidence=next(e for e in content['evidences'] if e['editorId']=='new-source')
        assert content['limitations'][0]['evidenceIds']==[evidence['id']]
        await call('PUT','/human-edits',{'ticketVersion':version,'changes':{'evidences':{'remove':['new-source']}}},422)
        preview=await call('POST','/wiki-preview',{'ticketVersion':version,'targetVersion':'v1.0.1'})
        await call('POST','/approve',{'ticketVersion':version},409)
        await call('POST','/approve',{'ticketVersion':version,'previewSignature':'stale','targetVersion':'v1.0.1'},409)
        approved=await call('POST','/approve',{'ticketVersion':version,'previewSignature':preview['previewSignature'],'targetVersion':'v1.0.1'})
        assert approved['ticket']['status']=='approved'
        wiki=(await client.get('/api/v1/concepts/film')).json();proposed=preview['previewConcept']
        assert wiki['summary']==proposed['summary'] and wiki['purpose']==proposed['purpose']
        def strip(rows):return [{k:v for k,v in r.items() if k!='editorId'} for r in rows]
        assert wiki['principles']==strip(proposed['principles']) and wiki['limitations']==strip(proposed['limitations'])
        assert len(wiki['perspectives'])==len(proposed['perspectives'])
        public_wiki=(await client.get('/api/v1/concepts/film',headers={'X-Fixture-Level':'2'})).json()
        assert next(c for c in public_wiki['perspectives'] if c['perspectiveTitle']=='공개 원문 조건')['isMasked'] is False
        async with factory() as db:
            ev=await db.get(EvidenceSourceModel,'fixture-body');assert any(r['conceptId']=='unrelated' for r in ev.referenced_concepts)
            assert next(r for r in ev.referenced_concepts if r['conceptId']=='film')['bodyFields']=={'purpose':'기존 목적'}
            assert (await db.get(PerspectiveCaseModel,'secret-fixture')).specifications[0]['value']=='SECRET-12345'
            assert any(e.target_concept_id=='etch' for e in (await db.execute(select(CausalEdgeModel))).scalars())
        await call('PUT','/human-edits',{'ticketVersion':approved['ticket']['ticketVersion'],'changes':{'summary':'after approval'}},409)
        # Guarded edits of an existing edge update graph reason, preserving unrelated evidence refs.
        async with factory() as db:
            db.add(EvidenceSourceModel(id='E-01',source_name='공인 인용',source_type='source_document',publisher='Samsung',quote=ns['definition'],external_url='',url_label='',credibility_tier='등록 원문',referenced_concepts=[dict(conceptId='film')]))
            db.add(ReviewTicketModel(id='citation-edit',concept_id='film',concept_title='박막 공정',title='citation-edit',review_type='파라미터 수정',author='격리',current_content=wiki['summary']+' [E-01]',ai_merged_draft=wiki['summary']+' [E-01]',status='pending',ticket_version=1,structured_patches=[],directive_history=[],integrity_report={}))
            for key in ('edge-edit','race-save','race-a','race-b'):
                db.add(ReviewTicketModel(id=key,concept_id='film',concept_title='박막 공정',title=key,review_type='파라미터 수정',author='격리',current_content=wiki['summary'],ai_merged_draft=wiki['summary'],status='pending',ticket_version=1,structured_patches=[],directive_history=[],integrity_report={}))
            await db.commit()
        async def specific(key,method,path,body=None):return await client.request(method,'/api/v1/review-tickets/'+key+path,json=body)
        removal={'ticketVersion':1,'changes':{'summary':wiki['summary'],'evidences':{'remove':['E-01']}}}
        r=await specific('citation-edit','PUT','/human-edits',removal);assert r.status_code==422,r.text
        r=await specific('citation-edit','PUT','/human-edits',{**removal,'allowCitationDeletion':True,'deprecatedCitations':['E-01'],'overrideReason':'공인 출처 인용 폐기'});assert r.status_code==200,r.text
        d=(await specific('edge-edit','GET','')).json();link=d['workingDraft']['content']['nextSteps'][0]
        r=await specific('edge-edit','PUT','/human-edits',{'ticketVersion':1,'changes':{'nextSteps':{'upsert':[dict(editorId=link['editorId'],reason='직접 정리한 공정 순서')]}}});assert r.status_code==200,r.text
        p=(await specific('edge-edit','POST','/wiki-preview',{'ticketVersion':2,'targetVersion':'v1.0.2'})).json()
        r=await specific('edge-edit','POST','/approve',{'ticketVersion':2,'previewSignature':p['previewSignature'],'targetVersion':'v1.0.2'});assert r.status_code==200,r.text
        async with factory() as db:assert any(e.mechanism_label=='직접 정리한 공정 순서' for e in (await db.execute(select(CausalEdgeModel))).scalars())
        requests=[specific('race-save','PUT','/human-edits',{'ticketVersion':1,'changes':{'summary':s}}) for s in ('동시 저장 A','동시 저장 B')]
        assert sorted(r.status_code for r in await asyncio.gather(*requests))==[200,409]
        previews=[]
        for key in ('race-a','race-b'):
            r=await specific(key,'PUT','/human-edits',{'ticketVersion':1,'changes':{'purpose':key}});assert r.status_code==200,r.text
            p=await specific(key,'POST','/wiki-preview',{'ticketVersion':2,'targetVersion':'v1.0.3'});assert p.status_code==200,p.text;previews.append(p.json())
        results=await asyncio.gather(*[specific(key,'POST','/approve',{'ticketVersion':2,'previewSignature':p['previewSignature'],'targetVersion':'v1.0.3'}) for key,p in zip(('race-a','race-b'),previews)])
        assert sorted(r.status_code for r in results)==[200,409],[(r.status_code,r.text) for r in results]
    await engine.dispose()
    (ROOT/'http-results.json').write_text(json.dumps(dict(passed=True,trace=trace),indent=2),encoding='utf-8')
    print('PASS whole draft edit/save/reopen/delete/re-add/undo/preview/approve/wiki; source ownership and L3; configured DB forbidden')

async def serve():
    import uvicorn
    app,engine,factory,ns=await fixture()
    sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen(128);sock.setblocking(False)
    port=sock.getsockname()[1]
    (ROOT/'server.json').write_text(json.dumps(dict(port=port)),encoding='utf-8')
    print('ISOLATED_PORT='+str(port),flush=True)
    try:await uvicorn.Server(uvicorn.Config(app,log_level='warning',access_log=False,lifespan='off')).serve(sockets=[sock])
    finally:await engine.dispose()

if __name__=='__main__':asyncio.run(serve() if '--serve' in sys.argv else checks())
