"""Real PostgreSQL + HTTP tests for manual shared editing, no model calls."""
from concurrent.futures import ThreadPoolExecutor
import uuid
import pytest


def request_id():
    return str(uuid.uuid4())


def call(app, method, path, name='alice', **kwargs):
    return app.server.request(method, '/wiki/pages' + path, token=app.tokens[name], **kwargs)


def create(app, name='alice', **values):
    body = {'requestId': request_id(), 'title': '공유 개념', 'markdown': '# 개념\n\n첫 설명  \n',
            'sourceNote': '직원이 기록한 업무 경험. 공식 지침이 아님.', **values}
    response = call(app, 'POST', '', name, json=body)
    assert response.status_code == 201, response.text
    return response.json(), body


def detail(app, page_id, name='alice'):
    response = call(app, 'GET', '/' + page_id, name)
    assert response.status_code == 200, response.text
    return response.json()


def edit_body(page, **values):
    return {'requestId': request_id(), 'baseVersion': page['version'], 'title': page['title'],
            'markdown': page['revision']['markdown'], 'sourceNote': page['revision']['sourceNote'], **values}


def test_employee_collaboration_revision_restore_and_process_restart(application):
    app = application
    receipt, body = create(app)
    page_id = receipt['pageId']; first = detail(app, page_id, 'bob')
    assert first['canEdit'] and not first['canProtect'] and first['creator']['username'] == 'alice'
    assert first['revision']['markdown'] == body['markdown']
    changed = call(app, 'POST', f'/{page_id}/revisions', 'bob', json=edit_body(first,
        title='새 제목', markdown='## 새 설명\n업무 조건을 보강했습니다.\n', changeSummary='활용 조건 추가'))
    assert changed.status_code == 201, changed.text
    second = detail(app, page_id)
    assert second['revisionNumber'] == 2 and second['editor']['username'] == 'bob'
    assert second['creator']['username'] == 'alice'
    history = call(app, 'GET', f'/{page_id}/revisions').json()
    assert history['total'] == 2
    comparison = call(app, 'GET', f'/{page_id}/compare', params={'fromRevisionId': first['currentRevisionId'], 'toRevisionId': second['currentRevisionId']})
    assert comparison.status_code == 200 and '+새 제목' in comparison.json()['diff']
    restore = {'requestId': request_id(), 'baseVersion': second['version'], 'revisionId': first['currentRevisionId']}
    result = call(app, 'POST', f'/{page_id}/restore', 'bob', json=restore)
    assert result.status_code == 201, result.text
    third = detail(app, page_id)
    assert third['revisionNumber'] == 3 and third['revision']['markdown'] == body['markdown']
    assert third['title'] == body['title'] and third['revision']['restoredFromId'] == first['currentRevisionId']
    assert third['editor']['username'] == 'bob'
    assert call(app, 'GET', f'/{page_id}/revisions/{second["currentRevisionId"]}').json()['title'] == '새 제목'
    pid = app.server.process.pid; app.server.restart()
    assert app.server.process.pid != pid and detail(app, page_id) == third
    assert app.database.query('SELECT count(*) AS n FROM wiki_revisions WHERE page_id=$1', page_id)[0]['n'] == 3


def test_admin_only_protection_covers_edit_and_restore(application):
    app = application; receipt, _ = create(app); pid = receipt['pageId']; p = detail(app, pid)
    protection = {'requestId': request_id(), 'baseVersion': p['version'], 'locked': True}
    for user in ('alice', 'bob'):
        assert call(app, 'PATCH', f'/{pid}/protection', user, json=protection).status_code == 403
    assert call(app, 'PATCH', f'/{pid}/protection', 'operator', json=protection).status_code == 200
    locked = detail(app, pid, 'bob'); assert locked['locked'] and not locked['canEdit']
    assert call(app, 'GET', f'/{pid}/revisions', 'bob').status_code == 200
    for user in ('alice', 'bob'):
        assert call(app, 'POST', f'/{pid}/revisions', user, json=edit_body(locked, markdown='우회')).status_code == 403
        assert call(app, 'POST', f'/{pid}/restore', user, json={'requestId': request_id(), 'baseVersion': locked['version'], 'revisionId': p['currentRevisionId']}).status_code == 403
    assert call(app, 'POST', f'/{pid}/revisions', 'operator', json=edit_body(locked, markdown='관리자 수정')).status_code == 201
    current = detail(app, pid)
    assert call(app, 'PATCH', f'/{pid}/protection', 'operator', json={'requestId': request_id(), 'baseVersion': current['version'], 'locked': False}).status_code == 200
    unlocked = detail(app, pid)
    assert unlocked['canEdit'] and not unlocked['locked']
    assert call(app, 'POST', f'/{pid}/revisions', 'bob', json=edit_body(unlocked, markdown='직원 보강')).status_code == 201


