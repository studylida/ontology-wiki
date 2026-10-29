"""Real database/HTTP/worker tests; only the embedding provider is an explicit fixture."""
import asyncio
from dataclasses import replace
import json
import os
import secrets
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from conftest import Server, cli


@pytest.fixture(scope='module')
def discovery(database_factory, tmp_path_factory):
    with database_factory() as db:
        env = {**os.environ, 'OW_DATABASE_URL': db.url, 'OW_PROVIDER_MODE': 'fixture',
            'OW_AUTH_SECRET': secrets.token_hex(32), 'OW_BOOTSTRAP_PASSWORD': secrets.token_urlsafe(24)}
        env.pop('OPENAI_API_KEY', None)
        cli(env, 'migrate', '--database-name', db.name)
        for name, role in [('alice', 'user'), ('bob', 'user'), ('operator', 'admin')]:
            cli(env, 'create-user', '--username', name, '--role', role)
        server = Server(env, tmp_path_factory.mktemp('wiki-discovery'))
        try:
            server.start()
            tokens = {name: server.request('POST','/auth/login',json={'username': name,
                'password': env['OW_BOOTSTRAP_PASSWORD']}).json()['accessToken'] for name in ('alice','bob','operator')}
            yield SimpleNamespace(server=server, database=db, environment=env, tokens=tokens)
        finally:
            server.stop()


def api(app, method, path, user='alice', **kw):
    return app.server.request(method, '/wiki' + path, token=app.tokens[user], **kw)


def create(app, title, markdown='## 개념\n\n안전한 본문', **extra):
    result = api(app, 'POST', '/pages', json={'requestId': str(uuid4()), 'title': title, 'markdown': markdown, **extra})
    assert result.status_code == 201, result.text
    return api(app, 'GET', '/pages/' + result.json()['pageId']).json()


def edit(app, page, **changes):
    body = {k: page['revision'][k] for k in ('title','markdown','sourceNote','aliases','meaning')}
    result = api(app, 'POST', f"/pages/{page['id']}/revisions", json={**body, 'requestId': str(uuid4()),
        'baseVersion': page['version'], **changes})
    assert result.status_code == 201, result.text
    return api(app, 'GET', '/pages/' + page['id']).json()


def work(app):
    result = json.loads(cli(app.environment, 'worker', '--once').stdout)
    assert result['status'] in ('succeeded', 'idle', 'superseded'), result
    return result


def drain(app):
    for _ in range(40):
        if work(app)['status'] == 'idle':
            return
    pytest.fail('Unexpected unbounded wiki jobs')


def test_aliases_same_names_and_manual_rename_are_immediate(discovery):
    app = discovery
    a = create(app, 'CMP (공정)', aliases=['CMP', 'cmp', 'Chemical Mechanical Planarization'], meaning='웨이퍼 공정')
    b = create(app, 'CMP (소프트웨어)', aliases=['CMP'], meaning='프로젝트 내 약어')
    assert a['aliases'] == ['CMP', 'Chemical Mechanical Planarization']
    alternatives = api(app, 'GET', f"/pages/{a['id']}/alternatives")
    assert alternatives.status_code == 200, alternatives.text
    assert any(x['page']['id'] == b['id'] for x in alternatives.json())
    # Hints use exact normalized names, not a model or an inferred semantic relation.
    c = create(app, 'OnlyDistinctName', meaning='이름이 겹치지 않음')
    assert api(app, 'GET', f"/pages/{c['id']}/alternatives").json() == []
    old_id = a['id']; a = edit(app, a, title='새 공정명')
    assert a['id'] == old_id and a['revision']['aliases'][0] == 'CMP'
    assert api(app, 'POST', '/search', json={'query': 'CMP'}).status_code == 200
    drain(app)


