"""Browser + PostgreSQL manual wiki workflow. Wiki operations never call a provider."""
import re
import uuid
from playwright.sync_api import expect


def login(app, name='alice'):
    page = app.page; page.goto(app.url)
    page.get_by_label('아이디', exact=True).fill(name)
    page.get_by_label('비밀번호', exact=True).fill(app.environment['OW_BOOTSTRAP_PASSWORD'])
    page.get_by_role('button', name='로그인', exact=True).click()
    page.get_by_role('button', name='공용 위키', exact=True).click()


def new_page(app, title='RUL 검증 개념'):
    page = app.page
    page.get_by_role('button', name='새 위키 문서', exact=True).click()
    page.get_by_label('위키 제목', exact=True).fill(title)
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill('# 정의\n\n원래 설명입니다.\n')
    page.get_by_label('근거·업무 맥락 (선택)', exact=True).fill('합성 프로젝트 경험 기록')
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_text('판본 1이 저장되었습니다.', exact=True)).to_be_visible()
    return app.database.query('SELECT id FROM wiki_pages')[0]['id']


def token(app, name='alice'):
    return app.server.request('POST', '/auth/login', json={'username': name,
        'password': app.environment['OW_BOOTSTRAP_PASSWORD']}).json()['accessToken']


def test_shared_edit_history_restore_and_admin_lock(browser_app):
    app = browser_app; page = app.page; login(app); pid = new_page(app)
    page.get_by_role('button', name='로그아웃', exact=True).click(); login(app, 'bob')
    page.get_by_role('button', name=re.compile('^RUL 검증 개념')).click()
    page.get_by_role('button', name='문서 편집', exact=True).click()
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill('# 정의\n\n동료가 보강한 내용입니다.\n')
    page.get_by_label('변경 요약 (선택)', exact=True).fill('업무 조건 보강')
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_text('판본 2이 저장되었습니다.', exact=True)).to_be_visible()
    page.get_by_role('button', name='변경 이력', exact=True).click()
    page.get_by_role('button', name=re.compile('^v1 · alice')).click()
    expect(page.get_by_label('이전 판본', exact=True)).to_contain_text('원래 설명입니다.')
    expect(page.locator('.wiki-diff')).to_contain_text('동료가 보강한 내용')
    page.get_by_role('button', name='이 판본으로 복구', exact=True).click()
    page.get_by_role('button', name='복구 실행', exact=True).click()
    expect(page.get_by_text('판본 3이 저장되었습니다.', exact=True)).to_be_visible()
    assert app.database.query('SELECT count(*) AS n FROM wiki_revisions WHERE page_id=$1', pid)[0]['n'] == 3
    page.reload(); page.get_by_role('button', name='공용 위키', exact=True).click()
    page.get_by_role('button', name=re.compile('^RUL 검증 개념')).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_contain_text('원래 설명입니다.')
    page.get_by_role('button', name='로그아웃', exact=True).click(); login(app, 'operator')
    page.get_by_role('button', name=re.compile('^RUL 검증 개념')).click()
    page.get_by_role('button', name='문서 보호', exact=True).click()
    page.get_by_role('button', name='보호 변경 실행', exact=True).click()
    expect(page.get_by_text('관리자가 문서를 보호했습니다.', exact=True)).to_be_visible()
    page.get_by_role('button', name='로그아웃', exact=True).click(); login(app, 'alice')
    page.get_by_role('button', name=re.compile('^RUL 검증 개념')).click()
    expect(page.get_by_role('button', name='문서 편집', exact=True)).to_have_count(0)
    expect(page.get_by_role('button', name='문서 보호 해제', exact=True)).to_have_count(0)
    page.get_by_role('button', name='변경 이력', exact=True).click()
    page.get_by_role('button', name=re.compile('^v1 · alice')).click()
    expect(page.get_by_role('button', name='이 판본으로 복구', exact=True)).to_have_count(0)
    assert app.database.query('SELECT is_locked FROM wiki_pages WHERE id=$1', pid)[0]['is_locked']
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')


def test_conflict_keeps_draft_and_shows_latest_without_overwriting(browser_app):
    app = browser_app; page = app.page; login(app); pid = new_page(app)
    page.get_by_role('button', name='문서 편집', exact=True).click()
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill('보존해야 할 내 초안')
    bob = token(app, 'bob')
    changed = app.server.request('POST', f'/wiki/pages/{pid}/revisions', token=bob, json={
        'requestId': str(uuid.uuid4()), 'baseVersion': 1, 'title': 'RUL 검증 개념', 'markdown': '먼저 저장한 동료의 변경'})
    assert changed.status_code == 201
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_text('입력을 보존했습니다', exact=True)).to_be_visible()
    expect(page.get_by_label('위키 본문 (Markdown)', exact=True)).to_have_value('보존해야 할 내 초안')
    page.get_by_role('button', name='최신 판본과 비교', exact=True).click()
    expect(page.get_by_text('먼저 저장한 동료의 변경', exact=True)).to_be_visible()
    expect(page.get_by_role('button', name='위키 저장', exact=True)).to_be_disabled()
    assert app.database.query('SELECT count(*) AS n FROM wiki_revisions WHERE page_id=$1', pid)[0]['n'] == 2
    page.get_by_role('button', name='최신 판본 확인 후 편집 계속', exact=True).click()
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill('먼저 저장한 동료의 변경\n보존해야 할 내 초안')
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_text('판본 3이 저장되었습니다.', exact=True)).to_be_visible()


def test_lost_save_response_resends_same_request_and_safe_preview(browser_app):
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
    page.get_by_label('위키 제목', exact=True).fill('안전한 저장')
    text = '# 개념\n\n<script>window.wikiInjected=true</script>\n\n[위험](javascript:alert(1))\n\n![추적](https://example.org/image)'
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill(text)
    page.get_by_role('button', name='Markdown 미리보기', exact=True).click()
    expect(page.locator('.wiki-preview script, .wiki-preview img, .wiki-preview a')).to_have_count(0)
    assert page.evaluate('window.wikiInjected') is None
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_role('button', name='같은 저장 요청 다시 확인', exact=True)).to_be_visible()
    page.get_by_role('button', name='같은 저장 요청 다시 확인', exact=True).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_be_visible()
    assert len(seen) == 2 and seen[0] == seen[1]
    assert app.database.query('SELECT count(*) AS n FROM wiki_pages')[0]['n'] == 1
    assert app.database.query('SELECT count(*) AS n FROM wiki_revisions')[0]['n'] == 1
    assert app.database.query('SELECT markdown FROM wiki_revisions')[0]['markdown'] == text
