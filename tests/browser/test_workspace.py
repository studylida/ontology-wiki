"""Synthetic documents; fixture models. No business accuracy claim."""
import json
import re
from pathlib import Path
from playwright.sync_api import expect

TEXT = b'# Reference\n\n## Alpha conditions\n\nThe sample uses alpha material at 250 C. These are synthetic test conditions, not company policy.\n\n## Result\n\nThe measured result applies only to these conditions. No company decision is implied.\n'

def login(app, username='alice'):
    page = app.page; page.goto(app.url)
    page.get_by_label('아이디', exact=True).fill(username)
    page.get_by_label('비밀번호', exact=True).fill(app.environment['OW_BOOTSTRAP_PASSWORD'])
    page.get_by_role('button', name='로그인', exact=True).click()
    expect(page.get_by_role('button', name='로그아웃', exact=True)).to_be_visible()


def upload_ui(app, title='Browser reference', body=TEXT, filename='reference.md'):
    page = app.page
    page.get_by_role('button', name='공용 문헌', exact=True).click()
    expect(page.get_by_text('회사 전체 직원이 검색하고 활용하는 공용 자료입니다.')).to_be_visible()
    page.get_by_label('문헌 제목 (선택)', exact=True).fill(title)
    page.get_by_label('문헌 파일', exact=True).set_input_files({'name': filename, 'mimeType': 'application/octet-stream', 'buffer': body})
    page.get_by_role('button', name='공용 문헌 업로드', exact=True).click()
    item = page.get_by_role('button', name=re.compile(title))
    expect(item).to_be_visible(); return item


def seed(app):
    token = app.server.request('POST', '/auth/login', json={'username': 'alice', 'password': app.environment['OW_BOOTSTRAP_PASSWORD']}).json()['accessToken']
    result = app.server.request('POST', '/documents', token=token, data={'title': 'Reference'}, files={'file': ('reference.md', TEXT, 'text/markdown')})
    assert result.status_code == 202
    assert app.work()['status'] == 'succeeded'


def ask(page, question='Explain alpha material conditions', new=True):
    if new: page.get_by_role('button', name='새 대화', exact=True).click()
    expect(page.get_by_label('업무 질문', exact=True)).to_be_enabled()
    page.get_by_label('업무 질문', exact=True).fill(question)
    page.get_by_role('button', name='질문 보내기', exact=True).click()


def answer(page, status='완료'):
    card = page.get_by_test_id('message-assistant').last
    expect(card.get_by_role('status')).to_have_text(status, timeout=20000)
    return card


def test_upload_question_citation_followup_refresh_and_private_ownership(browser_app):
    app = browser_app; page = app.page; login(app)
    item = upload_ui(app)
    expect(item).to_contain_text('처리 대기')
    assert app.database.query('SELECT count(*) AS n FROM passages')[0]['n'] == 0
    assert app.work()['status'] == 'succeeded'
    expect(item).to_contain_text('사용 가능')
    ask(page); card = answer(page)
    expect(card).to_contain_text('검증용 fixture')
    saved = app.database.query("SELECT citations FROM messages WHERE role='assistant'")[0]['citations']
    citations = json.loads(saved) if isinstance(saved, str) else saved
    assert citations and app.database.query('SELECT id FROM passages WHERE id=$1', citations[0]['passageId'])
    card.get_by_role('button', name=re.compile('^출처 ')).first.click()
    panel = page.get_by_label('원문 패널', exact=True)
    expect(panel).to_be_visible(); expect(page.get_by_test_id('evidence-passage')).to_contain_text(citations[0]['locator'])
    # The source itself may contain h2 headings; select the panel's named heading.
    expect(panel.get_by_role('heading', level=2, name=f"출처 [{citations[0]['number']}]", exact=True)).to_be_visible()
    with page.expect_download() as download:
        page.get_by_role('button', name='원본 파일 받기', exact=True).click()
    assert Path(download.value.path()).read_bytes() == TEXT
    page.get_by_role('button', name='원문 닫기', exact=True).click()
    ask(page, 'What about the result under those conditions?', new=False); answer(page)
    expect(page.get_by_test_id('message-assistant')).to_have_count(2)
    before = page.get_by_test_id('message-assistant').last.inner_text()
    page.reload(); answer(page)
    expect(page.get_by_test_id('message-assistant')).to_have_count(2)
    assert page.get_by_test_id('message-assistant').last.inner_text() == before
    assert app.database.query('SELECT count(*) AS n FROM answer_runs')[0]['n'] == 2
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.get_by_role('button', name='로그아웃', exact=True).click(); login(app, 'bob')
    expect(page.get_by_label('내 대화 목록', exact=True).get_by_role('button')).to_have_count(0)
    page.get_by_role('button', name='공용 문헌', exact=True).click()
    page.get_by_role('button', name=re.compile('Browser reference')).click()
    expect(page.get_by_text('검색에 사용하는 판본: 1')).to_be_visible()
    expect(page.get_by_role('button', name='재처리 요청', exact=True)).to_have_count(0)
    expect(page.get_by_test_id('message-assistant')).to_have_count(0)