def test_actual_passages_vectors_profile_and_duplicate_notice(discovery):
    app = discovery
    markdown = '# RUL\n\n## 고객 A\n\n부하 조건을 확인하고 잔여 수명을 예측한다.\n\n## 편집 기록\n\nNEVER_INDEX_AUDIT'
    page = create(app, 'Remaining Useful Life', markdown, aliases=['RUL', '잔여 수명'],
                  meaning='설비의 잔여 수명 예측', sourceNote='NEVER_INDEX_STAFF_NOTE')
    status = api(app, 'GET', f"/pages/{page['id']}/index").json()
    assert status['status'] == 'queued' and not status['indexedRevisionId']
    drain(app)
    status = api(app, 'GET', f"/pages/{page['id']}/index").json()
    assert status['status'] == 'ready', status
    assert status['indexedRevisionId'] == page['currentRevisionId']
    rows = app.database.query('SELECT * FROM wiki_passages WHERE revision_id=$1 ORDER BY ordinal', page['currentRevisionId'])
    assert len(rows) >= 2
    for row in rows:
        assert markdown[row['start_offset']:row['end_offset']] == row['text']
        assert 'NEVER_INDEX' not in row['embedding_text']
    assert any('고객 A' in r['locator'] for r in rows)
    assert app.database.query('SELECT count(*) n FROM wiki_passage_embeddings')[0]['n'] > 0
    found = api(app, 'POST', '/search', json={'query': 'RUL 잔여 수명 부하 조건'})
    assert found.status_code == 200, found.text
    assert found.json()['semanticStatus'] == 'used'
    assert page['id'] in {h['page']['id'] for h in found.json()['items']}
    similar = api(app, 'POST', '/similar', json={'title': 'RUL', 'markdown': '잔여 수명 예측'})
    assert similar.status_code == 200 and any(h['page']['id'] == page['id'] for h in similar.json()['items'])
    duplicate = create(app, 'Remaining Useful Life', '다른 작성자의 별도 문서')
    assert duplicate['id'] != page['id']
    drain(app)


def test_partial_oversized_passages_and_revision_switch(discovery):
    app = discovery
    page = create(app, 'PartialStage2', '## 정상\n\n정상 핵심 설명\n\n## 긴 표\n\n|' + '긴 내용' * 2500 + '|')
    drain(app)
    status = api(app, 'GET', f"/pages/{page['id']}/index").json()
    assert status['status'] == 'partial' and status['heldPassages']
    old = page['currentRevisionId']
    page = edit(app, page, markdown='## 새 판본\n\n새로운 유효 설명')
    pending = api(app, 'GET', f"/pages/{page['id']}/index").json()
    assert pending['indexedRevisionId'] == old and pending['status'] == 'queued'
    # Old passages must not masquerade as current evidence while reindexing.
    found = api(app, 'POST', '/search', json={'query': 'PartialStage2 정상 핵심 설명'}).json()
    assert all(hit['revisionId'] != old for hit in found['items'])
    drain(app)
    ready = api(app, 'GET', f"/pages/{page['id']}/index").json()
    assert ready['status'] == 'ready' and ready['indexedRevisionId'] == page['currentRevisionId']


def test_index_failure_keeps_body_and_retries_without_duplication(discovery):
    app = discovery
    page = create(app, 'RetryStage2', '## 본문\n\n실패해도 보존되는 본문')
    disabled = {**app.environment, 'OW_PROVIDER_MODE': 'disabled'}
    result = json.loads(cli(disabled, 'worker', '--once').stdout)
    assert result['status'] == 'failed', result
    state = api(app, 'GET', f"/pages/{page['id']}/index").json()
    assert state['status'] == 'failed' and state['canRetry']
    assert api(app, 'GET', '/pages/' + page['id']).json()['revision']['markdown'] == page['revision']['markdown']
    for _ in range(2):
        result = api(app, 'POST', f"/pages/{page['id']}/index/retry", json={'baseVersion': page['version']})
        assert result.status_code == 202, result.text
    drain(app)
    assert api(app, 'GET', f"/pages/{page['id']}/index").json()['status'] == 'ready'
    assert app.database.query('SELECT count(*) n FROM wiki_index_jobs WHERE revision_id=$1', page['currentRevisionId'])[0]['n'] == 1
    assert app.database.query('SELECT count(*) n FROM wiki_revisions WHERE page_id=$1', page['id'])[0]['n'] == 1


def test_permissions_invalid_queries_and_same_title_not_blocked(discovery):
    app = discovery
    assert app.server.request('POST', '/wiki/search', json={'query':'RUL'}).status_code == 401
    assert api(app,'POST','/search',json={'query':'  '}).status_code == 422
    assert api(app,'POST','/search',json={'query':'bad\u0000input'}).status_code == 422
    page = create(app,'ProtectedStage2')
    protection = api(app,'PATCH',f"/pages/{page['id']}/protection",'operator',json={
        'requestId':str(uuid4()),'baseVersion':page['version'],'locked':True})
    assert protection.status_code == 200
    assert api(app,'POST',f"/pages/{page['id']}/index/retry",json={'baseVersion':protection.json()['version']}).status_code == 403
    drain(app)


