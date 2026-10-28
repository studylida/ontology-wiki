"""One source through partial indexing, answers, failed revision and withdrawal."""
from test_document_pipeline import documents_app, upload, work, detail, action
from test_answer_pipeline import conversation, question, wait, events


def test_partial_source_remains_useful_without_reviving_held_or_failed_revision(documents_app):
    app = documents_app
    # A single oversized source block is preserved/held, not sliced into misleading facts.
    valid = '# Alpha fixture\n\nAlpha material is tested at 250 C for 30 min on M1. Synthetic only.\n\n'
    long_block = '## Held appendix\n\n' + ('unverified table-value ' * 600) + '\n'
    source = upload(app, body=(valid + long_block).encode(), title='Partial fixture')
    assert work(app)['status'] == 'succeeded'
    state = detail(app, source['documentId'])
    assert state['status'] == 'partial' and state['searchable']
    original_revision = state['activeRevisionId']
    passages = app.server.request('GET', f"/documents/{source['documentId']}/passages", token=app.tokens['bob']).json()['passages']
    held = {p['id'] for p in passages if p['excluded']}
    assert held and any(not p['excluded'] for p in passages)
    conv = conversation(app)
    first, _ = question(app, conv, text='What are the Alpha material conditions?')
    answer = wait(app, first['runId'])
    assert answer['status'] == 'completed'
    assert not held.intersection(e['passageId'] for e in answer['retrieval']['evidence'])
    assert original_revision in answer['retrieval']['sourceRevisionIds']
    bad = upload(app, body=b'\xff\xfe', filename='replacement.txt', document_id=source['documentId'])
    assert bad['revisionId'] != original_revision
    assert work(app)['status'] == 'failed'
    state = detail(app, source['documentId'])
    assert state['status'] == 'failed' and state['searchable']
    assert state['activeRevisionId'] == original_revision
    second, _ = question(app, conv, text='Which temperature and duration were used?')
    followup = wait(app, second['runId'])
    assert followup['status'] == 'completed'
    assert followup['retrieval']['sourceRevisionIds'] == [original_revision]
    assert not held.intersection(e['passageId'] for e in followup['retrieval']['evidence'])
    action(app, source['documentId'], 'deactivate', expect=200)
    transcript = app.server.request('GET', '/conversations/' + conv, token=app.tokens['alice']).json()
    assistants = [m for m in transcript['messages'] if m['role'] == 'assistant']
    assert len(assistants) == 2
    assert all(m['sourceUnavailable'] and not m['content'] and not m['citations'] for m in assistants)
    assert app.server.request('GET', f"/answer-runs/{second['runId']}/events", token=app.tokens['alice']).status_code == 409
    assert app.server.request('POST', f"/documents/{source['documentId']}/reprocess", token=app.tokens['alice']).status_code == 409
