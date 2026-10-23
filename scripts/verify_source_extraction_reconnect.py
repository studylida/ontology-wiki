"""Isolated refresh/replay/recovery assertions; no model calls or operational database writes."""
import asyncio
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from httpx import ASGITransport,AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from backend.app.api import admin_sources
from backend.app.core.database import Base,get_db
from backend.app.core.security import get_current_active_user
from backend.app.models.entities import SourceDocumentModel
from backend.app.services.source_service import SourceExtractionService,source_service
from backend.app.repositories.source_repo import source_repo
from backend.app.schemas.source_ingestion import ExtractedConceptDiffDTO
from starlette.responses import StreamingResponse

async def main():
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as connection:await connection.run_sync(Base.metadata.create_all)
    service=SourceExtractionService(session_factory=factory)
    admin_sources.source_service=service
    original=source_repo.sources_dir
    started=asyncio.Event();gate=asyncio.Event();cancelled=asyncio.Event();calls=[]
    async def extract(doc,**kwargs):
        calls.append(doc.doc_id)
        if doc.doc_id=='d5':
            started.set()
            try:await gate.wait()
            except asyncio.CancelledError:cancelled.set();raise
        return [ExtractedConceptDiffDTO(**raw(doc.doc_id))]
    def raw(did):
        text=f'{did}는 재료를 연결하는 검증 공정이다.'
        return service.normalize_concept(service.validate_quotes({'conceptId':'c-'+did,'title':did,'engName':did,
            'domainFacet':'unit_process','category':'검증','scaleLevel':3,'summary':text,'summaryEvidenceQuote':text,'purpose':'',
            'sourceCoverage':{'complete':True,'totalParts':1,'processedParts':1,'totalCharacters':len(text),'processedCharacters':len(text)}},text),did)
    app=FastAPI();app.include_router(admin_sources.router,prefix='/api/v1')
    level=4
    async def db():
        async with factory() as session:yield session
    async def admin():return SimpleNamespace(level=level,name='검증 관리자')
    app.dependency_overrides.update({get_db:db,get_current_active_user:admin})
    try:
        with tempfile.TemporaryDirectory(prefix='source-reconnect-') as temporary:
            source_repo.sources_dir=Path(temporary).resolve()
            async with factory() as session:
                for i in range(7):
                    did='d'+str(i);text=f'{did}는 재료를 연결하는 검증 공정이다.'
                    (source_repo.sources_dir/(did+'.md')).write_text(text,encoding='utf-8')
                    session.add(SourceDocumentModel(doc_id=did,file_path=did+'.md',publisher='fixture',title=did,file_hash='fixture',
                        attempt_status='success' if i<5 or i==6 else 'running',last_attempted_at=datetime(2026,1,1),
                        last_succeeded_at=datetime(2026,1,1) if i!=5 else None,last_preview_payload=[raw(did)] if i!=5 else None))
                await session.commit()
            async with factory() as session:
                before={did:(doc.last_succeeded_at,json.dumps(doc.last_preview_payload,sort_keys=True)) for did in ['d'+str(i) for i in range(5)] if (doc:=await session.get(SourceDocumentModel,did))}
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://memory') as client:
                level=3
                assert (await client.get('/api/v1/admin/sources/extraction-state')).status_code==403
                assert (await client.get('/api/v1/admin/sources/extract?runId=missing')).status_code==403
                level=4
                assert (await client.get('/api/v1/admin/sources/extract?runId=missing')).status_code==404
                state=(await client.get('/api/v1/admin/sources/extraction-state')).json()
                assert state['state']=='interrupted' and state['preservedCount']==5 and state['docIds']==['d'+str(i) for i in range(7)]
                with patch.object(service,'extract_single_document',new=extract):
                    async with factory() as session:
                        run_id=await service.start_extraction(session,state['docIds'],resume_interrupted=True)
                    await asyncio.wait_for(started.wait(),3)
                    disconnected=asyncio.Event()
                    async def receive():await disconnected.wait();return {'type':'http.disconnect'}
                    async def send(message):
                        if message['type']=='http.response.body' and b'event: progress' in message.get('body',b''):disconnected.set()
                    await StreamingResponse(service.extraction_events(run_id),media_type='text/event-stream')({'type':'http','asgi':{'spec_version':'2.3'}},receive,send)
                    assert not cancelled.is_set() and not service._extraction_run['task'].done()
                    state=(await client.get('/api/v1/admin/sources/extraction-state')).json()
                    assert state['state']=='running' and state['runId']==run_id
                    duplicate=await client.post('/api/v1/admin/sources/extract',json={'docIds':['d6'],'forceReextract':True})
                    assert duplicate.status_code==409 and calls==['d5']
                    gate.set()
                    response=await client.get('/api/v1/admin/sources/extract',params={'runId':run_id});response.raise_for_status()
                    assert 'event: finished' in response.text,response.text
                    finished=json.loads(response.text.split('event: finished\ndata: ')[-1].strip())
                    assert finished['totalSucceeded']==7 and finished['totalFailed']==0
                    assert len(finished['aggregatedConcepts'])==7 and calls==['d5','d6']
                    assert response.text.count('"preserved": true')==5
                    assert (await client.get('/api/v1/admin/sources/extraction-state')).json()['state']=='finished'
                    replay=await client.get('/api/v1/admin/sources/extract',params={'runId':run_id})
                    assert replay.text==response.text and calls==['d5','d6']
                    # A rejected recovery plan cannot silently start a partial or reordered catalog.
                    async with factory() as session:
                        try:await service.start_extraction(session,['d6','d5'],resume_interrupted=True)
                        except Exception as error:assert error.status_code==409
                        else:raise AssertionError('Invalid recovery scope must be rejected')
            async with factory() as session:
                after={did:(doc.last_succeeded_at,json.dumps(doc.last_preview_payload,sort_keys=True)) for did in before if (doc:=await session.get(SourceDocumentModel,did))}
            assert after==before,'Completed source previews/timestamps must remain byte-for-byte equivalent'
            print('PASS disconnect leaves worker alive; authenticated running/finished replay; no duplicate work; exact legacy catalog recovery preserves five previews/timestamps and includes them in final aggregate; only interrupted/tail documents extracted')
    finally:
        source_repo.sources_dir=original
        if service._extraction_run and not service._extraction_run['task'].done():
            service._extraction_run['task'].cancel()
            try:await service._extraction_run['task']
            except asyncio.CancelledError:pass
        await engine.dispose()

asyncio.run(main())