def test_edit_lock_unlock_invalidates_old_form(application):
    app = application; receipt, _ = create(app); pid = receipt['pageId']; original = detail(app, pid)
    for locked in (True, False):
        p = detail(app, pid)
        assert call(app, 'PATCH', f'/{pid}/protection', 'operator', json={'requestId': request_id(), 'baseVersion': p['version'], 'locked': locked}).status_code == 200
    response = call(app, 'POST', f'/{pid}/revisions', 'alice', json=edit_body(original, markdown='오래된 양식'))
    assert response.status_code == 409 and response.json()['error']['code'] == 'wiki_version_conflict'
    assert detail(app, pid)['revisionNumber'] == 1


def test_concurrent_edit_one_wins_without_lost_update(application):
    app = application; receipt, _ = create(app); pid = receipt['pageId']; p = detail(app, pid)
    def write(name):
        return call(app, 'POST', f'/{pid}/revisions', name, json=edit_body(p, markdown=name))
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(write, ['alice', 'bob']))
    assert sorted(r.status_code for r in responses) == [201, 409]
    assert detail(app, pid)['revisionNumber'] == 2
    assert call(app, 'GET', f'/{pid}/revisions').json()['total'] == 2


def test_same_request_create_and_restore_are_idempotent(application):
    app = application
    receipt, body = create(app)
    repeated = call(app, 'POST', '', json=body)
    assert repeated.status_code == 201 and repeated.json()['replayed']
    assert repeated.json()['pageId'] == receipt['pageId']
    conflict = call(app, 'POST', '', json={**body, 'title': '다른 내용'})
    assert conflict.status_code == 409
    pid = receipt['pageId']; p = detail(app, pid)
    restore = {'requestId': request_id(), 'baseVersion': p['version'], 'revisionId': p['currentRevisionId']}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: call(app, 'POST', f'/{pid}/restore', 'bob', json=restore), range(2)))
    assert all(r.status_code == 201 for r in results)
    assert len({r.json()['revisionId'] for r in results}) == 1
    assert detail(app, pid)['revisionNumber'] == 2


def test_duplicate_titles_stable_ids_and_title_search(application):
    app = application; title = '동음이의어_' + request_id()
    a, _ = create(app, title=title); b, _ = create(app, 'bob', title=title)
    assert a['pageId'] != b['pageId']
    found = call(app, 'GET', '', params={'q': title}).json()
    assert found['total'] == 2 and {i['id'] for i in found['items']} == {a['pageId'], b['pageId']}
    first = detail(app, a['pageId'])
    assert call(app, 'POST', f'/{a["pageId"]}/revisions', json=edit_body(first, title=title + ' 새 이름')).status_code == 201
    assert detail(app, a['pageId'])['id'] == a['pageId']
    literal = '100%_literal_' + request_id(); create(app, title=literal)
    assert call(app, 'GET', '', params={'q': literal, 'limit': 1}).json()['total'] == 1


def test_other_page_revision_cannot_be_read_compared_or_restored(application):
    app = application; a, _ = create(app); b, _ = create(app)
    pid = a['pageId']; p = detail(app, pid); other = b['revisionId']
    assert call(app, 'GET', f'/{pid}/revisions/{other}').status_code == 404
    assert call(app, 'GET', f'/{pid}/compare', params={'fromRevisionId': other, 'toRevisionId': p['currentRevisionId']}).status_code == 404
    assert call(app, 'POST', f'/{pid}/restore', json={'requestId': request_id(), 'baseVersion': p['version'], 'revisionId': other}).status_code == 404
    assert detail(app, pid)['revisionNumber'] == 1


@pytest.mark.parametrize('bad', [{'title': '   '}, {'markdown': '  '}, {'markdown': 'bad\x00text'}, {'locked': True}, {'editorId': 'another'}, {'title': 'two\nlines'}])
def test_invalid_input_does_not_create_a_page(application, bad):
    app = application
    response = call(app, 'POST', '', json={'requestId': request_id(), 'title': '검증', 'markdown': '내용', **bad})
    assert response.status_code == 422, response.text


def test_auth_required_and_service_principal_denied(application):
    app = application
    assert app.server.request('GET', '/wiki/pages').status_code == 401
    assert app.server.request('POST', '/wiki/pages', json={'title': 'x', 'markdown': 'y', 'requestId': request_id()}).status_code == 401
    app.database.execute("UPDATE knowledge_users SET kind='service' WHERE username='bob'")
    try: assert call(app, 'GET', '', 'bob').status_code == 403
    finally: app.database.execute("UPDATE knowledge_users SET kind='user' WHERE username='bob'")
    # Session lookup rejects inactive users before wiki operations, just as chat does.
    app.database.execute("UPDATE knowledge_users SET is_active=false WHERE username='bob'")
    try: assert call(app, 'GET', '', 'bob').status_code == 401
    finally: app.database.execute("UPDATE knowledge_users SET is_active=true WHERE username='bob'")


