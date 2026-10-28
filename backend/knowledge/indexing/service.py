"""Source processing, reusable embeddings and an atomic active-revision switch."""
from __future__ import annotations
import asyncio
import logging
import math
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from ..core.errors import AppError
from ..core.ids import new_id, utcnow
from ..documents.entities import Document, DocumentRevision, EmbeddingRecord, Passage, PassageEmbedding
from ..documents.parsing import digest
from ..documents.processing import prepare_file
from ..documents.repository import DocumentRepository
from ..documents.storage import read_raw
from ..jobs.entities import Job
from .dto import IndexUnit


async def locked_work(session, job_id):
    snapshot = await session.get(Job,job_id)
    if snapshot is None:
        raise AppError(404,'job_not_found','작업을 찾을 수 없습니다.')
    document = await DocumentRepository(session).get(snapshot.document_id,lock=True)
    job = await session.get(Job,job_id,with_for_update=True,populate_existing=True)
    revision = await session.get(DocumentRevision,job.source_revision_id,with_for_update=True)
    return document,revision,job


def valid_work(document,revision,job):
    if job.status != 'running':
        return False
    if document.withdrawn or document.current_revision_id != revision.id:
        job.status,job.updated_at = 'superseded',utcnow()
        if revision.id != document.active_revision_id:
            revision.index_status = 'superseded'
        return False
    return True


