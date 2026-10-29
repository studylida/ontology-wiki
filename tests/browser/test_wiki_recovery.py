"""Actual browser recovery checks against real persistence, never a simulated app."""
import re
from playwright.sync_api import expect
from test_shared_wiki import login, new_page, token
import uuid


def test_acknowledged_save_readback_failure_reloads_without_another_write(browser_app):
    app = browser_app; page = app.page; login(app); writes = []; failed = []
    page.on('request', lambda req: writes.append(req.post_data_json['requestId'])
            if req.method == 'POST' and req.url.endswith('/api/v1/wiki/pages') else None)
    def readback(route):
        if route.request.method == 'GET' and not failed:
            failed.append(True)
            route.fulfill(status=503, content_type='application/json', body='{"error":{"code":"test_read_failed","message":"조회 실패"}}')
        else: route.continue_()
    page.route('**/api/v1/wiki/pages/*', readback)
    page.get_by_role('button', name='새 위키 문서', exact=True).click()
    page.get_by_label('위키 제목', exact=True).fill('저장 후 조회 실패')
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill('실제로 저장된 내용')
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_role('button', name='저장된 문서 다시 불러오기', exact=True)).to_be_visible()
    page.once('dialog', lambda dialog: dialog.accept()); page.reload()
    page.get_by_role('button', name='공용 위키', exact=True).click()
    page.get_by_role('button', name='저장된 문서 다시 불러오기', exact=True).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_contain_text('실제로 저장된 내용')
    assert len(writes) == 1
    assert app.database.query('SELECT count(*) AS n FROM wiki_revisions')[0]['n'] == 1


def test_restore_conflict_has_visible_latest_state_recovery(browser_app):
    app = browser_app; page = app.page; login(app); pid = new_page(app); bob = token(app, 'bob')
    def change(version, content):
        response = app.server.request('POST', f'/wiki/pages/{pid}/revisions', token=bob, json={
            'requestId': str(uuid.uuid4()), 'baseVersion': version, 'title': 'RUL 검증 개념', 'markdown': content})
        assert response.status_code == 201
    change(1, '동료의 두 번째 판본')
    page.get_by_role('button', name='문서 새로고침', exact=True).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_contain_text('동료의 두 번째 판본')
    page.get_by_role('button', name='변경 이력', exact=True).click()
    page.get_by_role('button', name=re.compile('^v1 · alice')).click()
    change(2, '동료의 세 번째 판본')
    page.get_by_role('button', name='이 판본으로 복구', exact=True).click()
    page.get_by_role('button', name='복구 실행', exact=True).click()
    expect(page.get_by_text('최신 문서 상태를 확인해 주세요', exact=True)).to_be_visible()
    page.get_by_role('button', name='최신 판본과 비교', exact=True).click()
    expect(page.get_by_text('동료의 세 번째 판본', exact=True)).to_be_visible()
    page.get_by_role('button', name='최신 문서 상태로 돌아가기', exact=True).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_contain_text('동료의 세 번째 판본')
    assert app.database.query('SELECT count(*) AS n FROM wiki_revisions WHERE page_id=$1', pid)[0]['n'] == 3
    expect(page.get_by_label('이전 판본', exact=True)).to_have_count(0)


def test_lost_save_acknowledgement_survives_browser_reload(browser_app):
    app = browser_app; page = app.page; login(app); seen = []
    def intercept(route):
        if route.request.method != 'POST': route.continue_(); return
        seen.append(route.request.post_data_json['requestId'])
        if len(seen) == 1:
            result = route.fetch(); assert result.status == 201
            route.abort('failed')
        else: route.continue_()
    page.route('**/api/v1/wiki/pages', intercept)
    page.get_by_role('button', name='새 위키 문서', exact=True).click()
    page.get_by_label('위키 제목', exact=True).fill('응답 유실 후 복원')
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill('같은 요청으로 확인할 내용')
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_role('button', name='같은 저장 요청 다시 확인', exact=True)).to_be_visible()
    page.once('dialog', lambda dialog: dialog.accept()); page.reload()
    page.get_by_role('button', name='공용 위키', exact=True).click()
    expect(page.get_by_label('위키 본문 (Markdown)', exact=True)).to_have_value('같은 요청으로 확인할 내용')
    assert len(seen) == 1  # Reading/reloading does not automatically resubmit.
    page.get_by_role('button', name='같은 저장 요청 다시 확인', exact=True).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_contain_text('같은 요청으로 확인할 내용')
    assert len(seen) == 2 and seen[0] == seen[1]
    assert app.database.query('SELECT count(*) AS n FROM wiki_revisions')[0]['n'] == 1
