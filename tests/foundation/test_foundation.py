import json
import os
import secrets
import subprocess
import sys
import pytest
from conftest import ROOT, cli

CORE_TABLES = {'knowledge_users','conversations','messages'}
DOCUMENT_TABLES = {'documents','document_revisions','passages','embedding_records','passage_embeddings','processing_jobs'}
ANSWER_TABLES = {'answer_runs','answer_event_batches','retrieval_runs'}


def new_conversation(application,name='alice'):
    response = application.server.request('POST','/conversations',token=application.tokens[name],json={'title':'사내 문헌 질문'})
    assert response.status_code == 201,response.text
    return response.json()['id']


def test_real_login_schema_and_health(application):
    response = application.server.request('GET','/health')
    assert response.status_code == 200
    assert set(response.json()['capabilities']) == {'authentication','private_conversations','message_storage','shared_document_upload','automatic_indexing','grounded_answers','durable_answer_events','shared_wiki'}
    tables = {r['tablename'] for r in application.database.query("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
    assert tables == CORE_TABLES | DOCUMENT_TABLES | ANSWER_TABLES | {'wiki_pages','wiki_revisions','wiki_mutations','knowledge_schema_migrations'}
    columns = {r['column_name'] for r in application.database.query("SELECT column_name FROM information_schema.columns WHERE table_schema='public'")}
    assert not columns.intersection({'auto_wiki','response_mode','extended','next_settings','review_status'})
    me = application.server.request('GET','/auth/me',token=application.tokens['alice'])
    assert me.status_code == 200 and me.json()['username'] == 'alice'
    assert not any('wiki' in p or 'research' in p for p in me.json()['permissions'])
    assert me.headers['cache-control'] == 'no-store'


def test_round_trip_and_real_server_restart(application):
    server,token = application.server,application.tokens['alice']
    conversation = new_conversation(application)
    message = server.request('POST',f'/conversations/{conversation}/messages',token=token,json={'content':'기록 보존을 확인하는 질문입니다.'})
    assert message.status_code == 201 and message.json()['role'] == 'user'
    changed = server.request('PATCH',f'/conversations/{conversation}',token=token,json={'title':'저장 후 재시작'})
    assert changed.status_code == 200
    before = server.request('GET',f'/conversations/{conversation}',token=token).json()
    old_pid = server.process.pid
    server.restart()
    assert server.process.pid != old_pid
    after = server.request('GET',f'/conversations/{conversation}',token=token)
    assert after.status_code == 200 and after.json() == before
    assert after.json()['messages'][0]['id'] == message.json()['id']
    assert len(after.json()['messages']) == 1
    assert after.json()['title'] == '저장 후 재시작'
    assert application.database.query('SELECT content FROM messages WHERE conversation_id=$1',conversation) == [{'content':'기록 보존을 확인하는 질문입니다.'}]


@pytest.mark.parametrize('intruder',['bob','operator'])
def test_other_employee_and_admin_cannot_access_private_conversation(application,intruder):
    conversation = new_conversation(application)
    server,token = application.server,application.tokens[intruder]
    listed = server.request('GET','/conversations',token=token)
    assert listed.status_code == 200
    assert conversation not in {item['id'] for item in listed.json()['items']}
    for method,path,values in (
        ('GET',f'/conversations/{conversation}',{}),
        ('PATCH',f'/conversations/{conversation}',{'json':{'title':'변경 시도'}}),
        ('POST',f'/conversations/{conversation}/messages',{'json':{'content':'접근 시도'}})):
        assert server.request(method,path,token=token,**values).status_code == 404
    owned = server.request('GET',f'/conversations/{conversation}',token=application.tokens['alice'])
    assert owned.json()['title'] == '사내 문헌 질문' and owned.json()['messages'] == []


@pytest.mark.parametrize('path',['/auth/me','/conversations','/conversations/unknown','/documents','/answer-runs/unknown'])
def test_authentication_required(application,path):
    assert application.server.request('GET',path).status_code == 401
    assert application.server.request('GET',path,token='not-a-token').status_code == 401


def test_wrong_password_and_no_default_account(application):
    for name in ('alice','admin','nonexistent'):
        assert application.server.request('POST','/auth/login',json={'username':name,'password':'wrong-password'}).status_code == 401
    assert application.database.query('SELECT username FROM knowledge_users ORDER BY username') == [{'username':'alice'},{'username':'bob'},{'username':'operator'}]


@pytest.mark.parametrize('body',[{'title':' '},{'title':'a'*301},{'title':'x','autoWiki':True},{'title':'x','ownerId':'another-user'},{'title':'\x00'}])
def test_conversation_contract_rejects_legacy_and_invalid_fields(application,body):
    assert application.server.request('POST','/conversations',token=application.tokens['alice'],json=body).status_code == 422


@pytest.mark.parametrize('body',[{'content':' '},{'content':'a'*30001},{'content':'\x00'}, {'content':'x','role':'assistant'},{'content':'x','extended':True}])
def test_message_contract_does_not_allow_spoofed_or_legacy_data(application,body):
    conversation = new_conversation(application)
    assert application.server.request('POST',f'/conversations/{conversation}/messages',token=application.tokens['alice'],json=body).status_code == 422


def test_blank_patch_rejected_and_default_title_works(application):
    server,token = application.server,application.tokens['alice']
    response = server.request('POST','/conversations',token=token,json={})
    assert response.status_code == 201 and response.json()['title'] == '새 대화'
    for body in ({},{'title':None},{'title':' '},{'autoWiki':False}):
        assert server.request('PATCH','/conversations/'+response.json()['id'],token=token,json=body).status_code == 422


def test_migration_is_idempotent_and_target_is_explicit(application):
    before = application.database.query('SELECT id FROM conversations ORDER BY id')
    assert json.loads(cli(application.environment,'migrate','--database-name',application.database.name).stdout)['applied'] == []
    mismatch = cli(application.environment,'migrate','--database-name','wrong_database_test',expect=1)
    assert 'must equal' in mismatch.stderr
    assert application.database.query('SELECT id FROM conversations ORDER BY id') == before
    assert 'already exists' in cli(application.environment,'create-user','--username','alice',expect=1).stderr


def test_legacy_database_is_rejected_without_mutation(database_factory):
    with database_factory() as database:
        database.execute("CREATE TABLE old_data (value text); INSERT INTO old_data VALUES ('keep-me')")
        environment = {**os.environ,'PYTHONPATH':str(ROOT/'backend'),'OW_DATABASE_URL':database.url}
        assert 'not empty' in cli(environment,'migrate','--database-name',database.name,expect=1).stderr
        assert database.query('SELECT value FROM old_data') == [{'value':'keep-me'}]
        assert database.query("SELECT tablename FROM pg_tables WHERE schemaname='public'") == [{'tablename':'old_data'}]


def test_missing_schema_refuses_startup_without_seed_or_migration(database_factory):
    with database_factory() as database:
        environment = {**os.environ,'PYTHONPATH':str(ROOT/'backend'),'OW_DATABASE_URL':database.url,
                       'OW_AUTH_SECRET':secrets.token_hex(32),'OW_PROVIDER_MODE':'disabled'}
        result = subprocess.run([sys.executable,'-m','uvicorn','knowledge.main:app','--port','0'],cwd=ROOT,
                                env=environment,capture_output=True,text=True,timeout=30)
        assert result.returncode != 0 and 'Foundation schema missing' in result.stderr
        assert database.query("SELECT tablename FROM pg_tables WHERE schemaname='public'") == []


def test_revoked_identity_is_rechecked(application):
    database,token = application.database,application.tokens['bob']
    try:
        database.execute("UPDATE knowledge_users SET is_active=false WHERE username='bob'")
        assert application.server.request('GET','/auth/me',token=token).status_code == 401
        assert application.server.request('GET','/conversations',token=token).status_code == 401
        assert application.server.request('GET','/documents',token=token).status_code == 401
    finally:
        database.execute("UPDATE knowledge_users SET is_active=true WHERE username='bob'")


@pytest.mark.parametrize('path',['/research/search','/personal-wiki/organize','/retrieval/search','/index-jobs'])
def test_removed_endpoints_do_not_succeed(application,path):
    assert application.server.request('POST',path,token=application.tokens['alice'],json={}).status_code == 404


def test_runtime_does_not_import_removed_features_or_document_worker(application):
    program = '''import sys
from knowledge.main import app
from knowledge.registry import load_entities
from knowledge.core.database import Base
load_entities()
assert set(Base.metadata.tables) == {'knowledge_users','conversations','messages','documents','document_revisions','passages','embedding_records','passage_embeddings','processing_jobs','retrieval_runs','answer_runs','answer_event_batches','wiki_pages','wiki_revisions','wiki_mutations'}
for prefix in ('knowledge.personal_wiki','knowledge.research','knowledge.ontology','knowledge.jobs.worker','knowledge.integrations.public_fetch'):
    assert not any(name == prefix or name.startswith(prefix+'.') for name in sys.modules), prefix
'''
    result = subprocess.run([sys.executable,'-c',program],cwd=ROOT,env=application.environment,capture_output=True,text=True,timeout=15)
    assert result.returncode == 0,result.stdout+result.stderr
    paths = application.server.client.get('/openapi.json').json()['paths']
    assert {'/api/v1/health','/api/v1/auth/login','/api/v1/auth/me','/api/v1/conversations',
            '/api/v1/conversations/{conversation_id}','/api/v1/conversations/{conversation_id}/messages',
            '/api/v1/conversations/{conversation_id}/turns','/api/v1/answer-runs/{run_id}/events','/api/v1/wiki/pages'} <= set(paths)
    assert all(not any(word in path for word in ('research','personal-wiki','retrieval')) for path in paths)
