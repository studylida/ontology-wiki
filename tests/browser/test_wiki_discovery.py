"""Real UI + DB wiki navigation and index states. Provider calls are fixtures."""
import json
import re
import subprocess
import sys
import uuid
from playwright.sync_api import expect
from test_shared_wiki import login, token


def create(app, title, markdown='본문', **extra):
    response = app.server.request('POST', '/wiki/pages', token=token(app), json={
        'requestId': str(uuid.uuid4()), 'title': title, 'markdown': markdown, **extra})
    assert response.status_code == 201, response.text
    return response.json()['pageId']


def test_stored_links_survive_rename_and_disambiguation_is_contextual(browser_app):
    app = browser_app; page = app.page
    target = create(app, '예지보전', '정비 시점을 판단하는 활용 분야')
    origin = create(app, 'RUL 연결', f'잔여 수명을 설명하며 [예지보전](/wiki/{target})을 참고합니다.')
    other = create(app, 'CMP 소프트웨어', aliases=['CMP'], meaning='합성 프로젝트의 약어')
    process = create(app, 'CMP 공정', aliases=['CMP'], meaning='웨이퍼 평탄화 공정')
    login(app)
    page.get_by_role('button', name=re.compile('^RUL 연결')).click()
    page.get_by_label('위키 본문', exact=True).get_by_role('link', name='예지보전').click()
    expect(page.get_by_role('heading', name='예지보전', exact=True)).to_be_visible()
    changed = app.server.request('POST', f'/wiki/pages/{target}/revisions', token=token(app), json={
        'requestId': str(uuid.uuid4()), 'baseVersion': 1, 'title': '예지보전 새 이름', 'markdown': '제목만 바꾼 예시'})
    assert changed.status_code == 201
    page.go_back()
    expect(page.get_by_role('heading', name='RUL 연결', exact=True)).to_be_visible()
    page.get_by_label('위키 본문', exact=True).get_by_role('link', name='예지보전').click()
    expect(page.get_by_role('heading', name='예지보전 새 이름', exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_role('heading', name='예지보전 새 이름', exact=True)).to_be_visible()
    page.get_by_role('button', name=re.compile('^CMP 공정')).click()
    hint = page.get_by_label('다른 의미 안내', exact=True)
    expect(hint).to_contain_text('CMP 소프트웨어')
    hint.get_by_role('button', name='CMP 소프트웨어', exact=True).click()
    expect(page.get_by_role('heading', name='CMP 소프트웨어', exact=True)).to_be_visible()
    assert app.database.query('SELECT markdown FROM wiki_revisions WHERE page_id=$1', origin)[0]['markdown'].endswith(f'(/wiki/{target})을 참고합니다.')


def test_similarity_notice_does_not_block_creation_or_lose_draft(browser_app):
    app = browser_app; page = app.page
    existing = create(app, 'RUL', '## 개념\n\n잔여 수명 예측', aliases=['잔여 수명'], meaning='설비의 잔여 수명')
    assert app.work()['status'] == 'succeeded'
    login(app)
    page.get_by_role('button', name='새 위키 문서', exact=True).click()
    page.get_by_label('위키 제목', exact=True).fill('RUL')
    page.get_by_label('위키 본문 (Markdown)', exact=True).fill('## 다른 관점\n\n잔여 수명에 관한 별도 설명')
    page.get_by_label('다른 이름·약어 (선택 · 한 줄에 하나)', exact=True).fill('Remaining Useful Life')
    page.get_by_label('이 개념의 뜻·구분 (선택)', exact=True).fill('추가 업무 사례')
    panel = page.get_by_label('비슷한 위키 안내', exact=True)
    panel.get_by_role('button', name='비슷한 위키 문서 확인', exact=True).click()
    expect(panel.get_by_role('link', name='기존 문서 확인·보강 (새 탭)', exact=True)).to_be_visible()
    expect(page.get_by_label('위키 본문 (Markdown)', exact=True)).to_have_value('## 다른 관점\n\n잔여 수명에 관한 별도 설명')
    page.get_by_role('button', name='위키 저장', exact=True).click()
    expect(page.get_by_label('위키 검색 준비와 이름 안내')).to_contain_text('색인 대기')
    assert app.database.query('SELECT count(*) n FROM wiki_pages')[0]['n'] == 2
    assert app.work()['status'] == 'succeeded'
    expect(page.get_by_label('위키 검색 준비와 이름 안내')).to_contain_text('검색 사용 가능', timeout=10000)
    query = page.get_by_label('위키 내용 검색', exact=True)
    query.get_by_label('개념·내용 검색', exact=True).fill('잔여 수명')
    query.get_by_role('button', name='키워드·의미 검색', exact=True).click()
    expect(query).to_contain_text('키워드 + 의미 검색')
    expect(query.locator('.wiki-search-hit')).to_have_count(2)


def test_failed_index_does_not_hide_saved_body_and_retry_is_explicit(browser_app):
    app = browser_app; page = app.page
    pid = create(app, '색인 재시도', '# 개념\n\n저장된 위키 내용')
    result = subprocess.run([sys.executable, '-m', 'knowledge.cli', 'worker', '--once'],
        env={**app.environment, 'OW_PROVIDER_MODE': 'disabled'}, capture_output=True, text=True, timeout=40)
    assert result.returncode == 0 and json.loads(result.stdout)['status'] == 'failed'
    login(app); page.get_by_role('button', name=re.compile('^색인 재시도')).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_contain_text('저장된 위키 내용')
    panel = page.get_by_label('위키 검색 준비와 이름 안내')
    expect(panel).to_contain_text('색인 실패')
    panel.get_by_role('button', name='위키 색인 재시도', exact=True).click()
    expect(panel).to_contain_text('색인 대기')
    assert app.work()['status'] == 'succeeded'
    expect(panel).to_contain_text('검색 사용 가능', timeout=10000)
    assert app.database.query('SELECT count(*) n FROM wiki_revisions WHERE page_id=$1',pid)[0]['n'] == 1
