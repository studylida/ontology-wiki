"""Stage 3 real PostgreSQL, HTTP, worker and durable answer tests; providers are fixtures."""
import asyncio
import hashlib
import json
from uuid import uuid4
import pytest
from test_document_pipeline import documents_app, upload, work, action
from test_answer_pipeline import conversation, question, wait, events
from test_wiki_discovery import api, create, edit, drain


def mixed(app):
    source = upload(app, title='Alpha reference', body=b'# Alpha reference\n\nAlpha material is measured at 250 C under laboratory load.\n')
    page = create(app, 'Alpha operating knowledge', '## Alpha customer context\n\nAlpha material supports a customer maintenance discussion. This is a synthetic staff experience, not an official decision.\n',
                  sourceNote='Synthetic staff experience; compare Alpha reference. Not independent validation.')
    drain(app)
    return source, page


def ask_mixed(app):
    c = conversation(app)
    handle, body = question(app, c, 'Explain alpha material laboratory conditions and customer maintenance context.')
    result = wait(app, handle['runId'])
    assert result['status'] == 'completed', result
    return c, handle, body, result


def test_mixed_sources_are_real_revision_citations_and_restore_without_new_calls(documents_app):
    app = documents_app
    source, page = mixed(app)
    conv, handle, body, result = ask_mixed(app)
    found = result['retrieval']
    assert set(found['sourceRevisionIds']) == {source['revisionId'], page['currentRevisionId']}
    assert {h['sourceKind'] for h in found['evidence']} == {'document', 'wiki'}
    assert found['contextCharacters'] <= 24000
    assert result['usage']['generation']['promptEvidenceIds'] == [h['passageId'] for h in found['evidence']]
    assert {c['sourceKind'] for c in result['answer']['citations']} == {'document', 'wiki'}
    for citation in result['answer']['citations']:
        if citation['sourceKind'] == 'wiki':
            assert 'documentId' not in citation and citation['pageId'] == page['id']
            response = api(app, 'GET', f"/pages/{page['id']}/passages?revisionId={citation['sourceRevisionId']}")
        else:
            response = app.server.request('GET', f"/documents/{source['documentId']}/passages?revisionId={citation['sourceRevisionId']}", token=app.tokens['alice'])
        assert response.status_code == 200, response.text
        p = next(p for p in response.json()['passages'] if p['id'] == citation['passageId'])
        assert citation['excerpt'] == p['text'] and not p['excluded']
    saved = app.server.request('GET', '/conversations/' + conv, token=app.tokens['alice']).json()
    app.server.restart()
    assert app.server.request('GET', '/conversations/' + conv, token=app.tokens['alice']).json() == saved
    recorded = events(app, handle['runId'])
    assert ''.join(e['data']['text'] for e in recorded if e['type'] == 'delta') == result['answer']['content']
    assert len([e for e in recorded if e['type'] == 'complete']) == 1
    replay = app.server.request('POST', f'/conversations/{conv}/turns', json=body, token=app.tokens['alice'])
    assert replay.json()['runId'] == handle['runId']
    assert app.database.query('SELECT count(*) n FROM answer_runs')[0]['n'] == 1
    for user in ('bob', 'operator'):
        assert app.server.request('GET', '/conversations/' + conv, token=app.tokens[user]).status_code == 404
        assert app.server.request('GET', f"/answer-runs/{handle['runId']}", token=app.tokens[user]).status_code == 404
    follow, _ = question(app, conv, 'What are the limitations of this comparison?')
    assert wait(app, follow['runId'])['status'] == 'completed'


def test_markdown_exact_bytes_metadata_and_authenticated_export(documents_app):
    app = documents_app
    text = '# 원문\r\n\r\n조건을  보존합니다.  \r\n\r\n<script>never execute</script>\r\n'
    page = create(app, 'Markdown snapshot', text, sourceNote='직원 경험 메모')
    path = f"/wiki/pages/{page['id']}/markdown"
    assert app.server.request('GET', path).status_code == 401
    for user in ('alice', 'bob', 'operator'):
        response = app.server.request('GET', path, token=app.tokens[user])
        assert response.status_code == 200 and response.content == text.encode('utf-8')
        assert response.headers['x-wiki-page-id'] == page['id']
        assert response.headers['x-wiki-revision-id'] == page['currentRevisionId']
        assert response.headers['x-content-sha256'] == hashlib.sha256(response.content).hexdigest()
        assert response.headers['content-type'].startswith('text/markdown')
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['content-disposition'].startswith('attachment;')
    newer = edit(app, page, markdown='새 판본\n')
    assert app.server.request('GET', path, token=app.tokens['alice']).text == '새 판본\n'
    old = app.server.request('GET', path + '?revisionId=' + page['currentRevisionId'], token=app.tokens['alice'])
    assert old.content == text.encode('utf-8')
    different = create(app, 'Other page')
    assert app.server.request('GET', path + '?revisionId=' + different['currentRevisionId'], token=app.tokens['alice']).status_code == 404
    assert any(p['id'] == newer['id'] for p in api(app, 'GET', '/pages').json()['items'])
    app.database.execute("UPDATE knowledge_users SET kind='service', role='admin' WHERE username='bob'")
    assert app.server.request('GET', path, token=app.tokens['bob']).status_code == 403