async def process_index_job(sessions, settings, job_id, embedding_client=None):
    """Called only after the queue claims a job. No DB transaction spans a model call."""
    phase = 'parsing'
    try:
        async with sessions() as session, session.begin():
            document,revision,job = await locked_work(session,job_id)
            if not valid_work(document,revision,job):
                return {'jobId':job_id,'status':job.status}
            revision.index_status = 'processing'
            job.progress,job.updated_at = {'phase':phase},utcnow()
            raw_path,raw_hash,title,media_type = revision.raw_path,revision.raw_sha256,revision.title,revision.media_type
            already_parsed = revision.content is not None
        raw = await asyncio.to_thread(read_raw,settings.storage_path,raw_path,raw_hash)
        if not already_parsed:
            prepared = await prepare_file(raw,media_type,title,settings)
            async with sessions() as session, session.begin():
                document,revision,job = await locked_work(session,job_id)
                if not valid_work(document,revision,job):
                    return {'jobId':job_id,'status':job.status}
                revision.content,revision.content_hash = prepared.content,digest(prepared.content)
                revision.processing_metadata = prepared.metadata
                revision.read_scope,revision.limitations = prepared.read_scope,prepared.limitations
                ids = [new_id('psg') for _ in prepared.passages]
                for index,(passage,source) in enumerate(zip(prepared.passages,prepared.source_map,strict=True)):
                    source = dict(source)
                    source['relatedPassageIds'] = [ids[n] for n in source.get('relatedOrdinals',[]) if type(n) is int and 0 <= n < len(ids)]
                    values = dict(passage.__dict__)
                    # Keep a complete source block, but never exceed safe embedding input limits.
                    if len(passage.embedding_text.encode('utf-8')) > 7000 and not passage.excluded:
                        values.update(excluded=True,exclusion_reason='긴 문단 또는 표의 분할 검토 필요')
                    session.add(Passage(id=ids[index],source_revision_id=revision.id,source_map=source,**values))
        async with sessions() as session:
            job = await session.get(Job,job_id)
            passages = await DocumentRepository(session).passages(job.source_revision_id)
            units = [IndexUnit(p.id,p.source_revision_id,p.embedding_text,p.input_hash) for p in passages]
        if not units:
            raise AppError(422,'no_indexable_passages','모든 구간이 보류되어 색인할 본문이 없습니다.')
        phase = 'embedding'
        if embedding_client is None:
            from ..integrations.providers import get_embedding_client
            embedding_client = get_embedding_client(settings)
        profile = embedding_client.profile_id
        embedded,reused = 0,0
        for offset in range(0,len(units),32):
            batch = units[offset:offset+32]
            async with sessions() as session, session.begin():
                document,revision,job = await locked_work(session,job_id)
                if not valid_work(document,revision,job):
                    return {'jobId':job_id,'status':job.status}
                job.progress = {'phase':phase,'processed':offset,'total':len(units),'embedded':embedded,'reused':reused}
                job.updated_at = utcnow()
                records = list(await session.scalars(select(EmbeddingRecord).where(EmbeddingRecord.scope == 'shared',
                    EmbeddingRecord.profile_id == profile,EmbeddingRecord.input_hash.in_([u.input_hash for u in batch]))))
                cached = {r.input_hash:r.id for r in records}
            missing = {u.input_hash:u.text for u in batch if u.input_hash not in cached}
            response,vectors = None,{}
            if missing:
                response = await embedding_client.embed(list(missing.values()))
                if len(response.vectors) != len(missing):
                    raise AppError(502,'invalid_embedding','임베딩 결과와 입력 개수가 다릅니다.')
                for hashed,vector in zip(missing,response.vectors,strict=True):
                    if len(vector) != 1536 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in vector) or not any(v != 0 for v in vector):
                        raise AppError(502,'invalid_embedding','임베딩 벡터의 차원 또는 값이 유효하지 않습니다.')
                    vectors[hashed] = vector
            async with sessions() as session, session.begin():
                document,revision,job = await locked_work(session,job_id)
                if response is not None:
                    job.usage = {'calls':[*(job.usage or {}).get('calls',[]),response.usage]}
                if not valid_work(document,revision,job):
                    return {'jobId':job_id,'status':job.status}
                reused += len(batch) - len(missing)
                for hashed,vector in vectors.items():
                    await session.execute(insert(EmbeddingRecord).values(id=new_id('vec'),scope='shared',profile_id=profile,
                        input_hash=hashed,vector=vector).on_conflict_do_nothing(index_elements=['scope','profile_id','input_hash']))
                    record = await session.scalar(select(EmbeddingRecord).where(EmbeddingRecord.scope == 'shared',
                        EmbeddingRecord.profile_id == profile,EmbeddingRecord.input_hash == hashed))
                    cached[hashed] = record.id
                embedded += len(vectors)
                for unit in batch:
                    await session.execute(insert(PassageEmbedding).values(id=new_id('pe'),passage_id=unit.passage_id,
                        profile_id=profile,embedding_id=cached[unit.input_hash]).on_conflict_do_nothing(index_elements=['passage_id','profile_id']))
                job.progress = {'phase':phase,'processed':offset+len(batch),'total':len(units),'embedded':embedded,'reused':reused}
                job.updated_at = utcnow()
        phase = 'activation'
        async with sessions() as session, session.begin():
            document,revision,job = await locked_work(session,job_id)
            if not valid_work(document,revision,job):
                return {'jobId':job_id,'status':job.status}
            count = await session.scalar(select(func.count()).select_from(PassageEmbedding).where(
                PassageEmbedding.passage_id.in_([u.passage_id for u in units]),PassageEmbedding.profile_id == profile))
            if count != len(units):
                raise AppError(409,'incomplete_index','모든 유효 구간의 색인이 준비되지 않았습니다.')
            revision.index_status,revision.embedding_profile,revision.index_snapshot_id = 'ready',profile,new_id('idx')
            document.active_revision_id,document.title,document.updated_at = revision.id,revision.title,utcnow()
            job.status,job.error,job.updated_at = 'succeeded',None,utcnow()
            job.progress = {**job.progress,'phase':'complete','indexedPassages':len(units),'embeddingProfile':profile}
        return {'jobId':job_id,'status':'succeeded','indexedPassages':len(units),'embedded':embedded,'reused':reused}
    except Exception as exc:
        error = exc.public() if isinstance(exc,AppError) else {
            'code':'processing_failed','message':'문헌 처리 중 오류가 발생했습니다. 원문과 설정을 확인해 주세요.','retryable':True}
        error = {**error,'phase':phase}
        logging.getLogger('knowledge.worker').warning('document_job_failed job=%s phase=%s error_type=%s',job_id,phase,type(exc).__name__)
        async with sessions() as session, session.begin():
            document,revision,job = await locked_work(session,job_id)
            if valid_work(document,revision,job):
                job.status,job.error,job.updated_at = 'failed',error,utcnow()
                if getattr(exc,'usage',None):
                    job.usage = {'calls':[*(job.usage or {}).get('calls',[]),exc.usage]}
                revision.index_status = 'failed'
            result = {'jobId':job_id,'status':job.status,'error':job.error}
        return result
