"""Real files, PostgreSQL, API and worker processes. Only embeddings are fixtures."""
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import pytest
from conftest import ROOT, Server, cli

TEXT = b'# Reference\n\n## Conditions\n\nThe sample uses alpha material at 250 C.\n\n## Result\n\nThe measured result applies only to the stated conditions.\n'


@pytest.fixture
def documents_app(database_factory,tmp_path):
    with database_factory() as database:
        environment = {**os.environ,'PYTHONPATH':str(ROOT/'backend'),'OW_DATABASE_URL':database.url,
            'OW_AUTH_SECRET':secrets.token_hex(32),'OW_BOOTSTRAP_PASSWORD':secrets.token_urlsafe(24),
            'OW_PROVIDER_MODE':'fixture','OW_STORAGE_PATH':str(tmp_path/'raw'),
            'OW_PDF_PARSER':'legacy','OW_DOCLING_PYTHON_PATH':'','OW_DOCLING_OCR':'false'}
        environment.pop('OPENAI_API_KEY',None)
        cli(environment,'migrate','--database-name',database.name)
        for name,role in (('alice','user'),('bob','user'),('operator','admin')):
            cli(environment,'create-user','--username',name,'--role',role)
        server = Server(environment,tmp_path)
        try:
            server.start()
            tokens = {}
            for name in ('alice','bob','operator'):
                response = server.request('POST','/auth/login',json={'username':name,'password':environment['OW_BOOTSTRAP_PASSWORD']})
                assert response.status_code == 200,response.text
                tokens[name] = response.json()['accessToken']
            yield SimpleNamespace(server=server,database=database,environment=environment,tokens=tokens,directory=tmp_path)
        finally:
            server.stop()


def upload(app,body=TEXT,filename='sample.md',title='Reference',document_id=None,user='alice',expect=202):
    path = f'/documents/{document_id}/revisions' if document_id else '/documents'
    response = app.server.request('POST',path,token=app.tokens[user],
        data={'title':title},files={'file':(filename,body,'application/octet-stream')})
    assert response.status_code == expect,response.text
    return response.json()


def detail(app,document_id,user='alice'):
    response = app.server.request('GET','/documents/'+document_id,token=app.tokens[user])
    assert response.status_code == 200,response.text
    return response.json()


def work(app,**env):
    return json.loads(cli({**app.environment,**env},'worker','--once').stdout)


def action(app,document_id,operation,user='alice',expect=202):
    response = app.server.request('POST',f'/documents/{document_id}/{operation}',token=app.tokens[user])
    assert response.status_code == expect,response.text
    return response.json()


def python_result(app,program):
    result = subprocess.run([sys.executable,'-c',program],cwd=ROOT,env=app.environment,
                            capture_output=True,text=True,timeout=40)
    assert result.returncode == 0,result.stdout+result.stderr
    return json.loads(result.stdout)


def search(app):
    return python_result(app,'''import asyncio,json
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from knowledge.core.config import get_settings
from knowledge.documents.repository import DocumentRepository
from knowledge.integrations.providers import FixtureEmbeddingClient
async def main():
    engine=create_async_engine(get_settings().database_url)
    sessions=async_sessionmaker(engine,expire_on_commit=False)
    provider=FixtureEmbeddingClient()
    vector=(await provider.embed(['alpha material conditions'])).vectors[0]
    async with sessions() as session:
        repo=DocumentRepository(session)
        found=await repo.search(None,vector,provider.profile_id,'alpha material conditions')
        neighbors=await repo.get_neighbors(None,[h['passageId'] for h in found['hits'][:1]])
        print(json.dumps({'hits':found['hits'],'neighbors':neighbors}))
    await engine.dispose()
asyncio.run(main())
''')


