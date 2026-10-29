"""Real HTTP/DB/worker requested drafts, with explicitly labelled fixture generation."""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from conftest import cli
from test_document_pipeline import documents_app, upload
from test_wiki_discovery import api, create, edit


def submit(app, page=None, mode=None, user='alice', **extra):
    body={'requestId':uuid4().hex,'mode':mode or ('edit' if page else 'create'),
          'instruction':'적용 조건을 보강해 주세요.', 'contextText':'고객 테스트에서는 저부하에서 사용했습니다.', **extra}
    if page: body['pageId']=page['id']
    r=api(app,'POST','/proposals',user=user,json=body)
    assert r.status_code == 202, r.text
    return r.json()['id'],body


def complete(app, identity):
    for _ in range(30):
        p=api(app,'GET','/proposals/'+identity).json()
        if p.get('status') not in ('pending','running'):
            assert p['status'] == 'ready', p
            return p
        result=json.loads(cli(app.environment,'worker','--once').stdout)
        assert result['status'] not in ('failed',), result
    pytest.fail('Proposal did not complete')


def application_body(p):
    r=p['result']
    return {'requestId':uuid4().hex, 'title':r['title'], 'markdown':r['markdown'],
        'sourceNote':r.get('sourceNote',''), 'changeSummary':'검토 후 반영',
        'aliases':r.get('aliases',[]),'meaning':r.get('meaning','')}


def test_draft_is_private_and_not_knowledge_until_atomic_human_apply(documents_app):
    app=documents_app
    pid,body=submit(app,contextText='UNPUBLISHED_NYX727 고객의 조건부 경험입니다.')
    replay=api(app,'POST','/proposals',json=body); assert replay.json()['id']==pid
    conflict=api(app,'POST','/proposals',json={**body,'instruction':'다른 요청'})
    assert conflict.status_code==409
    assert api(app,'GET','/proposals/'+pid,user='bob').status_code==404
    assert api(app,'GET','/proposals/'+pid,user='operator').status_code==404
    p=complete(app,pid)
    assert 'UNPUBLISHED_NYX727' in p['result']['markdown']
    assert api(app,'GET','/pages').json()['total']==0
    found=api(app,'POST','/search',json={'query':'UNPUBLISHED_NYX727'}).json()
    assert found['items']==[]
    assert app.database.query('SELECT count(*) n FROM wiki_passages')[0]['n']==0
    # Read-only refresh never enqueues another job or generation.
    for _ in range(3): assert api(app,'GET','/proposals/'+pid).status_code==200
    assert app.database.query('SELECT count(*) n FROM wiki_proposals')[0]['n']==1
    before=p['result']['markdown']; cmd=application_body(p)
    cmd['markdown']=before+'\n직원이 직접 확인한 추가 내용.'
    r=api(app,'POST',f'/proposals/{pid}/apply',json=cmd)
    assert r.status_code==200,r.text
    replay=api(app,'POST',f'/proposals/{pid}/apply',json=cmd)
    assert replay.json()['replayed']
    detail=api(app,'GET','/proposals/'+pid).json()
    assert detail['appliedResult']['pageId']==r.json()['pageId']
    assert detail['appliedResult']['revisionId']==r.json()['revisionId']
    assert 'page_id' not in detail['appliedResult']
    page=api(app,'GET','/pages/'+r.json()['pageId']).json()
    assert page['revision']['markdown']==cmd['markdown'] and page['revision']['aiAssisted']
    assert app.database.query('SELECT count(*) n FROM wiki_revisions')[0]['n']==1
    assert 'conversationId' not in json.dumps(page['revision']['provenance'])
    exported=api(app,'GET',f"/pages/{page['id']}/markdown")
    assert exported.text==cmd['markdown']
    cli(app.environment,'worker','--once')
    found=api(app,'POST','/search',json={'query':'UNPUBLISHED_NYX727'}).json()
    assert found['items'][0]['page']['id']==page['id']