def test_wiki_replacement_uses_new_evidence_but_keeps_exact_old_citation(documents_app):
    app = documents_app
    _, old = mixed(app)
    conv, handle, _, result = ask_mixed(app)
    fresh = edit(app, old, title='Alpha renamed', markdown='Alpha updated staff context applies only at a different customer load.\n')
    # Saved content is immediately readable; unindexed content is not answer evidence.
    during, _ = question(app, conv, 'Alpha current customer load?')
    pending = wait(app, during['runId'])
    assert old['currentRevisionId'] not in pending['retrieval']['sourceRevisionIds']
    assert fresh['currentRevisionId'] not in pending['retrieval']['sourceRevisionIds']
    historical = wait(app, handle['runId'])
    assert historical['answer']['historicalSources'] and not historical['answer']['sourceUnavailable']
    wiki_cite = next(c for c in result['answer']['citations'] if c['sourceKind'] == 'wiki')
    old_source = api(app, 'GET', f"/pages/{old['id']}/passages?revisionId={wiki_cite['sourceRevisionId']}").json()
    assert not old_source['active'] and old_source['title'] == old['title']
    drain(app)
    follow, _ = question(app, conv, 'Alpha updated customer load?')
    current = wait(app, follow['runId'])
    assert fresh['currentRevisionId'] in current['retrieval']['sourceRevisionIds']
    assert old['currentRevisionId'] not in current['retrieval']['sourceRevisionIds']


@pytest.mark.parametrize('withdraw', ['wiki', 'document'])
def test_withdrawal_closes_search_sources_history_and_replay(documents_app, withdraw):
    app = documents_app
    source, page = mixed(app)
    conv, handle, _, _ = ask_mixed(app)
    if withdraw == 'wiki':
        body = {'requestId': uuid4().hex, 'baseVersion': page['version']}
        assert api(app, 'POST', f"/pages/{page['id']}/deactivate", json=body).status_code == 403
        response = api(app, 'POST', f"/pages/{page['id']}/deactivate", user='operator', json=body)
        assert response.status_code == 200, response.text
        assert api(app, 'POST', f"/pages/{page['id']}/deactivate", user='operator', json=body).json()['replayed']
        for suffix in ('', '/markdown', '/passages', '/revisions', '/revisions/' + page['currentRevisionId'], '/index'):
            assert api(app, 'GET', f"/pages/{page['id']}" + suffix).status_code == 404
        found = api(app, 'POST', '/search', json={'query': 'Alpha customer'}).json()
        assert not found['items']
    else:
        action(app, source['documentId'], 'deactivate', expect=200)
        assert app.server.request('GET', f"/documents/{source['documentId']}/raw", token=app.tokens['alice']).status_code == 404
    result = wait(app, handle['runId'])
    assert result['answer']['sourceUnavailable'] and not result['answer']['content']
    assert result['answer']['citations'] == [] and result['retrieval'] is None
    assert app.server.request('GET', f"/answer-runs/{handle['runId']}/events", token=app.tokens['alice']).status_code == 409
    restored = app.server.request('GET', '/conversations/' + conv, token=app.tokens['alice']).json()
    assert restored['messages'][1]['sourceUnavailable']
    fresh, _ = question(app, conv, 'Alpha context still available?')
    fresh_result = wait(app, fresh['runId'])
    assert fresh_result['status'] == 'completed'
    removed = page['currentRevisionId'] if withdraw == 'wiki' else source['revisionId']
    assert removed not in fresh_result['retrieval']['sourceRevisionIds']


