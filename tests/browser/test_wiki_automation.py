"""Document upload -> automatic draft -> human review -> links -> chat -> export. Fixture models."""
import json
import re
from pathlib import Path
from uuid import uuid4
import pytest
from playwright.sync_api import expect
from test_workspace import login, upload_ui, ask, answer
from test_shared_wiki import token

pytestmark = pytest.mark.parametrize('browser_app', [True], indirect=True)


def drain(app):
    for _ in range(20):
        result=app.work()
        assert result['status']!='failed',result
        if result['status']=='idle': return
    raise AssertionError('Unbounded automatic work')


def test_upload_automatically_proposes_then_links_chat_and_exports(browser_app):
    app=browser_app;page=app.page;alice=token(app,'alice')
    ref=app.server.request('POST','/wiki/pages',token=alice,json={'requestId':uuid4().hex,
        'title':'상태 모니터링','markdown':'# 상태 모니터링\n\n설비 상태를 관찰합니다.'})
    assert ref.status_code==201;ref_id=ref.json()['pageId']
    login(app)
    upload_ui(app,title='RULStage5Source',body=b'# RULStage5Source\n\nRULStage5Source uses only low-load laboratory conditions.\n')
    drain(app)
    notice=page.get_by_label('문헌의 위키 보강 안내',exact=True)
    expect(notice.get_by_role('status')).to_contain_text('확인할 제안 1건',timeout=20000)
    assert app.database.query('SELECT count(*) n FROM wiki_pages')[0]['n']==1
    notice.get_by_role('button',name='위키 보강 제안 확인',exact=True).click()
    notice.get_by_role('button',name=re.compile('^문헌 자동 제안 · 직원 확인 필요')).click()
    expect(notice.get_by_label('반영할 Markdown',exact=True)).to_be_visible()
    expect(notice).to_contain_text('RULStage5Source uses only low-load laboratory conditions.')
    reviewed='# RULStage5Source\n\nRULStage5Source customer maintenance depends on low-load conditions.\n\n[상태 모니터링](/wiki/'+ref_id+')으로 이어서 확인합니다.\n'
    notice.get_by_label('반영할 위키 제목',exact=True).fill('RULStage5Source')
    notice.get_by_label('반영할 Markdown',exact=True).fill(reviewed)
    notice.get_by_role('button',name='검토한 내용 위키에 반영',exact=True).click()
    expect(notice.get_by_role('heading',name='반영 완료',exact=True)).to_be_visible()
    drain(app)
    pid=app.database.query("SELECT page_id FROM wiki_revisions WHERE ai_proposal_id IS NOT NULL")[0]['page_id']
    notice.get_by_role('link',name='반영한 위키 열기',exact=True).click()
    body=page.get_by_label('위키 본문',exact=True)
    expect(body).to_contain_text('customer maintenance')
    body.get_by_role('link',name='상태 모니터링',exact=True).click()
    expect(page.get_by_label('위키 본문',exact=True)).to_contain_text('설비 상태를 관찰합니다.')
    page.go_back()
    expect(page.get_by_label('위키 본문',exact=True)).to_contain_text('customer maintenance')
    with page.expect_download() as downloaded:
        page.get_by_role('button',name='Markdown 받기',exact=True).click()
    assert Path(downloaded.value.path()).read_bytes()==reviewed.encode()
    ask(page,'Explain RULStage5Source customer maintenance and laboratory conditions.')
    card=answer(page)
    data=app.database.query("SELECT citations FROM messages WHERE role='assistant' ORDER BY created_at DESC")[0]['citations']
    citations=json.loads(data) if isinstance(data,str) else data
    assert {c['sourceKind'] for c in citations}=={'document','wiki'}
    for kind in ('wiki','document'):
        c=next(c for c in citations if c['sourceKind']==kind)
        card.get_by_role('button',name=f"출처 {c['number']}: {c['title']}",exact=True).click()
        expect(page.get_by_label('원문 패널',exact=True)).to_be_visible()
        expect(page.get_by_test_id('evidence-passage')).to_be_visible()
        page.get_by_role('button',name='원문 닫기',exact=True).click()
    ask(page,'What are the restrictions on RULStage5Source?',new=False)
    expect(page.get_by_test_id('message-assistant')).to_have_count(2);answer(page)
    # Switching from a permalink to chat must also update the browser route.
    expect(page).to_have_url(app.url + '/')
    page.reload();answer(page)
    expect(page.get_by_test_id('message-assistant')).to_have_count(2)
    page.get_by_role('button', name='공용 문헌', exact=True).click()
    expect(page).to_have_url(app.url + '/documents')
    page.reload()
    expect(page.get_by_role('button', name='공용 문헌', exact=True)).to_have_attribute('aria-current', 'page')
    assert app.database.query('SELECT count(*) n FROM wiki_document_jobs')[0]['n']==1
    assert app.database.query('SELECT count(*) n FROM wiki_proposals')[0]['n']==1
    assert app.server.request('GET',f'/wiki/pages/{pid}/markdown',token=alice).text==reviewed


def test_another_employee_reviews_shared_source_but_not_private_request(browser_app):
    app=browser_app;page=app.page;alice=token(app,'alice')
    private=app.server.request('POST','/wiki/proposals',token=alice,json={'requestId':uuid4().hex,
        'mode':'create','instruction':'PRIVATE_TEST_ONLY','contextText':'Private requested idea'})
    assert private.status_code==202
    login(app);upload_ui(app,title='PublicAutoSource')
    drain(app)
    page.get_by_role('button',name='로그아웃',exact=True).click();login(app,'bob')
    page.get_by_role('button',name='공용 문헌',exact=True).click()
    page.get_by_role('button',name=re.compile('^PublicAutoSource')).click()
    notice=page.get_by_label('문헌의 위키 보강 안내',exact=True)
    expect(notice.get_by_role('status')).to_contain_text('확인할 제안 1건')
    notice.get_by_role('button',name='위키 보강 제안 확인',exact=True).click()
    notice.get_by_role('button',name=re.compile('^문헌 자동 제안 · 직원 확인 필요')).click()
    expect(notice.get_by_label('반영할 Markdown',exact=True)).to_be_visible()
    expect(notice).not_to_contain_text('PRIVATE_TEST_ONLY')
    notice.get_by_role('button',name='이 제안 무시',exact=True).click()
    expect(notice.get_by_role('heading',name='무시함',exact=True)).to_be_visible()
    assert app.database.query('SELECT count(*) n FROM wiki_pages')[0]['n']==0