def test_stale_edit_and_protection_checked_again_and_admin_can_apply(documents_app):
    app=documents_app; page=create(app,'RUL','# RUL\n\n기존 설명입니다.')
    pid,_=submit(app,page); p=complete(app,pid); cmd=application_body(p)
    newer=edit(app,page,markdown=page['revision']['markdown']+'\n동료가 먼저 추가함')
    r=api(app,'POST',f'/proposals/{pid}/apply',json=cmd)
    assert r.status_code==409 and r.json()['error']['code']=='wiki_version_conflict'
    assert api(app,'GET','/proposals/'+pid).json()['result']['markdown']==p['result']['markdown']
    # Employee can ask for protected content, admin alone can publish it.
    locked=api(app,'PATCH',f"/pages/{page['id']}/protection",user='operator',json={
        'requestId':uuid4().hex,'baseVersion':newer['version'],'locked':True})
    assert locked.status_code==200
    page=api(app,'GET','/pages/'+page['id']).json()
    pid,_=submit(app,page); p=complete(app,pid); cmd=application_body(p)
    assert not p['canApply']
    assert api(app,'POST',f'/proposals/{pid}/apply',json=cmd).status_code==403
    assert api(app,'GET','/proposals/'+pid,user='operator').json()['canApply']
    assert api(app,'POST',f'/proposals/{pid}/apply',user='operator',json=cmd).status_code==200
    current=api(app,'GET','/pages/'+page['id']).json()
    assert current['locked'] and current['revision']['editor']['username']=='operator'


def test_concurrent_apply_same_proposal_does_not_duplicate_and_failed_commit_is_not_success(documents_app):
    app=documents_app; page=create(app,'Concurrent','# Existing\n\nKeep this sentence.')
    pid,_=submit(app,page); p=complete(app,pid); cmd=application_body(p)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:api(app,'POST',f'/proposals/{pid}/apply',json=cmd),range(2)))
    assert all(r.status_code==200 for r in responses)
    assert len({r.json()['revisionId'] for r in responses})==1
    assert app.database.query('SELECT count(*) n FROM wiki_revisions WHERE page_id=$1',page['id'])[0]['n']==2
    pid,_=submit(app); p=complete(app,pid); cmd=application_body(p)
    app.database.execute("""CREATE FUNCTION reject_proposal_test() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'test failure'; END $$;
        CREATE TRIGGER reject_proposal_write BEFORE INSERT ON wiki_revisions FOR EACH ROW EXECUTE FUNCTION reject_proposal_test();""")
    try:
        r=api(app,'POST',f'/proposals/{pid}/apply',json=cmd)
        assert r.status_code==503,r.text
        assert api(app,'GET','/proposals/'+pid).json()['status']=='ready'
        assert app.database.query('SELECT count(*) n FROM wiki_pages')[0]['n']==1
    finally: app.database.execute('DROP TRIGGER reject_proposal_write ON wiki_revisions; DROP FUNCTION reject_proposal_test();')
    assert api(app,'POST',f'/proposals/{pid}/apply',json=cmd).status_code==200


def test_selected_chat_excerpt_checks_ownership_and_never_copies_other_text(documents_app):
    app=documents_app
    c=app.server.request('POST','/conversations',token=app.tokens['alice'],json={'title':'private'}).json()['id']
    msg=app.server.request('POST',f'/conversations/{c}/messages',token=app.tokens['alice'],json={
        'content':'DO_NOT_COPY_PRIVATE_991\n선택할 고객 경험 문장입니다.\nDO_NOT_COPY_OTHER_883'})
    assert msg.status_code in (200,201),msg.text
    m=app.server.request('GET',f'/conversations/{c}',token=app.tokens['alice']).json()['messages'][0]['id']
    selection={'conversationId':c,'messageId':m,'text':'선택할 고객 경험 문장입니다.'}
    body={'requestId':uuid4().hex,'mode':'create','instruction':'선택한 경험으로 초안','selection':selection}
    assert api(app,'POST','/proposals',user='bob',json=body).status_code==404
    assert api(app,'POST','/proposals',json={**body,'selection':{**selection,'text':'조작된 다른 문장'}}).status_code==422
    result=api(app,'POST','/proposals',json=body); assert result.status_code==202,result.text
    p=complete(app,result.json()['id'])
    saved=json.dumps(app.database.query('SELECT input, result FROM wiki_proposals'),ensure_ascii=False)
    assert 'DO_NOT_COPY' not in saved and c not in saved and m not in saved
    cmd=application_body(p); r=api(app,'POST',f"/proposals/{p['id']}/apply",json=cmd)
    assert r.status_code==200,r.text
    revision=api(app,'GET','/pages/'+r.json()['pageId']).json()['revision']
    assert 'DO_NOT_COPY' not in revision['markdown']
    assert revision['provenance']['inputKind']=='chat_selection'