def test_wiki_only_pending_empty_and_real_search_failure_are_not_confused(documents_app):
    app = documents_app
    page = create(app, 'WikiOnly', '## 조건\n\nWikiOnly exact original passage.\n\n## 한계\n\nWikiOnly neighboring condition.\n')
    handle, _ = question(app, conversation(app), 'WikiOnly conditions?')
    assert wait(app, handle['runId'])['retrieval']['status'] == 'no_evidence'
    drain(app)
    app.server.environment['OW_RETRIEVAL_LIMIT'] = '1'
    app.server.restart()
    handle, _ = question(app, conversation(app), 'WikiOnly conditions?')
    result = wait(app, handle['runId'])
    assert result['status'] == 'completed'
    assert all(h['sourceKind'] == 'wiki' and h['hasPassage'] for h in result['retrieval']['evidence'] if 'hasPassage' in h)
    assert any('neighbor' in h['methods'] for h in result['retrieval']['evidence'])
    assert result['retrieval']['sourceRevisionIds'] == [page['currentRevisionId']]
    app.database.execute('ALTER TABLE wiki_passages RENAME TO unavailable_wiki_passages')
    try:
        handle, _ = question(app, conversation(app), 'WikiOnly conditions?')
        failure = wait(app, handle['runId'])
        assert failure['status'] == 'failed' and failure['error']['code'] == 'wiki_retrieval_failed'
    finally:
        app.database.execute('ALTER TABLE unavailable_wiki_passages RENAME TO wiki_passages')


def test_wiki_storage_failure_does_not_break_original_document_answers(documents_app):
    app = documents_app
    source, _ = mixed(app)
    app.database.execute('ALTER TABLE wiki_passages RENAME TO unavailable_wiki_passages')
    try:
        _, _, _, result = ask_mixed(app)
        assert result['retrieval']['sourceRevisionIds'] == [source['revisionId']]
        assert any('위키 검색에 실패' in w for w in result['answer']['warnings'])
    finally:
        app.database.execute('ALTER TABLE unavailable_wiki_passages RENAME TO wiki_passages')


def test_withdrawal_during_generation_stops_and_cannot_be_undone_by_worker(documents_app):
    app = documents_app
    page = create(app, 'Withdraw in progress', 'Alpha operational conditions.\n' * 20)
    drain(app)
    handle, _ = question(app, conversation(app), 'Alpha operational conditions?')
    wait(app, handle['runId'], states=('generating',))
    response = api(app, 'POST', f"/pages/{page['id']}/deactivate", user='operator', json={
        'requestId': uuid4().hex, 'baseVersion': page['version']})
    assert response.status_code == 200
    result = wait(app, handle['runId'])
    assert result['status'] == 'failed' and result['error']['code'] == 'source_unavailable'
    assert result['answer']['sourceUnavailable']
    assert app.server.request('GET', f"/answer-runs/{handle['runId']}/events", token=app.tokens['alice']).status_code == 409
    assert work(app)['status'] == 'idle'


def test_one_embedding_one_rerank_and_private_draft_never_becomes_evidence(documents_app):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from knowledge.core.config import Settings
    from knowledge.identity.service import IdentityService
    from knowledge.integrations.providers import FixtureEmbeddingClient
    from knowledge.rag.service import RAGService
    from knowledge.registry import load_entities
    load_entities()  # In-process service test needs the same registry as application startup.
    app = documents_app
    source, page = mixed(app)
    conv = conversation(app)
    before = app.database.query('SELECT count(*) n FROM wiki_revisions')[0]['n']
    assert api(app, 'POST', '/similar', json={'title': 'private-unsaved', 'markdown': 'PRIVATE_DRAFT_NEVER_PUBLISH'}).status_code == 200
    assert app.database.query('SELECT count(*) n FROM wiki_revisions')[0]['n'] == before

    class CountingEmbedding(FixtureEmbeddingClient):
        calls = 0
        async def embed(self, texts):
            self.calls += 1
            return await super().embed(texts)

    class CountingReranker:
        calls = 0
        async def rerank(self, query, hits):
            self.calls += 1
            assert {h['sourceKind'] for h in hits} == {'wiki', 'document'}
            return {'hits': hits, 'model': 'injected-fixture', 'elapsedMs': 0}

    async def run():
        engine = create_async_engine(app.database.url)
        sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
        settings = Settings(database_url=app.database.url, provider_mode='fixture', auth_secret=app.environment['OW_AUTH_SECRET'])
        embed, reranker = CountingEmbedding(), CountingReranker()
        try:
            principal = await IdentityService(sessions, settings).authenticate(app.tokens['alice'])
            _, result = await RAGService(sessions, settings, embed, reranker).retrieve(principal, conv, 'Alpha customer conditions', [])
            assert embed.calls == reranker.calls == 1
            assert result['reranking']['status'] == 'used'
            assert set(result['sourceRevisionIds']) == {source['revisionId'], page['currentRevisionId']}
            assert all('PRIVATE_DRAFT_NEVER_PUBLISH' not in h['text'] for h in result['evidence'])
        finally:
            await engine.dispose()
    asyncio.run(run())
