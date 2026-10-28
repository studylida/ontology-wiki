"""Stage 2 uploads + real PostgreSQL/HTTP/SSE; provider output is explicitly fixture."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from test_document_pipeline import documents_app, upload, work, detail, action


def conversation(app, user='alice'):
    response = app.server.request('POST','/conversations',token=app.tokens[user],json={})
    assert response.status_code == 201,response.text
    return response.json()['id']


def question(app, conv, text='What are the alpha material experimental conditions?', request_id=None, user='alice'):
    body = {'question':text,'requestId':request_id or uuid4().hex}
    response = app.server.request('POST',f'/conversations/{conv}/turns',token=app.tokens[user],json=body)
    assert response.status_code == 202,response.text
    return response.json(),body


def wait(app, run, *, states=('completed','failed','cancelled','interrupted')):
    deadline = time.monotonic()+25
    while time.monotonic()<deadline:
        response = app.server.request('GET','/answer-runs/'+run,token=app.tokens['alice'])
        assert response.status_code == 200,response.text
        value = response.json()
        if value['status'] in states:
            return value
        time.sleep(.025)
    pytest.fail('Run did not reach expected state: '+repr(value))


def events(app, run, after=0, user='alice'):
    response = app.server.request('GET',f'/answer-runs/{run}/events?after={after}',token=app.tokens[user])
    assert response.status_code == 200,response.text
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]


def indexed(app):
    accepted = upload(app)
    assert work(app)['status'] == 'succeeded'
    return accepted


def test_uploaded_evidence_answer_citations_followup_and_restart(documents_app):
    app = documents_app
    source = indexed(app)
    app.server.environment['OW_RETRIEVAL_LIMIT'] = '1'
    app.server.restart()
    conv = conversation(app)
    run,body = question(app,conv)
    result = wait(app,run['runId'])
    assert result['status'] == 'completed',result
    assert result['retrieval']['status'] == 'found'
    evidence = result['retrieval']['evidence']
    assert source['revisionId'] in {h['sourceRevisionId'] for h in evidence}
    assert any('neighbor' in h['methods'] for h in evidence)
    assert result['usage']['generation']['promptEvidenceIds'] == [h['passageId'] for h in evidence]
    assert result['retrieval']['contextCharacters'] <= 24000
    assert result['answer']['citations']
    for citation in result['answer']['citations']:
        rows = app.database.query('SELECT source_revision_id,text FROM passages WHERE id=$1',citation['passageId'])
        assert rows[0]['source_revision_id'] == citation['sourceRevisionId']
        assert citation['excerpt'] == rows[0]['text']
        assert '[['+citation['passageId']+']]' in result['answer']['content']
    before = app.server.request('GET','/conversations/'+conv,token=app.tokens['alice']).json()
    assert [m['role'] for m in before['messages']] == ['user','assistant']
    app.server.restart()
    assert app.server.request('GET','/conversations/'+conv,token=app.tokens['alice']).json() == before
    follow,_ = question(app,conv,'What limitations apply to those conditions?')
    followed = wait(app,follow['runId'])
    assert followed['status'] == 'completed' and followed['usage']['generation']['historyMessages'] == 2
    assert body['question'] in followed['retrieval']['query']


def test_sse_disconnect_resume_and_duplicate_request_do_not_regenerate(documents_app):
    app = documents_app
    indexed(app)
    app.server.environment['OW_STREAM_FLUSH_CHARACTERS'] = '32'
    app.server.restart()
    conv = conversation(app)
    run,body = question(app,conv)
    first = []
    with app.server.client.stream('GET','/api/v1'+f"/answer-runs/{run['runId']}/events",
        headers={'Authorization':'Bearer '+app.tokens['alice']}) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith('data: '):
                event = json.loads(line[6:])
                first.append(event)
                if event['type'] == 'delta':
                    break
    result = wait(app,run['runId'])
    assert result['status'] == 'completed'
    tail = events(app,run['runId'],first[-1]['seq'])
    all_events = first+tail
    assert [e['seq'] for e in all_events] == list(range(1,result['durableSeq']+1))
    assert ''.join(e['data']['text'] for e in all_events if e['type']=='delta') == result['answer']['content']
    assert sum(e['type']=='complete' for e in all_events) == 1
    repeated = app.server.request('POST',f'/conversations/{conv}/turns',token=app.tokens['alice'],json=body)
    assert repeated.status_code == 202 and repeated.json()['runId'] == run['runId']
    restored = app.server.client.get('/api/v1'+f"/answer-runs/{run['runId']}/events",headers={
        'Authorization':'Bearer '+app.tokens['alice'],'Last-Event-ID':str(first[-1]['seq'])})
    assert [json.loads(line[6:]) for line in restored.text.splitlines() if line.startswith('data: ')] == tail
    assert app.database.query('SELECT count(*) n FROM answer_runs')[0]['n'] == 1
    assert result['usage']['generation']['fixtureCalls'] == 1
    assert app.server.request('GET',f"/answer-runs/{run['runId']}/events?after=999999",token=app.tokens['alice']).status_code == 409


def test_concurrent_same_request_and_conflicts(documents_app):
    app = documents_app
    indexed(app)
    conv = conversation(app)
    body = {'question':'alpha material conditions','requestId':uuid4().hex}
    def send():
        return app.server.request('POST',f'/conversations/{conv}/turns',token=app.tokens['alice'],json=body)
    with ThreadPoolExecutor(max_workers=3) as pool:
        responses = list(pool.map(lambda _:send(),range(3)))
    assert all(r.status_code==202 for r in responses),[r.text for r in responses]
    ids = {r.json()['runId'] for r in responses}
    assert len(ids)==1
    assert wait(app,next(iter(ids)))['status']=='completed'
    conflict = app.server.request('POST',f'/conversations/{conv}/turns',token=app.tokens['alice'],json={**body,'question':'different'})
    assert conflict.status_code==409
    assert app.database.query("SELECT count(*) n FROM messages WHERE role='user'")[0]['n']==1


def test_cancel_and_explicit_retry_reuse_question_but_new_run(documents_app):
    app = documents_app
    indexed(app)
    conv = conversation(app)
    run,_ = question(app,conv)
    wait(app,run['runId'],states=('generating',))
    busy = app.server.request('POST',f'/conversations/{conv}/turns',token=app.tokens['alice'],
                              json={'question':'another question','requestId':uuid4().hex})
    assert busy.status_code==409
    stopped = app.server.request('POST',f"/answer-runs/{run['runId']}/cancel",token=app.tokens['alice'])
    assert stopped.status_code==200 and stopped.json()['status']=='cancelled',stopped.text
    assert not any(e['type']=='complete' for e in events(app,run['runId']))
    request_id = uuid4().hex
    retried = app.server.request('POST',f"/answer-runs/{run['runId']}/retry",token=app.tokens['alice'],json={'requestId':request_id})
    assert retried.status_code==202,retried.text
    new = retried.json()
    assert new['runId']!=run['runId'] and new['userMessageId']==run['userMessageId']
    assert wait(app,new['runId'])['status']=='completed'
    duplicate = app.server.request('POST',f"/answer-runs/{run['runId']}/retry",token=app.tokens['alice'],json={'requestId':request_id})
    assert duplicate.json()['runId']==new['runId']
    assert app.database.query("SELECT count(*) n FROM messages WHERE role='user'")[0]['n']==1


def test_process_kill_restores_partial_without_new_generation(documents_app):
    app = documents_app
    indexed(app)
    app.server.environment['OW_STREAM_FLUSH_CHARACTERS']='32'
    app.server.restart()
    conv = conversation(app)
    run,_ = question(app,conv)
    wait(app,run['runId'],states=('generating',))
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        rows=app.database.query('SELECT content FROM messages WHERE id=$1',run['messageId'])
        if rows[0]['content']:
            break
        time.sleep(.01)
    assert rows[0]['content']
    app.server.process.kill()
    app.server.process.wait(timeout=10)
    saved=app.database.query('SELECT content FROM messages WHERE id=$1',run['messageId'])[0]['content']
    app.server.restart()
    result=wait(app,run['runId'])
    assert result['status']=='interrupted' and result['answer']['content']==saved
    replay=events(app,run['runId'])
    assert replay[-1]['type']=='interrupted' and not any(e['type']=='complete' for e in replay)
    assert app.database.query('SELECT count(*) n FROM answer_runs')[0]['n']==1


@pytest.mark.parametrize('intruder',['bob','operator'])
def test_private_run_and_replay_not_readable_by_other_employee(documents_app,intruder):
    app=documents_app
    conv=conversation(app)
    run,_=question(app,conv)
    wait(app,run['runId'])
    for method,path,extra in (
        ('GET',f"/answer-runs/{run['runId']}",{}),
        ('GET',f"/answer-runs/{run['runId']}/events",{}),
        ('POST',f"/answer-runs/{run['runId']}/cancel",{}),
        ('POST',f"/answer-runs/{run['runId']}/retry",{'json':{'requestId':uuid4().hex}})):
        assert app.server.request(method,path,token=app.tokens[intruder],**extra).status_code==404


def test_deactivated_evidence_is_redacted_in_detail_replay_and_history(documents_app):
    app=documents_app
    source=indexed(app)
    conv=conversation(app)
    run,_=question(app,conv)
    assert wait(app,run['runId'])['status']=='completed'
    action(app,source['documentId'],'deactivate',expect=200)
    result=wait(app,run['runId'])
    assert result['answer']['sourceUnavailable'] and not result['answer']['content']
    assert not result['answer']['citations'] and result['retrieval'] is None
    assert app.server.request('GET',f"/answer-runs/{run['runId']}/events",token=app.tokens['alice']).status_code==409
    stored=app.server.request('GET','/conversations/'+conv,token=app.tokens['alice']).json()
    assert stored['messages'][1]['sourceUnavailable'] and not stored['messages'][1]['content']
    follow,_=question(app,conv,'Explain the previous decision')
    followup=wait(app,follow['runId'])
    assert followup['status']=='completed' and followup['retrieval']['status']=='no_evidence'
    assert followup['usage']['generation']['historyMessages']==1
    assert followup['usage']['generation']['promptEvidenceIds']==[]


def test_no_evidence_is_distinct_from_real_database_retrieval_failure(documents_app):
    app=documents_app
    conv=conversation(app)
    run,_=question(app,conv,'Explain a general technical term')
    empty=wait(app,run['runId'])
    assert empty['status']=='completed' and empty['retrieval']['status']=='no_evidence'
    assert not empty['answer']['citations']
    indexed(app)
    app.database.execute('ALTER TABLE embedding_records RENAME TO temporarily_unavailable_vectors')
    try:
        broken,_=question(app,conv,'alpha material')
        failure=wait(app,broken['runId'])
        assert failure['status']=='failed' and failure['error']['phase']=='retrieval'
        assert 'generation' not in failure['usage']
        assert not any(e['type']=='complete' for e in events(app,broken['runId']))
    finally:
        app.database.execute('ALTER TABLE temporarily_unavailable_vectors RENAME TO embedding_records')


def test_completion_storage_failure_is_not_published_as_complete(documents_app):
    app=documents_app
    indexed(app)
    app.database.execute('''CREATE FUNCTION reject_answer_completion() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.role='assistant' AND NEW.status='completed' THEN RAISE EXCEPTION 'test completion persistence failure'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER reject_answer_completion BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION reject_answer_completion();''')
    try:
        run,_=question(app,conversation(app))
        failed=wait(app,run['runId'])
        assert failed['status']=='failed' and failed['error']['phase']=='persistence',failed
        recorded=events(app,run['runId'])
        assert recorded[-1]['type']=='error' and not any(e['type']=='complete' for e in recorded)
    finally:
        app.database.execute('DROP TRIGGER reject_answer_completion ON messages; DROP FUNCTION reject_answer_completion()')


def test_optional_reranker_failure_falls_back_without_ontology(documents_app):
    app=documents_app
    indexed(app)
    app.server.environment.update(OW_RERANKER_MODE='cross_encoder',OW_RERANKER_PYTHON_PATH='/no/such/python',OW_RERANKER_MODEL_PATH='/no/such/model')
    app.server.restart()
    run,_=question(app,conversation(app))
    result=wait(app,run['runId'])
    assert result['status']=='completed' and result['retrieval']['reranking']['status']=='fallback'
    assert result['answer']['warnings']


@pytest.mark.parametrize('extra',[{'extended':True},{'responseMode':'wiki'},{'autoWiki':True},{'role':'assistant'}])
def test_answer_contract_rejects_removed_fields(application,extra):
    conv=conversation(application)
    response=application.server.request('POST',f'/conversations/{conv}/turns',token=application.tokens['alice'],
        json={'question':'test','requestId':uuid4().hex,**extra})
    assert response.status_code==422