def test_cancel_and_explicit_retry_keep_one_user_question(browser_app):
    app = browser_app; seed(app); login(app); page = app.page
    ask(page)
    stop = page.get_by_role('button', name='답변 중단', exact=True)
    expect(stop).to_be_enabled(); stop.click(); answer(page, '취소됨')
    page.get_by_role('button', name='답변 다시 생성', exact=True).click(); answer(page)
    assert app.database.query("SELECT count(*) AS n FROM messages WHERE role='user'")[0]['n'] == 1
    assert app.database.query('SELECT count(*) AS n FROM answer_runs')[0]['n'] == 2


def test_lost_submission_response_resends_same_id(browser_app):
    app = browser_app; seed(app); login(app); page = app.page; seen = []
    def lose_first_response(route):
        seen.append(route.request.post_data_json['requestId'])
        if len(seen) == 1:
            response = route.fetch(); assert response.status == 202
            route.abort('failed')
        else: route.continue_()
    page.route('**/conversations/*/turns', lose_first_response)
    ask(page)
    expect(page.get_by_text('전송 결과 확인이 필요합니다.')).to_be_visible()
    page.get_by_role('button', name='같은 요청 다시 전송', exact=True).click(); answer(page)
    assert len(seen) == 2 and seen[0] == seen[1]
    assert app.database.query('SELECT count(*) AS n FROM answer_runs')[0]['n'] == 1
    page.reload(); answer(page)
    assert len(seen) == 2


def test_disconnection_is_not_success_and_real_storage_failure_can_retry(browser_app):
    app = browser_app; seed(app); login(app); page = app.page
    pattern = re.compile(r'/api/v1/answer-runs/[^/?]+(?:/events.*)?$')
    def block_reads(route):
        if route.request.method == 'GET': route.abort('failed')
        else: route.continue_()
    page.route(pattern, block_reads)
    ask(page)
    expect(page.get_by_role('button', name='저장된 실행 다시 연결', exact=True)).to_be_visible(timeout=20000)
    assert page.get_by_test_id('message-assistant').last.get_by_role('status').inner_text() != '완료'
    page.unroute(pattern, block_reads)
    page.get_by_role('button', name='저장된 실행 다시 연결', exact=True).click(); answer(page)
    assert app.database.query('SELECT count(*) AS n FROM answer_runs')[0]['n'] == 1
    app.database.execute("""CREATE FUNCTION browser_reject_complete() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN IF NEW.role='assistant' AND NEW.status='completed' THEN RAISE EXCEPTION 'browser fixture persistence failure'; END IF; RETURN NEW; END $$;
      CREATE TRIGGER browser_completion_failure BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION browser_reject_complete();""")
    ask(page, 'Explain the result', new=False); answer(page, '실패')
    app.database.execute('DROP TRIGGER browser_completion_failure ON messages; DROP FUNCTION browser_reject_complete()')
    page.get_by_role('button', name='답변 다시 생성', exact=True).click(); answer(page)
    assert app.database.query("SELECT count(*) AS n FROM messages WHERE role='user'")[0]['n'] == 2
    assert app.database.query('SELECT count(*) AS n FROM answer_runs')[0]['n'] == 3


def test_operational_reprocess_and_deactivate_are_real_requests(browser_app):
    app = browser_app; login(app); page = app.page
    item = upload_ui(app, 'Broken text fixture', b'\xff\xfe', 'broken.txt')
    assert app.work()['status'] == 'failed'
    expect(item).to_contain_text('처리 실패')
    page.get_by_role('button', name='재처리 요청', exact=True).click()
    expect(item).to_contain_text('처리 대기')
    assert app.database.query('SELECT status FROM processing_jobs')[0]['status'] == 'pending'
    assert app.work()['status'] == 'failed'
    expect(item).to_contain_text('처리 실패')
    page.get_by_role('button', name='문헌 비활성화', exact=True).click()
    page.get_by_role('button', name='비활성화 실행', exact=True).click()
    expect(item).to_contain_text('비활성')
    assert app.database.query('SELECT withdrawn FROM documents')[0]['withdrawn']
    expect(page.get_by_role('button', name='최신 판본 원문 확인', exact=True)).to_have_count(0)