def test_new_revision_failure_keeps_previous_index_but_never_returns_it_as_current(discovery):
    app = discovery
    page = create(app, 'KeepPreviousIndex', '## 원본\n\nold-search-only-token')
    drain(app)
    old = page['currentRevisionId']
    current = edit(app, page, markdown='## 편집 기록\n\nonly-audit-not-knowledge')
    failed = json.loads(cli(app.environment, 'worker', '--once').stdout)
    assert failed['status'] == 'failed', failed
    state = api(app, 'GET', f"/pages/{page['id']}/index").json()
    assert state['status'] == 'failed' and state['indexedRevisionId'] == old
    found = api(app, 'POST', '/search', json={'query': 'old-search-only-token'}).json()
    assert all(h['revisionId'] != old for h in found['items'])
    assert api(app, 'GET', f"/pages/{page['id']}/revisions/{old}").status_code == 200
    assert api(app, 'GET', '/pages/' + page['id']).json()['currentRevisionId'] == current['currentRevisionId']


def test_shared_cache_reuse_superseded_job_and_profile_isolation(discovery):
    from knowledge.core.config import Settings
    from knowledge.integrations.providers import FixtureEmbeddingClient
    from knowledge.wiki.index_repository import WikiIndexRepository
    from knowledge.wiki.indexing import process_wiki_index_job
    from knowledge.wiki.search import WikiSearchService
    from knowledge.identity.dto import Principal
    from knowledge.identity.entities import User
    from sqlalchemy import select
    app = discovery
    page = create(app, 'CacheSupersedeStage2', '## 내용\n\nunique reusable content')

    async def scenario():
        engine = create_async_engine(app.database.url)
        sessions = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
        settings = Settings(database_url=app.database.url, provider_mode='fixture')
        class Counting(FixtureEmbeddingClient):
            calls = 0
            async def embed(self, texts):
                self.calls += 1
                return await super().embed(texts)
        provider = Counting()
        async def run_next():
            async with sessions() as session, session.begin():
                job = await WikiIndexRepository(session).claim(); jid = job.id
            return await process_wiki_index_job(sessions, settings, jid, provider)
        try:
            assert (await run_next())['status'] == 'succeeded'
            calls = provider.calls
            changed = await asyncio.to_thread(edit, app, page, changeSummary='본문은 그대로')
            assert (await run_next())['status'] == 'succeeded'
            assert provider.calls == calls
            async with sessions() as session:
                user = await session.scalar(select(User).where(User.username == 'alice'))
                principal = Principal(id=user.id, username=user.username, role=user.role, kind=user.kind)
            class OtherProfile(Counting):
                profile_id = 'fixture:other-space:1536:v1'
            other = OtherProfile()
            search = WikiSearchService(sessions, settings, other)
            assert (await search.status(principal, page['id'])).status == 'profile_mismatch'
            result = await search.search(principal, 'CacheSupersedeStage2')
            assert result.semantic_status == 'unavailable' and other.calls == 0
            assert not any('vector' in h.methods for h in result.items)
            class FixtureRerank:
                calls = 0
                async def rerank(self, query, hits):
                    self.calls += 1
                    return {'hits': list(reversed(hits)), 'provider': 'explicit-fixture'}
            successful = FixtureRerank()
            verified = await WikiSearchService(sessions, settings, provider, successful).search(principal, 'CacheSupersedeStage2')
            assert successful.calls == 1 and verified.reranking == {'provider': 'explicit-fixture', 'status': 'used'}
            assert verified.items
            class BrokenRerank:
                calls = 0
                async def rerank(self, query, hits):
                    self.calls += 1; assert hits
                    raise RuntimeError('synthetic reranker outage')
            reranker = BrokenRerank()
            result = await WikiSearchService(sessions, settings, provider, reranker).search(principal, 'CacheSupersedeStage2')
            assert result.reranking['status'] == 'fallback' and result.items and reranker.calls == 1
            pending = await asyncio.to_thread(edit, app, changed, markdown='새 실행에서 바뀔 본문')
            class EditDuringEmbed(Counting):
                async def embed(self, texts):
                    await asyncio.to_thread(edit, app, pending, markdown='가장 최신 본문')
                    return await super().embed(texts)
            provider = EditDuringEmbed()
            assert (await run_next())['status'] == 'superseded'
            provider = Counting()
            assert (await run_next())['status'] == 'succeeded'
        finally:
            await engine.dispose()
    asyncio.run(scenario())
    assert api(app, 'GET', f"/pages/{page['id']}/index").json()['status'] == 'ready'