def test_storage_failure_has_no_partial_revision_or_success_receipt(application):
    app = application; receipt, _ = create(app); pid = receipt['pageId']; p = detail(app, pid)
    app.database.execute("""CREATE FUNCTION reject_wiki_test() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN IF NEW.change_summary='FAIL_STORAGE_TEST' THEN RAISE EXCEPTION 'test write failure'; END IF; RETURN NEW; END $$;
      CREATE TRIGGER wiki_test_failure BEFORE INSERT ON wiki_revisions FOR EACH ROW EXECUTE FUNCTION reject_wiki_test();""")
    body = edit_body(p, markdown='must not persist', changeSummary='FAIL_STORAGE_TEST')
    try:
        response = call(app, 'POST', f'/{pid}/revisions', json=body)
        assert response.status_code == 503 and response.json()['error']['code'] == 'wiki_storage_failed'
        assert detail(app, pid) == p
        assert not app.database.query('SELECT request_id FROM wiki_mutations WHERE request_id=$1', body['requestId'])
    finally:
        app.database.execute('DROP TRIGGER wiki_test_failure ON wiki_revisions; DROP FUNCTION reject_wiki_test()')
    assert call(app, 'POST', f'/{pid}/revisions', json=body).status_code == 201


def test_pagination_has_no_omitted_pages_or_history(application):
    app = application; name = 'pagination_' + request_id()
    receipts = [create(app, title=name)[0] for _ in range(3)]
    found = [call(app, 'GET', '', params={'q': name, 'limit': 1, 'offset': i}).json() for i in range(3)]
    assert all(x['total'] == 3 for x in found)
    assert {x['items'][0]['id'] for x in found} == {r['pageId'] for r in receipts}


def test_markdown_newline_changes_are_visible_in_comparison(application):
    app = application
    first, _ = create(app, markdown='line')
    p = detail(app, first['pageId'])
    changed = call(app, 'POST', f"/{p['id']}/revisions", json=edit_body(p, markdown='line\n'))
    assert changed.status_code == 201
    compared = call(app, 'GET', f"/{p['id']}/compare", params={
        'fromRevisionId': first['revisionId'], 'toRevisionId': changed.json()['revisionId']})
    assert compared.status_code == 200 and '개행' in compared.json()['diff']
    assert compared.json()['before']['markdown'] == 'line'
    assert compared.json()['after']['markdown'] == 'line\n'


def test_additive_upgrade_preserves_existing_chat_database(database_factory):
    import os
    from conftest import ROOT, cli
    from knowledge.migration.schema import migration_files
    with database_factory() as database:
        database.execute('CREATE TABLE knowledge_schema_migrations (version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())')
        files = migration_files()
        for name, (body, digest) in files.items():
            if name.startswith(('001_', '002_', '003_')):
                database.execute(body)
                database.execute('INSERT INTO knowledge_schema_migrations(version,sha256) VALUES($1,$2)', name, digest)
        database.execute("INSERT INTO knowledge_users(id,username,password_hash) VALUES('upgrade-user','upgrade-user','not-a-login-hash')")
        database.execute("INSERT INTO conversations(id,owner_id,title) VALUES('upgrade-chat','upgrade-user','기존 대화')")
        database.execute("INSERT INTO messages(id,conversation_id,role,content) VALUES('upgrade-message','upgrade-chat','user','보존할 기존 질문')")
        old = database.query('SELECT version,sha256 FROM knowledge_schema_migrations ORDER BY version')
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'backend'), 'OW_DATABASE_URL': database.url}
        import json
        result = json.loads(cli(env, 'migrate', '--database-name', database.name).stdout)
        assert result['applied'] == ['004_shared_wiki.sql', '005_wiki_discovery.sql', '006_wiki_publication.sql', '007_wiki_proposals.sql', '008_wiki_document_proposals.sql']
        assert database.query("SELECT content FROM messages WHERE id='upgrade-message'") == [{'content': '보존할 기존 질문'}]
        assert database.query("SELECT version,sha256 FROM knowledge_schema_migrations WHERE version NOT IN ('004_shared_wiki.sql','005_wiki_discovery.sql','006_wiki_publication.sql','007_wiki_proposals.sql','008_wiki_document_proposals.sql') ORDER BY version") == old
        assert database.query('SELECT count(*) AS n FROM wiki_pages') == [{'n': 0}]