def test_dismiss_failed_generation_and_source_withdrawal_do_not_publish(documents_app):
    app=documents_app
    pid,_=submit(app)
    assert api(app,'POST',f'/proposals/{pid}/dismiss').json()['status']=='dismissed'
    assert api(app,'POST',f'/proposals/{pid}/apply',json={'requestId':uuid4().hex,'title':'x','markdown':'y'}).status_code==409
    pid,_=submit(app)
    blocked={**app.environment,'OW_PROVIDER_MODE':'disabled'}
    r=json.loads(cli(blocked,'worker','--once').stdout)
    assert r['status']=='failed'
    p=api(app,'GET','/proposals/'+pid).json()
    assert p['status']=='failed' and p['error']['code']=='configuration_blocked'
    assert api(app,'GET','/pages').json()['total']==0
    page=create(app,'withdrawn draft target')
    pid,_=submit(app,page); complete(app,pid)
    assert api(app,'POST',f"/pages/{page['id']}/deactivate",user='operator',json={'requestId':uuid4().hex,'baseVersion':page['version']}).status_code==200
    assert api(app,'GET','/proposals/'+pid).status_code in (404,409)


def test_real_candidate_context_with_injected_link_verifier_and_unknown_source_rejection(documents_app):
    from knowledge.core.config import Settings
    from knowledge.jobs.worker import run_worker
    from knowledge.integrations.providers import ProviderDelta
    app=documents_app
    target=create(app,'예지보전','예지보전은 설비 상태에 근거해 정비를 계획하는 개념입니다.')
    page=create(app,'RUL 설명','RUL은 예지보전 분야에서 활용됩니다.\n\n기존 업무 경험을 보존합니다.')
    pid,_=submit(app,page,mode='links',instruction='예지보전에 중요한 링크만 검토해 주세요.')
    seen=[]
    class Verifier:
        model='test-injected-link-review-not-live'
        async def stream(self,messages,**kwargs):
            data=json.loads(messages[1]['content'].split('\n',1)[1]);seen.append(data)
            assert any(c['pageId']==target['id'] for c in data['linkCandidates'])
            yield ProviderDelta(text=json.dumps({'title':'','markdown':'','patches':[],
                'reason':'주입형 검증 결과입니다. 실제 의미 판정 품질을 보장하지 않습니다.',
                'links':[{'anchor':'예지보전','pageId':target['id'],'sameConcept':True,'important':True,'reason':'본문의 분야 개념'}],
                'evidenceIds':[]}),model=self.model)
    settings=Settings(database_url=app.database.url,provider_mode='fixture')
    for _ in range(8):
        r=asyncio.run(run_worker(once=True,settings=settings,generation_client=Verifier()))
        if r['status']=='ready':break
    p=api(app,'GET','/proposals/'+pid).json()
    assert p['status']=='ready',p
    assert p['result']['markdown']==page['revision']['markdown'].replace('예지보전',f"[예지보전](/wiki/{target['id']})")
    assert len(seen)==1
    # Revoked input cannot be published even after the generation has succeeded.
    r=api(app,'POST',f"/pages/{target['id']}/deactivate",user='operator',json={'requestId':uuid4().hex,'baseVersion':target['version']})
    assert r.status_code==200
    assert api(app,'POST',f'/proposals/{pid}/apply',json=application_body(p)).status_code==409
    assert api(app,'GET','/proposals/'+pid).status_code==409


def test_interrupted_draft_is_failed_not_automatically_regenerated(documents_app):
    app=documents_app; pid,_=submit(app)
    app.database.execute("UPDATE wiki_proposals SET status='running' WHERE id=$1",pid)
    result=json.loads(cli(app.environment,'worker','--once').stdout)
    assert result['status']=='idle'
    p=api(app,'GET','/proposals/'+pid).json()
    assert p['status']=='failed' and p['error']['code']=='worker_interrupted'
    assert api(app,'GET','/pages').json()['total']==0
