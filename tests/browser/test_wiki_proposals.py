"""Actual Chromium/API/DB/worker; only AI and embedding providers are fixtures."""
import re
import uuid
from playwright.sync_api import expect
from test_shared_wiki import login, token, new_page


def finish(app):
    for _ in range(10):
        result=app.work()
        if result['status']=='ready':return
        assert result['status'] not in ('failed','idle'),result
    raise AssertionError('Requested proposal did not finish')


def request_form(page, instruction, context):
    page.get_by_text(re.compile('^AI에게 .* 요청$')).click()
    page.get_by_label('AI 편집 요청',exact=True).fill(instruction)
    page.get_by_label('추가할 업무 경험·내용 (선택)',exact=True).fill(context)
    page.get_by_role('button',name='AI 제안 요청',exact=True).click()
    expect(page.get_by_role('heading',name='생성 대기',exact=True)).to_be_visible()


def test_requested_new_draft_is_reviewed_before_publication(browser_app):
    app=browser_app;page=app.page;login(app)
    request_form(page,'RUL의 실무 사례 초안을 만들어 주세요.','고객 테스트에서는 저부하에서 사용했습니다.')
    assert app.database.query('SELECT count(*) n FROM wiki_pages')[0]['n']==0
    finish(app)
    expect(page.get_by_label('반영할 Markdown',exact=True)).to_be_visible()
    page.get_by_label('반영할 위키 제목',exact=True).fill('검토한 RUL 사례')
    page.get_by_label('반영할 Markdown',exact=True).fill('# RUL\n\n직원이 검토한 저부하 사례입니다.')
    page.get_by_role('button',name='검토한 내용 위키에 반영',exact=True).click()
    expect(page.get_by_label('위키 본문',exact=True)).to_contain_text('직원이 검토한 저부하 사례입니다.')
    assert app.database.query('SELECT count(*) n FROM wiki_revisions')[0]['n']==1
    assert app.database.query('SELECT ai_proposal_id FROM wiki_revisions')[0]['ai_proposal_id']
    page.reload()
    expect(page.get_by_label('위키 본문',exact=True)).to_contain_text('직원이 검토한 저부하 사례입니다.')
    assert app.database.query('SELECT count(*) n FROM wiki_proposals')[0]['n']==1


def test_stale_proposal_keeps_review_text_and_never_overwrites_colleague(browser_app):
    app=browser_app;page=app.page;login(app);pid=new_page(app)
    request_form(page,'조건을 부분 보강해 주세요.','조건부로만 적용한 사례입니다.')
    finish(app)
    expect(page.get_by_label('반영할 Markdown',exact=True)).to_be_visible()
    page.get_by_label('반영할 Markdown',exact=True).fill('직원이 보존할 검토 초안')
    bob=token(app,'bob')
    change=app.server.request('POST',f'/wiki/pages/{pid}/revisions',token=bob,json={
        'requestId':uuid.uuid4().hex,'baseVersion':1,'title':'RUL 검증 개념','markdown':'동료의 먼저 저장한 내용'})
    assert change.status_code==201
    page.get_by_role('button',name='검토한 내용 위키에 반영',exact=True).click()
    expect(page.get_by_text('대상 문서나 보호 상태가 변경됐습니다.',exact=False)).to_be_visible()
    expect(page.get_by_label('반영할 Markdown',exact=True)).to_have_value('직원이 보존할 검토 초안')
    expect(page.get_by_role('button',name='검토한 내용 위키에 반영',exact=True)).to_be_disabled()
    assert app.database.query('SELECT count(*) n FROM wiki_revisions')[0]['n']==2


def test_chat_selection_excludes_nonselected_private_text(browser_app):
    app=browser_app;page=app.page;alice=token(app,'alice')
    c=app.server.request('POST','/conversations',token=alice,json={'title':'선택 전달 테스트'}).json()['id']
    app.server.request('POST',f'/conversations/{c}/messages',token=alice,json={'content':'PRIVATE_NOT_FOR_WIKI_919\n고객의 저부하 사례입니다.'})
    login(app)
    page.get_by_role('button',name=re.compile('^선택 전달 테스트')).click()
    page.get_by_role('button',name='선택해서 위키 제안',exact=True).click()
    modal=page.get_by_role('dialog',name='선택 대화로 위키 제안')
    modal.get_by_label('AI 편집 요청',exact=True).fill('선택한 경험으로 개념 초안을 만들어 주세요.')
    modal.get_by_label('위키 반영 요청에 포함할 선택 문장',exact=True).fill('고객의 저부하 사례입니다.')
    modal.get_by_role('checkbox').check()
    modal.get_by_role('button',name='AI 제안 요청',exact=True).click()
    expect(modal.get_by_role('heading',name='생성 대기',exact=True)).to_be_visible()
    finish(app)
    expect(modal.get_by_label('반영할 Markdown',exact=True)).not_to_contain_text('PRIVATE_NOT_FOR_WIKI_919')
    expect(modal.get_by_label('반영할 Markdown',exact=True)).to_have_value(re.compile('고객의 저부하 사례'))
    modal.get_by_role('button',name='검토한 내용 위키에 반영',exact=True).click()
    expect(modal.get_by_role('heading',name='반영 완료',exact=True)).to_be_visible()
    assert 'PRIVATE_NOT_FOR_WIKI_919' not in str(app.database.query('SELECT input,result FROM wiki_proposals'))
    assert 'PRIVATE_NOT_FOR_WIKI_919' not in app.database.query('SELECT markdown FROM wiki_revisions')[0]['markdown']
