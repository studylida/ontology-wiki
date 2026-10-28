"""Current-source and execution boundaries using real Stage 2 intake."""
from uuid import uuid4
from test_document_pipeline import documents_app, upload, work, action
from test_answer_pipeline import conversation, question, wait, events, indexed


def test_replaced_revision_is_historical_and_not_reused_as_current_history(documents_app):
    app = documents_app
    old = indexed(app)
    conv = conversation(app)
    run, _ = question(app, conv)
    assert wait(app, run['runId'])['status'] == 'completed'
    new = upload(app, body=b'# Reference\n\n## Updated conditions\n\nThe new reference uses beta material at 300 C.\n',
                 document_id=old['documentId'])
    assert work(app)['status'] == 'succeeded'
    saved = wait(app, run['runId'])
    assert saved['answer']['historicalSources'] and not saved['answer']['sourceUnavailable']
    assert {c['sourceRevisionId'] for c in saved['answer']['citations']} == {old['revisionId']}
    follow, _ = question(app, conv, 'What conditions apply now?')
    result = wait(app, follow['runId'])
    assert result['status'] == 'completed'
    assert result['retrieval']['sourceRevisionIds'] == [new['revisionId']]
    assert result['usage']['generation']['historyMessages'] == 1
    assert all(h['sourceRevisionId'] != old['revisionId'] for h in result['retrieval']['evidence'])


def test_two_different_source_conditions_reach_one_answer_context(documents_app):
    app = documents_app
    first = indexed(app)
    second = upload(app, filename='alternative.md', title='Alternative reference',
        body=b'# Alternative reference\n\n## Experimental conditions\n\nThe sample uses beta material at 300 C for a different evaluation goal.\n')
    assert work(app)['status'] == 'succeeded'
    run, _ = question(app, conversation(app), 'Compare the alpha and beta material experimental conditions.')
    result = wait(app, run['runId'])
    assert result['status'] == 'completed'
    assert set(result['retrieval']['sourceRevisionIds']) == {first['revisionId'], second['revisionId']}
    evidence = result['retrieval']['evidence']
    assert {'250 C', '300 C'} <= {term for term in ('250 C', '300 C') if any(term in h['text'] for h in evidence)}
    assert result['usage']['generation']['promptEvidenceIds'] == [h['passageId'] for h in evidence]
    # This checks evidence delivery, not the semantic quality of a fixture's comparison.


def test_immediate_cancel_never_publishes_a_completed_answer(documents_app):
    app = documents_app
    indexed(app)
    run, _ = question(app, conversation(app))
    response = app.server.request('POST', f"/answer-runs/{run['runId']}/cancel", token=app.tokens['alice'])
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'cancelled'
    recorded = events(app, run['runId'])
    assert recorded[-1]['type'] == 'cancelled'
    assert not any(e['type'] == 'complete' for e in recorded)


def test_deactivation_during_generation_stops_and_blocks_replay(documents_app):
    app = documents_app
    source = indexed(app)
    run, _ = question(app, conversation(app))
    wait(app, run['runId'], states=('generating',))
    action(app, source['documentId'], 'deactivate', expect=200)
    result = wait(app, run['runId'])
    assert result['status'] == 'failed', result
    assert result['error']['code'] == 'source_unavailable'
    assert result['answer']['sourceUnavailable'] and not result['answer']['content']
    assert app.server.request('GET', f"/answer-runs/{run['runId']}/events", token=app.tokens['alice']).status_code == 409