def test_upload_is_queued_then_shared_after_real_worker_and_restart(documents_app):
    app = documents_app
    accepted = upload(app)
    doc,rev = accepted['documentId'],accepted['revisionId']
    assert accepted['status'] == 'queued' and not accepted['searchable']
    assert detail(app,doc,'bob')['latestRevision']['job']['status'] == 'pending'
    assert app.database.query('SELECT count(*) AS n FROM passages')[0]['n'] == 0
    original = app.server.request('GET',f'/documents/{doc}/raw',token=app.tokens['bob'])
    assert original.status_code == 200 and original.content == TEXT
    assert work(app)['status'] == 'succeeded'
    result = detail(app,doc,'bob')
    assert result['searchable'] and result['activeRevisionId'] == rev and result['status'] == 'ready'
    assert result['latestRevision']['embeddingProfile'] == 'fixture:sha256:1536:v1'
    assert result['latestRevision']['job']['usage']['calls'][0]['source'] == 'fixture'
    passages = app.server.request('GET',f'/documents/{doc}/passages',token=app.tokens['bob']).json()
    assert len(passages['passages']) >= 2
    for p in passages['passages']:
        assert passages['content'][p['startOffset']:p['endOffset']] == p['text']
        assert p['locator'] and not p['excluded']
    links = app.database.query('SELECT count(*) AS n FROM passage_embeddings')[0]['n']
    assert links == len(passages['passages'])
    assert app.database.query('SELECT vector_dims(vector) AS n FROM embedding_records LIMIT 1')[0]['n'] == 1536
    assert {r['kind'] for r in app.database.query('SELECT kind FROM processing_jobs')} == {'document_index'}
    found = search(app)
    assert found['hits'] and all(h['sourceRevisionId'] == rev for h in found['hits'])
    assert found['neighbors']
    app.server.restart()
    assert detail(app,doc,'bob')['activeRevisionId'] == rev


def test_concurrent_duplicate_uploads_create_one_revision_and_job(documents_app):
    app = documents_app
    with ThreadPoolExecutor(max_workers=4) as pool:
        accepted = list(pool.map(lambda _:upload(app),range(4)))
    assert len({a['documentId'] for a in accepted}) == 1
    assert sum(a['duplicate'] for a in accepted) == 3
    for table in ('documents','document_revisions','processing_jobs'):
        assert app.database.query(f'SELECT count(*) AS n FROM {table}')[0]['n'] == 1
    assert work(app)['status'] == 'succeeded'
    before = app.database.query('SELECT count(*) AS n FROM embedding_records')
    repeat = upload(app,user='bob')
    assert repeat['duplicate'] and repeat['documentId'] == accepted[0]['documentId']
    action(app,repeat['documentId'],'reprocess')
    assert work(app)['status'] == 'idle'
    assert app.database.query('SELECT count(*) AS n FROM embedding_records') == before
    assert detail(app,repeat['documentId'])['latestRevision']['job']['attempts'] == 1


def test_real_partial_quality_hold_excludes_only_oversized_table(documents_app):
    app = documents_app
    table = '| Field | Value |\n|---|---|\n' + ''.join(f'| row {i} | '+('unverified '*50)+' |\n' for i in range(20))
    body = TEXT + ('\n## Large table\n\n'+table+'\n## Limits\n\nOnly the normal sections may be searched.').encode()
    accepted = upload(app,body)
    assert work(app)['status'] == 'succeeded'
    result = detail(app,accepted['documentId'])
    assert result['status'] == 'partial' and result['searchable']
    assert result['latestRevision']['heldPassageCount'] >= 1
    held = app.database.query('SELECT id,exclusion_reason FROM passages WHERE excluded')
    assert held and all(p['exclusion_reason'] for p in held)
    assert app.database.query('SELECT count(*) AS n FROM passage_embeddings e JOIN passages p ON p.id=e.passage_id WHERE p.excluded')[0]['n'] == 0
    result = search(app)
    assert result['hits'] and not {p['id'] for p in held}.intersection(h['passageId'] for h in result['hits']+result['neighbors'])


def test_all_held_is_distinct_from_embedding_failure(documents_app):
    app = documents_app
    accepted = upload(app,b'long-block '*1000,filename='long.txt')
    assert work(app)['status'] == 'failed'
    result = detail(app,accepted['documentId'])
    assert not result['searchable'] and result['latestRevision']['job']['error']['code'] == 'no_indexable_passages'
    assert app.database.query('SELECT count(*) AS n FROM embedding_records')[0]['n'] == 0


def test_failed_revision_preserves_active_revision_and_retry_is_deduplicated(documents_app):
    app = documents_app
    first = upload(app)
    assert work(app)['status'] == 'succeeded'
    second = upload(app,TEXT.replace(b'measured result',b'new measured result'),document_id=first['documentId'])
    # A real configured-disabled adapter must fail rather than quietly use fixtures.
    assert work(app,OW_PROVIDER_MODE='disabled')['status'] == 'failed'
    result = detail(app,first['documentId'])
    assert result['searchable'] and result['activeRevisionId'] == first['revisionId']
    assert result['latestRevision']['job']['error']['phase'] == 'embedding'
    assert result['latestRevision']['job']['error']['code'] == 'configuration_blocked'
    assert {h['sourceRevisionId'] for h in search(app)['hits']} == {first['revisionId']}
    with ThreadPoolExecutor(max_workers=3) as pool:
        retries = list(pool.map(lambda _:action(app,first['documentId'],'reprocess'),range(3)))
    assert len({r['job']['id'] for r in retries}) == 1
    completed = work(app)
    assert completed['status'] == 'succeeded' and completed['reused'] > 0
    assert detail(app,first['documentId'])['activeRevisionId'] == second['revisionId']
    assert {h['sourceRevisionId'] for h in search(app)['hits']} == {second['revisionId']}
    assert app.database.query('SELECT count(*) AS n FROM processing_jobs')[0]['n'] == 2