def test_search_database_failure_is_not_an_empty_result(discovery):
    app = discovery
    app.database.execute('ALTER TABLE wiki_passages RENAME TO unavailable_wiki_passages')
    try:
        response = api(app, 'POST', '/search', json={'query': 'RUL'})
        assert response.status_code == 503 and response.json()['error']['code'] == 'wiki_search_failed'
    finally:
        app.database.execute('ALTER TABLE unavailable_wiki_passages RENAME TO wiki_passages')


def test_stage1_migration_backfills_current_wiki_once(database_factory):
    from conftest import ROOT
    from knowledge.migration.schema import migration_files
    with database_factory() as db:
        db.execute('CREATE TABLE knowledge_schema_migrations (version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())')
        for name, (body, digest) in migration_files().items():
            if name.startswith(('001_', '002_', '003_', '004_')):
                db.execute(body)
                db.execute('INSERT INTO knowledge_schema_migrations(version,sha256) VALUES($1,$2)', name, digest)
        db.execute("INSERT INTO knowledge_users(id,username,password_hash) VALUES('stage1-user','stage1-user','not-a-login-hash')")
        db.execute("""BEGIN;
        INSERT INTO wiki_pages(id,creator_id,current_revision_id,version,created_at,updated_at) VALUES('old-page','stage1-user','old-rev',1,now(),now());
        INSERT INTO wiki_revisions(id,page_id,number,title,markdown,editor_id,created_at) VALUES('old-rev','old-page',1,'OLD','보존 원문','stage1-user',now()); COMMIT;""")
        before = db.query('SELECT version,sha256 FROM knowledge_schema_migrations ORDER BY version')
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'backend'), 'OW_DATABASE_URL': db.url}
        assert json.loads(cli(env, 'migrate', '--database-name', db.name).stdout)['applied'] == ['005_wiki_discovery.sql', '006_wiki_publication.sql']
        assert json.loads(cli(env, 'migrate', '--database-name', db.name).stdout)['applied'] == []
        assert db.query("SELECT version,sha256 FROM knowledge_schema_migrations WHERE version NOT IN ('005_wiki_discovery.sql','006_wiki_publication.sql') ORDER BY version") == before
        assert db.query('SELECT markdown FROM wiki_revisions')[0]['markdown'] == '보존 원문'
        assert db.query('SELECT revision_id,status FROM wiki_index_jobs') == [{'revision_id':'old-rev', 'status':'pending'}]


def test_stage1_receipt_replay_survives_new_optional_name_fields(discovery):
    import hashlib
    app = discovery
    request_id = str(uuid4())
    body = {'requestId':request_id, 'title':'OldReceiptStage2', 'markdown':'unchanged content'}
    created = api(app, 'POST', '/pages', json=body)
    assert created.status_code == 201
    pid = created.json()['pageId']
    old_payload = {'operation':'create', 'pageId':None, 'body':{
        'title':body['title'], 'markdown':body['markdown'], 'source_note':'', 'change_summary':''}}
    old_hash = hashlib.sha256(json.dumps(old_payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    # This is exactly a durable receipt produced by the Stage-1 request contract.
    app.database.execute('UPDATE wiki_mutations SET payload_hash=$1 WHERE request_id=$2',old_hash,request_id)
    replay = api(app, 'POST', '/pages', json=body)
    assert replay.status_code == 201 and replay.json()['replayed'] is True
    assert replay.json()['pageId'] == pid
    assert api(app, 'POST', '/pages', json={**body,'aliases':['different meaning']}).status_code == 409
    assert app.database.query('SELECT count(*) n FROM wiki_revisions WHERE page_id=$1',pid)[0]['n'] == 1
    drain(app)
