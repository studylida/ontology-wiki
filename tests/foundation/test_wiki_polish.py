"""Real HTTP regressions for shared wiki authorization and replay."""
from test_shared_wiki import call, create, detail, edit_body, request_id


def test_service_admin_label_cannot_bypass_wiki_employee_policy(application):
    app = application; receipt, _ = create(app); pid = receipt['pageId']; page = detail(app, pid)
    app.database.execute("UPDATE knowledge_users SET kind='service',role='admin' WHERE username='bob'")
    try:
        actions = [('GET', '/' + pid, None),
                   ('POST', '', {'requestId': request_id(), 'title': '우회', 'markdown': '우회'}),
                   ('POST', f'/{pid}/revisions', edit_body(page, markdown='우회')),
                   ('POST', f'/{pid}/restore', {'requestId': request_id(), 'baseVersion': page['version'], 'revisionId': receipt['revisionId']}),
                   ('PATCH', f'/{pid}/protection', {'requestId': request_id(), 'baseVersion': page['version'], 'locked': True})]
        for method, path, body in actions:
            response = call(app, method, path, 'bob', **({'json': body} if body else {}))
            assert response.status_code == 403 and response.json()['error']['code'] == 'wiki_employee_required'
    finally:
        app.database.execute("UPDATE knowledge_users SET kind='user',role='user' WHERE username='bob'")
    assert detail(app, pid) == page


def test_acknowledged_request_replay_after_protection_performs_no_new_write(application):
    app = application; receipt, body = create(app); pid = receipt['pageId']; p = detail(app, pid)
    protected = call(app, 'PATCH', f'/{pid}/protection', 'operator', json={
        'requestId': request_id(), 'baseVersion': p['version'], 'locked': True})
    assert protected.status_code == 200
    replay = call(app, 'POST', '', json=body)
    assert replay.status_code == 201 and replay.json()['replayed']
    assert replay.json()['revisionId'] == receipt['revisionId']
    now = detail(app, pid)
    assert now['locked'] and now['revisionNumber'] == 1 and now['version'] == 2
    assert not now['canEdit'] and not now['canProtect']
