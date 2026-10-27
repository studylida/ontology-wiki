from sqlalchemy import case, select
from sqlalchemy.dialects.postgresql import insert

from knowledge.core.ids import new_id, utcnow
from knowledge.core.errors import AppError
from knowledge.jobs.entities import Job


class JobRepository:
    def __init__(self, session):
        self.session = session

    async def enqueue(self, kind, dedupe_key, payload, owner_id=None, *, available_at=None):
        values = dict(id=new_id("job"), kind=kind, dedupe_key=dedupe_key, payload=payload,
                      owner_id=owner_id, status="pending", available_at=available_at or utcnow())
        await self.session.execute(insert(Job).values(**values).on_conflict_do_nothing(index_elements=["dedupe_key"]))
        return await self.session.scalar(select(Job).where(Job.dedupe_key == dedupe_key))

    async def claim(self):
        job = await self.session.scalar(select(Job).where(Job.status == "pending", Job.available_at <= utcnow())
            .order_by(case((Job.kind == "index", 0), else_=1), Job.available_at, Job.created_at)
            .with_for_update(skip_locked=True).limit(1))
        if job:
            job.status, job.started_at = "running", utcnow()
            job.attempts += 1
        return job

    async def owned(self, principal, job_id, *, lock=False):
        statement = select(Job).where(Job.id == job_id)
        if lock:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        job = await self.session.scalar(statement)
        if not job or (job.owner_id != principal.id and not (principal.can("jobs:manage") and job.kind != "personal_wiki")):
            raise AppError(404, "job_not_found", "작업을 찾을 수 없습니다.")
        return job

    async def visible(self, principal, kind=None):
        statement = select(Job)
        if principal.can("jobs:manage"):
            statement = statement.where((Job.owner_id == principal.id) | Job.kind.in_(["index", "ontology_extract", "source_view"]))
        else:
            statement = statement.where(Job.owner_id == principal.id)
        if kind:
            statement = statement.where(Job.kind == kind)
        return list((await self.session.scalars(statement.order_by(Job.created_at.desc()).limit(100))).all())

    @staticmethod
    def restart(job):
        history = list((job.result or {}).get("attemptHistory", []))
        history.append({"attempt": job.attempts, "status": job.status, "usage": job.usage,
                        "error": job.error, "finishedAt": job.finished_at.isoformat() if job.finished_at else None})
        job.result, job.progress, job.usage = {"attemptHistory": history}, {}, None
        job.status, job.available_at, job.error = "pending", utcnow(), None
        job.started_at = job.finished_at = None


def job_dict(job):
    return {"id": job.id, "kind": job.kind, "status": job.status, "progress": job.progress,
            "result": job.result, "error": job.error, "usage": job.usage, "attempts": job.attempts,
            "createdAt": job.created_at.isoformat(), "availableAt": job.available_at.isoformat(),
            "finishedAt": job.finished_at.isoformat() if job.finished_at else None}
