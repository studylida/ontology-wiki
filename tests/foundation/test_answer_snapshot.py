"""Every restored body must correspond exactly to its durable replay cursor."""
import json
from concurrent.futures import ThreadPoolExecutor
from test_document_pipeline import documents_app, upload, work


def test_concurrent_snapshot_and_stream_have_one_consistent_boundary(documents_app):
    app = documents_app
    upload(app)
    assert work(app)['status'] == 'succeeded'
    token = app.tokens['alice']
    conversation = app.server.request('POST', '/conversations', token=token, json={}).json()['id']
    accepted = app.server.request('POST', f'/conversations/{conversation}/turns', token=token,
        json={'question': 'alpha material conditions', 'requestId': 'snapshot-concurrency'})
    assert accepted.status_code == 202
    run_id = accepted.json()['runId']
    def snapshot(_):
        response = app.server.request('GET', f'/answer-runs/{run_id}', token=token)
        assert response.status_code == 200
        return response.json()
    with ThreadPoolExecutor(max_workers=6) as pool:
        snapshots = list(pool.map(snapshot, range(36)))
    response = app.server.request('GET', f'/answer-runs/{run_id}/events', token=token)
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'complete'
    for view in snapshots:
        prefix = ''.join(event['data']['text'] for event in events
            if event['type'] == 'delta' and event['seq'] <= view['durableSeq'])
        assert prefix == view['answer']['content']
    assert app.database.query('SELECT count(*) AS n FROM answer_runs')[0]['n'] == 1