def test_bad_utf8_preserves_raw_and_does_not_replace_active(documents_app):
    app = documents_app
    first = upload(app)
    assert work(app)['status'] == 'succeeded'
    invalid = upload(app,b'\xff\xfe\x00bad',document_id=first['documentId'])
    failed = work(app)
    assert failed['status'] == 'failed' and failed['error']['code'] == 'source_encoding'
    assert failed['error']['phase'] == 'parsing'
    assert detail(app,first['documentId'])['activeRevisionId'] == first['revisionId']
    raw = app.server.request('GET',f"/documents/{first['documentId']}/raw?revisionId={invalid['revisionId']}",token=app.tokens['alice'])
    assert raw.content == b'\xff\xfe\x00bad'


def test_deactivation_blocks_sources_search_and_retry(documents_app):
    app = documents_app
    accepted = upload(app)
    assert work(app)['status'] == 'succeeded'
    doc = accepted['documentId']
    action(app,doc,'deactivate',expect=200)
    assert not detail(app,doc,'bob')['searchable']
    for suffix in ('raw','passages'):
        assert app.server.request('GET',f'/documents/{doc}/{suffix}',token=app.tokens['bob']).status_code == 404
    assert search(app)['hits'] == []
    action(app,doc,'reprocess',expect=409)
    upload(app,expect=409)
    assert work(app)['status'] == 'idle'


def test_shared_read_does_not_grant_other_employee_mutation(documents_app):
    app = documents_app
    accepted = upload(app)
    doc = accepted['documentId']
    assert detail(app,doc,'bob')['canManage'] is False
    for operation in ('reprocess','deactivate'):
        action(app,doc,operation,user='bob',expect=403)
    upload(app,TEXT+b'new',document_id=doc,user='bob',expect=403)
    action(app,doc,'deactivate',user='operator',expect=200)


def test_old_pending_revision_is_superseded_not_accidentally_activated(documents_app):
    app = documents_app
    first = upload(app)
    second = upload(app,TEXT+b'\nExtra revision.\n',document_id=first['documentId'])
    assert app.database.query('SELECT status FROM processing_jobs WHERE id=$1',first['jobId']) == [{'status':'superseded'}]
    assert work(app)['jobId'] == second['jobId']
    assert detail(app,first['documentId'])['activeRevisionId'] == second['revisionId']


