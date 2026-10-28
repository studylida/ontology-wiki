"""Browser restoration and source withdrawal use the same real services as uploads."""
import re
from playwright.sync_api import expect
from test_workspace import login, seed, ask, answer


def test_refresh_during_generation_does_not_submit_another_question(browser_app):
    app = browser_app; seed(app); login(app); page = app.page
    posts = []
    page.on('request', lambda request: posts.append(request.url)
        if request.method == 'POST' and request.url.endswith('/turns') else None)
    ask(page)
    expect(page.get_by_role('button', name='답변 중단', exact=True)).to_be_visible()
    page.reload()
    answer(page)
    expect(page.get_by_test_id('message-user')).to_have_count(1)
    assert len(posts) == 1
    assert app.database.query('SELECT count(*) AS n FROM answer_runs')[0]['n'] == 1
    assert app.database.query("SELECT count(*) AS n FROM messages WHERE role='user'")[0]['n'] == 1


def test_source_deactivation_is_reflected_in_restored_chat(browser_app):
    app = browser_app; seed(app); login(app); page = app.page
    ask(page); card = answer(page)
    card.get_by_role('button', name=re.compile('^출처 ')).first.click()
    expect(page.get_by_test_id('evidence-passage')).to_be_visible()
    page.get_by_role('button', name='원문 닫기', exact=True).click()
    page.get_by_role('button', name='공용 문헌', exact=True).click()
    page.get_by_role('button', name=re.compile('^Reference')).click()
    page.get_by_role('button', name='문헌 비활성화', exact=True).click()
    page.get_by_role('button', name='비활성화 실행', exact=True).click()
    expect(page.get_by_text('서버에서 문헌을 비활성화했습니다.')).to_be_visible()
    page.get_by_role('button', name='대화', exact=True).click()
    expect(page.get_by_text('근거 문헌을 현재 사용할 수 없어 답변과 출처를 숨겼습니다.')).to_be_visible()
    expect(page.get_by_test_id('message-assistant').get_by_role('button', name=re.compile('^출처 '))).to_have_count(0)
    assert app.database.query('SELECT withdrawn FROM documents')[0]['withdrawn']
    page.reload()
    expect(page.get_by_text('근거 문헌을 현재 사용할 수 없어 답변과 출처를 숨겼습니다.')).to_be_visible()
