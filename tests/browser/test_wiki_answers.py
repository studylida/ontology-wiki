"""Real UI/HTTP/DB mixed-source answers and exact Markdown downloads. Models are fixtures."""
import json
import re
from pathlib import Path
from uuid import uuid4
from playwright.sync_api import expect
from test_workspace import login, ask, answer


def seed(app):
    token = app.server.request('POST', '/auth/login', json={'username': 'alice', 'password': app.environment['OW_BOOTSTRAP_PASSWORD']}).json()['accessToken']
    markdown = '# Alpha concept\n\nAlpha customer experience applies to maintenance planning. This synthetic example is not company policy.\n'
    wiki = app.server.request('POST', '/wiki/pages', token=token, json={'requestId': uuid4().hex,
        'title': 'Alpha concept', 'markdown': markdown, 'sourceNote': '합성 직원 경험. 독립 검증 근거 아님.'})
    assert wiki.status_code == 201
    doc = app.server.request('POST', '/documents', token=token, data={'title': 'Alpha reference'},
        files={'file': ('reference.md', b'# Alpha reference\n\nAlpha laboratory tests used 250 C under controlled load.\n', 'text/markdown')})
    assert doc.status_code == 202
    for _ in range(6):
        if app.work()['status'] == 'idle': break
    return token, wiki.json(), doc.json(), markdown


def test_mixed_chat_citations_historical_source_and_markdown_download(browser_app):
    app = browser_app; page = app.page
    token, wiki, doc, markdown = seed(app)
    login(app)
    ask(page, 'Explain alpha customer maintenance context and laboratory conditions.')
    card = answer(page)
    data = app.database.query("SELECT citations FROM messages WHERE role='assistant' ORDER BY created_at DESC")[0]['citations']
    citations = json.loads(data) if isinstance(data, str) else data
    wc = next(c for c in citations if c['sourceKind'] == 'wiki')
    dc = next(c for c in citations if c['sourceKind'] == 'document')
    card.get_by_role('button', name=f"출처 {wc['number']}: {wc['title']}", exact=True).click()
    panel = page.get_by_label('원문 패널', exact=True)
    expect(panel).to_contain_text('공용 위키 · 직원이 편집한 지식')
    expect(page.get_by_test_id('evidence-passage')).to_contain_text('customer experience')
    expect(panel.get_by_role('button', name='원본 파일 받기', exact=True)).to_have_count(0)
    with page.expect_download() as downloaded:
        panel.get_by_role('button', name='이 판본 Markdown 받기', exact=True).click()
    assert Path(downloaded.value.path()).read_bytes() == markdown.encode()
    changed = app.server.request('POST', f"/wiki/pages/{wiki['pageId']}/revisions", token=token, json={
        'requestId': uuid4().hex, 'baseVersion': 1, 'title': 'Alpha renamed', 'markdown': 'New alpha knowledge.\n'})
    assert changed.status_code == 201
    page.reload(); card = answer(page)
    expect(card).to_contain_text('과거 판본을 사용한 답변')
    card.get_by_role('button', name=f"출처 {wc['number']}: {wc['title']}", exact=True).click()
    panel = page.get_by_label('원문 패널', exact=True)
    expect(panel).to_contain_text('인용한 판본을 그대로 표시')
    expect(page.get_by_test_id('evidence-passage')).to_contain_text('customer experience')
    page.get_by_role('button', name='원문 닫기', exact=True).click()
    card.get_by_role('button', name=f"출처 {dc['number']}: {dc['title']}", exact=True).click()
    expect(page.get_by_label('원문 패널', exact=True)).to_contain_text('원본 문헌')
    expect(page.get_by_role('button', name='원본 파일 받기', exact=True)).to_be_visible()
    page.get_by_role('button', name='원문 닫기', exact=True).click()
    assert app.work()['status'] == 'succeeded'
    ask(page, 'Explain the updated alpha knowledge.', new=False)
    expect(page.get_by_test_id('message-assistant')).to_have_count(2)
    answer(page)
    page.reload(); answer(page)
    assert app.database.query('SELECT count(*) n FROM answer_runs')[0]['n'] == 2
    # Only saved wiki content is public; no implicit chat-to-wiki writes.
    assert app.database.query('SELECT count(*) n FROM wiki_revisions')[0]['n'] == 2
    page.get_by_role('button', name='로그아웃', exact=True).click(); login(app, 'bob')
    expect(page.get_by_label('내 대화 목록', exact=True).get_by_role('button')).to_have_count(0)


def test_wiki_page_exports_selected_revision_without_models(browser_app):
    app = browser_app; page = app.page
    _, wiki, _, markdown = seed(app)
    login(app)
    page.get_by_role('button', name='공용 위키', exact=True).click()
    page.get_by_role('button', name=re.compile('^Alpha concept')).click()
    expect(page.get_by_label('위키 본문', exact=True)).to_contain_text('customer experience')
    with page.expect_download() as downloaded:
        page.get_by_role('button', name='Markdown 받기', exact=True).click()
    assert Path(downloaded.value.path()).read_bytes() == markdown.encode()
    assert wiki['revisionId'] in downloaded.value.suggested_filename
    assert app.database.query('SELECT count(*) n FROM answer_runs')[0]['n'] == 0
