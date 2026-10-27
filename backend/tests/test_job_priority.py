from datetime import timedelta

import pytest

from knowledge.core.ids import utcnow
from knowledge.jobs.repository import JobRepository


@pytest.mark.asyncio
async def test_ready_index_precedes_derived_jobs_but_future_index_does_not(sessions):
    async with sessions() as session, session.begin():
        repo = JobRepository(session)
        old = await repo.enqueue("source_view", "older", {}, available_at=utcnow() - timedelta(hours=1))
        await repo.enqueue("index", "future", {}, available_at=utcnow() + timedelta(hours=1))
        ready = await repo.enqueue("index", "ready", {})
        first = await repo.claim()
        assert first.id == ready.id and first.status == "running"
        await session.flush()
        second = await repo.claim()
        assert second.id == old.id
