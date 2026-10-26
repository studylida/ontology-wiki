from knowledge.core.errors import AppError
from knowledge.core.ids import utcnow
from knowledge.documents.entities import DocumentRevision
from knowledge.documents.repository import DocumentRepository
from knowledge.jobs.indexing import enqueue_index
from knowledge.jobs.repository import JobRepository, job_dict


class JobService:
    def __init__(self, sessions, embedding_profile):
        self.sessions, self.embedding_profile = sessions, embedding_profile

    async def enqueue_index(self, principal, revision_ids):
        principal.require("jobs:manage")
        if not revision_ids:
            raise AppError(422, "select_sources", "즉시 색인할 승인 문헌을 선택하세요.")
        async with self.sessions() as session, session.begin():
            result = []
            for revision_id in sorted(set(revision_ids)):
                revision, document = await DocumentRepository(session).revision(principal, revision_id, for_update=True)
                if (revision.review_status != "approved" or document.visibility != "shared_candidate"
                    or document.withdrawn or document.current_revision_id != revision.id):
                    raise AppError(409, "not_approved_current_source", "현재 승인된 공용 문헌 판본만 색인할 수 있습니다.")
                job = await enqueue_index(session, revision, self.embedding_profile, principal.id)
                await session.flush()
                result.append(job_dict(job))
            return {"items": result}

    async def list(self, principal, kind=None):
        async with self.sessions() as session:
            return {"items": [job_dict(job) for job in await JobRepository(session).visible(principal, kind)]}

    async def cancel(self, principal, job_id):
        async with self.sessions() as session, session.begin():
            job = await JobRepository(session).owned(principal, job_id, lock=True)
            if job.status in ("pending", "running"):
                job.status, job.finished_at = "cancelled", utcnow()
                if job.kind == "index":
                    revision = await session.get(DocumentRevision, job.payload["sourceRevisionId"], with_for_update=True)
                    if revision and revision.index_status == "indexing":
                        revision.index_status = "pending"
            return job_dict(job)

    async def retry(self, principal, job_id):
        async with self.sessions() as session, session.begin():
            job = await JobRepository(session).owned(principal, job_id, lock=True)
            if job.status not in ("failed", "cancelled"):
                raise AppError(409, "job_not_retryable", "실패하거나 취소된 작업만 재시도할 수 있습니다.")
            JobRepository.restart(job)
            return job_dict(job)