def pdf_bytes():
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(width=595,height=842)
    font = DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 780 Td (Synthetic PDF: alpha material uses 250 C under the stated test conditions.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_real_pdf_subprocess_extraction_preserves_page_and_raw(documents_app):
    app = documents_app
    body = pdf_bytes()
    accepted = upload(app,body,filename='fixture.pdf')
    assert work(app)['status'] == 'succeeded'
    result = detail(app,accepted['documentId'])
    assert result['status'] == 'partial'
    assert result['latestRevision']['processing']['parserProfile']['engine'] == 'pypdf'
    source = app.server.request('GET',f"/documents/{accepted['documentId']}/passages",token=app.tokens['bob']).json()
    assert 'alpha material' in source['content']
    assert any('페이지 1' in p['locator'] for p in source['passages'])
    assert app.server.request('GET',f"/documents/{accepted['documentId']}/raw",token=app.tokens['bob']).content == body


@pytest.mark.parametrize('filename,body,config',[
    ('fixture.pdf',b'%PDF-1.7 fake only',{'OW_PDF_PARSER':'docling'}),
    ('fixture.xml',b'<article><body><p>JATS content</p></body></article>',{}),
])
def test_missing_docling_configuration_never_silently_falls_back(documents_app,filename,body,config):
    app = documents_app
    accepted = upload(app,body,filename=filename)
    failed = work(app,**config)
    assert failed['status'] == 'failed' and failed['error']['phase'] == 'parsing'
    assert failed['error']['code'] == 'parser_configuration'
    assert not detail(app,accepted['documentId'])['searchable']
    assert app.database.query('SELECT count(*) AS n FROM embedding_records')[0]['n'] == 0


def test_corrupt_raw_fails_integrity_without_indexing(documents_app):
    app = documents_app
    accepted = upload(app)
    relative = app.database.query('SELECT raw_path FROM document_revisions WHERE id=$1',accepted['revisionId'])[0]['raw_path']
    (Path(app.environment['OW_STORAGE_PATH'])/relative).write_bytes(b'corrupt source')
    failed = work(app)
    assert failed['status'] == 'failed' and failed['error']['code'] == 'source_integrity'
    assert app.database.query('SELECT count(*) AS n FROM passages')[0]['n'] == 0
    assert app.server.request('GET',f"/documents/{accepted['documentId']}/raw",token=app.tokens['bob']).status_code == 409


def slow_worker(app):
    sentinel = app.directory/'embedding-started'
    program = f'''import asyncio,json
from pathlib import Path
from knowledge.jobs.worker import run_worker
from knowledge.integrations.providers import FixtureEmbeddingClient
class Slow(FixtureEmbeddingClient):
    async def embed(self,texts):
        Path({str(sentinel)!r}).write_text('started')
        await asyncio.sleep(3)
        return await super().embed(texts)
print(json.dumps(asyncio.run(run_worker(once=True,embedding_client=Slow()))))
'''
    process = subprocess.Popen([sys.executable,'-c',program],cwd=ROOT,env=app.environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    deadline = time.monotonic()+15
    while time.monotonic() < deadline:
        if sentinel.exists():
            return process
        if process.poll() is not None:
            stdout,stderr = process.communicate()
            raise AssertionError(stdout+stderr)
        time.sleep(.05)
    process.kill()
    process.communicate()
    raise AssertionError('Worker did not reach embedding')


def test_second_worker_cannot_duplicate_running_job(documents_app):
    app = documents_app
    accepted = upload(app)
    process = slow_worker(app)
    try:
        assert work(app)['status'] == 'busy'
        stdout,stderr = process.communicate(timeout=20)
        assert process.returncode == 0,stderr
        assert json.loads(stdout)['status'] == 'succeeded'
        assert detail(app,accepted['documentId'])['latestRevision']['job']['attempts'] == 1
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


def test_deactivate_during_embedding_cannot_resurrect_document(documents_app):
    app = documents_app
    accepted = upload(app)
    process = slow_worker(app)
    try:
        action(app,accepted['documentId'],'deactivate',expect=200)
        stdout,stderr = process.communicate(timeout=20)
        assert process.returncode == 0,stderr
        assert json.loads(stdout)['status'] == 'cancelled'
        result = detail(app,accepted['documentId'])
        assert result['status'] == 'inactive' and result['activeRevisionId'] is None
        assert search(app)['hits'] == []
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


def test_crashed_worker_is_recoverable_without_automatic_paid_retry(documents_app):
    app = documents_app
    accepted = upload(app)
    process = slow_worker(app)
    process.kill()
    process.communicate(timeout=10)
    assert work(app)['status'] == 'idle'
    failed = detail(app,accepted['documentId'])['latestRevision']['job']
    assert failed['status'] == 'failed' and failed['error']['code'] == 'worker_interrupted'
    action(app,accepted['documentId'],'reprocess')
    assert work(app)['status'] == 'succeeded'


def test_partial_embedding_cache_survives_batch_failure(documents_app):
    app = documents_app
    body = '\n\n'.join(f'## Section {i}\n\nalpha material sample {i}.' for i in range(40)).encode()
    accepted = upload(app,body)
    result = python_result(app,'''import asyncio,json
from knowledge.jobs.worker import run_worker
from knowledge.integrations.providers import FixtureEmbeddingClient
from knowledge.core.errors import AppError
class Failing(FixtureEmbeddingClient):
    count=0
    async def embed(self,texts):
        self.count+=1
        if self.count==2:
            raise AppError(502,'fixture_interruption','Explicit test interruption',retryable=True)
        return await super().embed(texts)
print(json.dumps(asyncio.run(run_worker(once=True,embedding_client=Failing()))))
''')
    assert result['status'] == 'failed'
    assert not detail(app,accepted['documentId'])['searchable']
    assert app.database.query('SELECT count(*) AS n FROM embedding_records')[0]['n'] == 32
    action(app,accepted['documentId'],'reprocess')
    result = work(app)
    assert result['status'] == 'succeeded' and result['reused'] >= 32
    assert app.database.query('SELECT count(*) AS n FROM passage_embeddings')[0]['n'] == 40


@pytest.mark.parametrize('filename,body,status', [('bad.exe',b'bad',415),('empty.md',b'',413)])
def test_invalid_uploads_create_no_jobs(documents_app,filename,body,status):
    app = documents_app
    upload(app,body,filename=filename,expect=status)
    assert app.database.query('SELECT count(*) AS n FROM processing_jobs')[0]['n'] == 0
