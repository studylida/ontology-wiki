"""Shared file intake and document operations. No model call in HTTP requests."""
from __future__ import annotations
import asyncio
import hashlib
from pathlib import PurePath
from sqlalchemy import func, select, text
from ..core.errors import AppError
from ..core.ids import new_id, utcnow
from ..jobs.entities import Job
from ..jobs.repository import JobRepository
from .entities import Document, DocumentRevision, Passage
from .parsing import metadata_digest
from .repository import DocumentRepository
from .storage import read_raw, save_raw

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MEDIA_TYPES = {'.md':'text/markdown','.markdown':'text/markdown','.txt':'text/plain',
               '.pdf':'application/pdf','.xml':'application/xml','.nxml':'application/xml','.jats':'application/jats+xml'}


class DocumentService:
    def __init__(self, session_factory, settings):
        self.sessions, self.settings = session_factory, settings

    async def upload(self, principal, body, filename, info, document_id=None):
        if principal.kind != 'user':
            raise AppError(403,'employee_required','직원 계정으로 문헌을 등록해 주세요.')
        filename = PurePath((filename or 'upload').replace('\\','/')).name
        if not filename or len(filename) > 255 or any(ord(c) < 32 for c in filename):
            raise AppError(422,'invalid_filename','파일 이름을 확인해 주세요.')
        media_type = MEDIA_TYPES.get(PurePath(filename).suffix.lower())
        if not media_type:
            raise AppError(415,'unsupported_source_type','Markdown·UTF-8 텍스트·PDF·JATS XML을 업로드해 주세요.')
        if not body or len(body) > MAX_UPLOAD_BYTES:
            raise AppError(413,'source_too_large','0바이트가 아닌 20MB 이하의 파일이 필요합니다.')
        if document_id:
            async with self.sessions() as session:
                document = await DocumentRepository(session).get(document_id)
                DocumentRepository.require_manage(document,principal)
                DocumentRepository.require_enabled(document)
        raw_hash = hashlib.sha256(body).hexdigest()
        metadata = info.metadata.model_dump(mode='json',by_alias=True,exclude_none=True)
        fingerprint = metadata_digest({'raw':raw_hash,'media':media_type,'title':info.title,'metadata':metadata})
        raw_path = await asyncio.to_thread(save_raw,self.settings.storage_path,body)
        async with self.sessions() as session, session.begin():
            repo = DocumentRepository(session)
            if document_id is None:
                # Serialize identical intake across API processes. No network work inside this transaction.
                lock_key = int.from_bytes(bytes.fromhex(fingerprint)[:8],'big',signed=True)
                await session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':lock_key})
                document = await session.scalar(select(Document).where(Document.origin_key == fingerprint).with_for_update())
                if document is None:
                    document = Document(id=new_id('doc'),owner_id=principal.id,title=info.title,origin_key=fingerprint)
                    session.add(document)
                    await session.flush()
            else:
                document = await repo.get(document_id,lock=True)
                repo.require_manage(document,principal)
            repo.require_enabled(document)
            revision = await session.scalar(select(DocumentRevision).where(
                DocumentRevision.document_id == document.id,DocumentRevision.input_hash == fingerprint))
            duplicate = revision is not None
            if revision is None:
                number = (await session.scalar(select(func.max(DocumentRevision.revision)).where(DocumentRevision.document_id == document.id)) or 0) + 1
                revision = DocumentRevision(id=new_id('rev'),document_id=document.id,revision=number,
                    title=info.title,filename=filename,media_type=media_type,raw_path=raw_path,
                    raw_sha256=raw_hash,input_hash=fingerprint,metadata_json=metadata)
                session.add(revision)
                await session.flush()
                # A newer upload supersedes unfinished work, not the last usable active revision.
                previous_jobs = list(await session.scalars(select(Job).where(Job.document_id == document.id,
                    Job.status.in_(['pending','running'])).with_for_update()))
                for old in previous_jobs:
                    old.status, old.updated_at = 'superseded', utcnow()
                    old_revision = await session.get(DocumentRevision,old.source_revision_id)
                    if old_revision.id != document.active_revision_id:
                        old_revision.index_status = 'superseded'
                document.current_revision_id, document.updated_at = revision.id, utcnow()
            job = await JobRepository(session).enqueue(document.id,revision.id)
            result = {'documentId':document.id,'revisionId':revision.id,'jobId':job.id,
                      'duplicate':duplicate,'status':revision.index_status,'jobStatus':job.status,
                      'shared':True,'searchable':bool(document.active_revision_id and not document.withdrawn)}
        return result

    async def _revision_summary(self, session, revision):
        if revision is None:
            return None
        total = await session.scalar(select(func.count()).select_from(Passage).where(Passage.source_revision_id == revision.id))
        held = await session.scalar(select(func.count()).select_from(Passage).where(Passage.source_revision_id == revision.id,Passage.excluded.is_(True)))
        status = revision.index_status
        if status == 'ready' and (held or revision.read_scope == 'partial'):
            status = 'partial'
        job = await JobRepository(session).for_revision(revision.id)
        return {'id':revision.id,'revision':revision.revision,'title':revision.title,'filename':revision.filename,
                'mediaType':revision.media_type,'status':status,'readScope':revision.read_scope,
                'passageCount':total,'heldPassageCount':held,'usablePassageCount':total-held,
                'metadata':revision.metadata_json,'processing':revision.processing_metadata,
                'limitations':revision.limitations,'embeddingProfile':revision.embedding_profile,
                'indexSnapshotId':revision.index_snapshot_id,'job':JobRepository.public(job),
                'createdAt':revision.created_at.isoformat()}

    async def _summary(self, session, document, principal):
        latest = await session.get(DocumentRevision,document.current_revision_id) if document.current_revision_id else None
        active = await session.get(DocumentRevision,document.active_revision_id) if document.active_revision_id else None
        latest_view = await self._revision_summary(session,latest)
        active_view = latest_view if active is not None and latest is not None and active.id == latest.id else await self._revision_summary(session,active)
        return {'id':document.id,'title':document.title,'shared':True,'withdrawn':document.withdrawn,
                'status':'inactive' if document.withdrawn else latest_view['status'] if latest_view else 'queued',
                'searchable':bool(active is not None and active.index_status == 'ready' and not document.withdrawn),
                'canManage':document.owner_id == principal.id or principal.role == 'admin',
                'currentRevisionId':document.current_revision_id,'activeRevisionId':document.active_revision_id,
                'latestRevision':latest_view,'activeRevision':active_view,'updatedAt':document.updated_at.isoformat()}

    async def list(self, principal):
        async with self.sessions() as session:
            documents = await DocumentRepository(session).list()
            return {'items':[await self._summary(session,d,principal) for d in documents]}

    async def detail(self, principal, document_id):
        async with self.sessions() as session:
            return await self._summary(session,await DocumentRepository(session).get(document_id),principal)

    async def source(self, principal, document_id, revision_id=None, *, raw=False):
        async with self.sessions() as session:
            repo = DocumentRepository(session)
            document = await repo.get(document_id)
            if document.withdrawn:
                raise AppError(404,'source_not_found','비활성화된 문헌입니다.')
            chosen = revision_id or document.active_revision_id or document.current_revision_id
            revision, owned_document = await repo.revision(principal,chosen)
            if owned_document.id != document.id:
                raise AppError(404,'source_not_found','해당 문헌의 판본이 아닙니다.')
            if raw:
                path, hashed, filename, media = revision.raw_path, revision.raw_sha256, revision.filename, revision.media_type
            else:
                passages = await repo.passages(revision.id,include_excluded=True)
                return {'documentId':document.id,'revisionId':revision.id,'active':document.active_revision_id == revision.id,
                        'content':revision.content,'contentHash':revision.content_hash,
                        'passages':[{'id':p.id,'ordinal':p.ordinal,'text':p.text,'locator':p.locator,
                                     'startOffset':p.start_offset,'endOffset':p.end_offset,'excluded':p.excluded,
                                     'exclusionReason':p.exclusion_reason,'sourceMap':p.source_map} for p in passages]}
        body = await asyncio.to_thread(read_raw,self.settings.storage_path,path,hashed)
        async with self.sessions() as session:
            if not await DocumentRepository(session).ensure_readable(principal,[chosen]):
                raise AppError(404,'source_not_found','비활성화된 문헌입니다.')
        return body,filename,media

    async def reprocess(self, principal, document_id):
        async with self.sessions() as session, session.begin():
            repo = DocumentRepository(session)
            document = await repo.get(document_id,lock=True)
            repo.require_manage(document,principal)
            repo.require_enabled(document)
            job = await JobRepository(session).for_revision(document.current_revision_id,lock=True)
            if job is None:
                raise AppError(409,'job_missing','문헌 처리 작업을 찾을 수 없습니다.')
            if job.status == 'failed':
                JobRepository.restart(job)
                revision = await session.get(DocumentRevision,job.source_revision_id)
                revision.index_status = 'queued'
            await session.flush()
            result = {'documentId':document.id,'revisionId':job.source_revision_id,'job':JobRepository.public(job)}
        return result

    async def deactivate(self, principal, document_id):
        async with self.sessions() as session, session.begin():
            repo = DocumentRepository(session)
            document = await repo.get(document_id,lock=True)
            repo.require_manage(document,principal)
            document.withdrawn,document.updated_at = True,utcnow()
            jobs = list(await session.scalars(select(Job).where(Job.document_id == document.id,Job.status.in_(['pending','running'])).with_for_update()))
            for job in jobs:
                job.status,job.updated_at = 'cancelled',utcnow()
                job.error = {'code':'document_inactive','message':'문헌이 비활성화되었습니다.','retryable':False}
        return {'documentId':document_id,'status':'inactive','searchable':False}
