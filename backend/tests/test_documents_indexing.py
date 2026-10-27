from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from knowledge.core.errors import AppError
from knowledge.core.ids import new_id
from knowledge.documents.dto import MetadataPatch, NewDocument, NewRevision, ReviewRequest
from knowledge.documents.entities import Document, DocumentRevision, EmbeddingRecord, Passage
from knowledge.documents.repository import DocumentRepository, citation_dict
from knowledge.documents.service import DocumentService
from knowledge.jobs.entities import Job
from knowledge.jobs.indexing import enqueue_index, process_index_job, schedule_daily
from knowledge.integrations.providers import FixtureEmbeddingClient
from knowledge.ontology.entities import Concept, ConceptSourceView
from knowledge.ontology.repository import OntologyRepository


@pytest.mark.asyncio
async def test_document_form_survives_ingestion_citation_and_revision(sessions, settings, reviewer):
    service = DocumentService(sessions, settings)
    text = '---\ndocument_form: edited_derivative\n---\n# 편집본\n수정한 내용'
    doc = await service.create(reviewer, NewDocument(title="편집본", content=text, sourceType="manufacturer_glossary"))
    revision_id = doc["currentRevisionId"]
    async with sessions() as session:
        repo = DocumentRepository(session)
        rev, document = await repo.revision(reviewer, revision_id)
        passage = await session.scalar(select(Passage).where(Passage.source_revision_id == revision_id))
        cite = citation_dict(passage, rev, document)
        assert cite["sourceType"] == "manufacturer_glossary"
        assert cite["documentForm"] == "edited_derivative"
    await service.patch_metadata(reviewer, revision_id, MetadataPatch(documentForm="editorial_summary"))
    assert (await service.detail(reviewer, revision_id))["metadata"]["documentForm"] == "editorial_summary"
    explicit = await service.create(reviewer, NewDocument(title="명시적 유형", content=text, documentForm="unknown"))
    assert (await service.detail(reviewer, explicit["currentRevisionId"]))["metadata"]["documentForm"] == "unknown"
    invalid = await service.create(reviewer, NewDocument(title="미확인 유형", content="---\ndocument_form: [not, valid]\n---\n본문"))
    assert (await service.detail(reviewer, invalid["currentRevisionId"]))["metadata"]["documentForm"] is None
    legacy = await service.create(reviewer, NewDocument(title="HDD 편집본", content="---\nsource_type: manufacturer_glossary\neditorial_derivative: true\n---\n본문"))
    assert (await service.detail(reviewer, legacy["currentRevisionId"]))["metadata"]["documentForm"] == "edited_derivative"
    non_boolean = await service.create(reviewer, NewDocument(title="문자 선언", content='---\neditorial_derivative: "true"\n---\n본문'))
    assert (await service.detail(reviewer, non_boolean["currentRevisionId"]))["metadata"]["documentForm"] is None
    new = await service.add_revision(reviewer, doc["id"], NewRevision(content=text + "\n새 판본"))
    assert (await service.detail(reviewer, new["currentRevisionId"]))["metadata"]["documentForm"] == "editorial_summary"
    assert (await service.detail(reviewer, revision_id))["metadata"]["documentForm"] == "editorial_summary"


async def approve_and_queue(sessions, settings, reviewer, embedding, *, publisher="test_publisher", content="테스트용 공정 원문. 식각은 조건에 따라 재료를 제거한다."):
    service = DocumentService(sessions, settings)
    document = await service.create(reviewer, NewDocument(title="TEST SOURCE", content=content,
        visibility="shared_candidate", publisher="테스트 발행자", publisher_id=publisher, source_type="test_fixture"))
    await service.review(reviewer, document["currentRevisionId"], ReviewRequest(decision="approve", reason="test fixture approval"))
    async with sessions() as session, session.begin():
        revision = await session.get(DocumentRevision, document["currentRevisionId"])
        job = await enqueue_index(session, revision, embedding.profile_id, reviewer.id)
        job.status = "running"
        job_id = job.id
    return document, job_id


@pytest.mark.asyncio
async def test_approval_is_separate_from_index_and_old_revision_is_preserved(sessions, settings, reviewer, principal, embedding_client):
    document, job_id = await approve_and_queue(sessions, settings, reviewer, embedding_client)
    old_id = document["currentRevisionId"]
    async with sessions() as session:
        assert await DocumentRepository(session).resolve_snapshot(principal) == []
    result = await process_index_job(sessions, embedding_client, job_id)
    assert result["status"] == "succeeded" and result["embedded"] > 0
    async with sessions() as session:
        assert await DocumentRepository(session).resolve_snapshot(principal) == [old_id]
        old_text = (await session.get(DocumentRevision, old_id)).content
    service = DocumentService(sessions, settings)
    updated = await service.add_revision(reviewer, document["id"], NewRevision(content=old_text + "\n새 조건을 덧붙였다."))
    async with sessions() as session:
        assert await DocumentRepository(session).resolve_snapshot(principal) == [old_id]
        assert (await session.get(DocumentRevision, old_id)).content == old_text
        assert updated["currentRevisionId"] != old_id


@pytest.mark.asyncio
async def test_withdrawal_during_embedding_cannot_activate_late_result(sessions, settings, reviewer, principal):
    class WithdrawDuringCall(FixtureEmbeddingClient):
        async def embed(self, texts):
            await DocumentService(sessions, settings).review(reviewer, document["currentRevisionId"],
                ReviewRequest(decision="withdraw", reason="concurrent access withdrawal"))
            return await super().embed(texts)
    embedding = WithdrawDuringCall()
    document, job_id = await approve_and_queue(sessions, settings, reviewer, embedding)
    result = await process_index_job(sessions, embedding, job_id)
    assert result["status"] == "superseded"
    async with sessions() as session:
        assert (await session.get(Document, document["id"])).active_revision_id is None
        assert not await DocumentRepository(session).ensure_readable(principal, [document["currentRevisionId"]])
        assert await DocumentRepository(session).resolve_snapshot(principal) == []


@pytest.mark.asyncio
async def test_private_pending_and_withdrawn_sources_do_not_enter_shared_snapshot(sessions, settings, reviewer, principal, other_principal):
    service = DocumentService(sessions, settings)
    doc = await service.create(principal, NewDocument(title="PRIVATE TEST", content="개인 조건 메모", visibility="private"))
    async with sessions() as session:
        repo = DocumentRepository(session)
        assert await repo.resolve_snapshot(principal) == []
        assert await repo.ensure_readable(principal, [doc["currentRevisionId"]])
        assert not await repo.ensure_readable(other_principal, [doc["currentRevisionId"]])
        with pytest.raises(AppError):
            await repo.selected_context(other_principal, [doc["currentRevisionId"]])


@pytest.mark.asyncio
async def test_cache_reused_and_metadata_change_invalidates_view_without_embedding(sessions, settings, reviewer, principal, embedding_client):
    document, job_id = await approve_and_queue(sessions, settings, reviewer, embedding_client)
    await process_index_job(sessions, embedding_client, job_id)
    async with sessions() as session, session.begin():
        revision = await session.get(DocumentRevision, document["currentRevisionId"])
        passage = await session.scalar(select(Passage).where(Passage.source_revision_id == revision.id))
        concept = Concept(id=new_id("concept"), name="식각", aliases=[], evidence_refs=[{"sourceRevisionId": revision.id, "passageId": passage.id}])
        session.add(concept)
        await session.flush()
        view = ConceptSourceView(concept_id=concept.id, source_revision_id=revision.id, aspect="principle",
            summary="테스트 발행 자료의 설명", conditions=None, attribution={"publisher": "테스트 발행자", "attributedTo": None},
            metadata_version=revision.metadata_version, metadata_hash=revision.metadata_hash, input_hash="a" * 64,
            evidence_refs=[{"sourceRevisionId": revision.id, "passageId": passage.id}])
        session.add(view)
        concept_id = concept.id
        count_before = await session.scalar(select(func.count()).select_from(EmbeddingRecord))
    async with sessions() as session:
        assert len((await OntologyRepository(session).source_views(principal, [concept_id]))["items"]) == 1
    changed = await DocumentService(sessions, settings).patch_metadata(reviewer, document["currentRevisionId"],
        MetadataPatch(author="외부 필자", attributed_to="외부 필자", attribution_basis="author_byline"))
    assert changed["invalidatedViews"] == 1 and changed["reembeddingRequired"] is False
    async with sessions() as session:
        assert (await OntologyRepository(session).source_views(principal, [concept_id]))["items"] == []
        assert await session.scalar(select(func.count()).select_from(EmbeddingRecord)) == count_before
        assert await session.scalar(select(func.count()).select_from(Job).where(Job.kind == "source_view")) == 1
    # Same input and profile: a requested reindex can reuse every cached vector.
    async with sessions() as session, session.begin():
        revision = await session.get(DocumentRevision, document["currentRevisionId"])
        job = await enqueue_index(session, revision, embedding_client.profile_id, reviewer.id)
        job.status = "running"
        second_job = job.id
    result = await process_index_job(sessions, embedding_client, second_job)
    assert result["embedded"] == 0 and result["reused"] >= 1


@pytest.mark.asyncio
async def test_each_requested_source_group_gets_its_own_candidates(sessions, settings, reviewer, principal, embedding_client):
    documents = []
    # A more frequent publisher must not suppress the explicitly requested smaller group.
    for publisher, text in [("large_group", "etch " * 60), ("small_group", "etch conditional alternative")]:
        document, job_id = await approve_and_queue(sessions, settings, reviewer, embedding_client, publisher=publisher, content=text)
        await process_index_job(sessions, embedding_client, job_id)
        documents.append(document)
    query = (await embedding_client.embed(["etch"])).vectors[0]
    groups = [{"groupId": "A", "publisherId": "large_group"}, {"groupId": "B", "publisherId": "small_group", "sourceType": "test_fixture"}, {"groupId": "missing", "publisherId": "not_present"}]
    async with sessions() as session:
        repo = DocumentRepository(session)
        snapshot = await repo.resolve_snapshot(principal, None, groups)
        result = await repo.search(principal, query, embedding_client.profile_id, "etch", snapshot, groups)
        coverage = {r["groupId"]: r["hitCount"] for r in result["groupCoverage"]}
        assert coverage["A"] and coverage["B"] and coverage["missing"] == 0
        assert {h["publisherId"] for h in result["hits"]} == {"large_group", "small_group"}


@pytest.mark.asyncio
async def test_daily_scheduler_runs_once_and_skips_obsolete_revision(sessions, settings, reviewer, embedding_client):
    doc, job_id = await approve_and_queue(sessions, settings, reviewer, embedding_client)
    new = await DocumentService(sessions, settings).add_revision(reviewer, doc["id"], NewRevision(content="새로 승인할 최신 원문"))
    await DocumentService(sessions, settings).review(reviewer, new["currentRevisionId"], ReviewRequest(decision="approve", reason="new source"))
    old_result = await process_index_job(sessions, embedding_client, job_id)
    assert old_result["status"] == "superseded"
    now = datetime(2026, 10, 26, 1, 0, tzinfo=timezone.utc)  # 10:00 Asia/Seoul
    assert await schedule_daily(sessions, settings, embedding_client.profile_id, now=now) == 1
    assert await schedule_daily(sessions, settings, embedding_client.profile_id, now=now) == 0


@pytest.mark.asyncio
async def test_reapproval_waits_for_index_and_reuses_original_vectors(sessions, settings, reviewer, principal, embedding_client):
    document, job_id = await approve_and_queue(sessions, settings, reviewer, embedding_client)
    await process_index_job(sessions, embedding_client, job_id)
    async with sessions() as session, session.begin():
        job = await session.get(Job, job_id)
        job.status = "succeeded"
    service = DocumentService(sessions, settings)
    await service.review(reviewer, document["currentRevisionId"], ReviewRequest(decision="withdraw", reason="철회"))
    await service.review(reviewer, document["currentRevisionId"], ReviewRequest(decision="approve", reason="문헌 재검토"))
    async with sessions() as session, session.begin():
        assert await DocumentRepository(session).resolve_snapshot(principal) == []
        revision = await session.get(DocumentRevision, document["currentRevisionId"])
        job = await enqueue_index(session, revision, embedding_client.profile_id, reviewer.id)
        assert job.status == "pending"
        job.status = "running"
    result = await process_index_job(sessions, embedding_client, job_id)
    assert result["embedded"] == 0 and result["reused"] > 0
    assert result["usage"]["calls"] == 0
    async with sessions() as session:
        assert await DocumentRepository(session).resolve_snapshot(principal) == [document["currentRevisionId"]]


@pytest.mark.asyncio
async def test_reindex_keeps_published_revision_searchable_during_call(sessions, settings, reviewer, principal, embedding_client):
    document, job_id = await approve_and_queue(sessions, settings, reviewer, embedding_client)
    await process_index_job(sessions, embedding_client, job_id)
    observed = []

    class AlternateProfile(FixtureEmbeddingClient):
        profile_id = "fixture:alternate-profile:1536:v1"
        async def embed(self, texts):
            async with sessions() as session:
                observed.extend(await DocumentRepository(session).resolve_snapshot(principal))
            return await super().embed(texts)

    alternate = AlternateProfile()
    async with sessions() as session, session.begin():
        revision = await session.get(DocumentRevision, document["currentRevisionId"])
        job = await enqueue_index(session, revision, alternate.profile_id, reviewer.id)
        job.status = "running"
        new_job_id = job.id
    assert (await process_index_job(sessions, alternate, new_job_id))["status"] == "succeeded"
    assert observed == [document["currentRevisionId"]]


@pytest.mark.asyncio
async def test_worker_restart_recovers_index_progress_atomically_and_keeps_published_revision(sessions, settings, reviewer, principal, embedding_client):
    from knowledge.jobs.worker import recover_interrupted_jobs
    document, old_job = await approve_and_queue(sessions, settings, reviewer, embedding_client)
    await process_index_job(sessions, embedding_client, old_job)
    old_revision = document["currentRevisionId"]
    service = DocumentService(sessions, settings)
    new = await service.add_revision(reviewer, document["id"], NewRevision(content="새 문헌의 작업 중 원문"))
    await service.review(reviewer, new["currentRevisionId"], ReviewRequest(decision="approve", reason="원문 검토"))
    async with sessions() as session, session.begin():
        revision = await session.get(DocumentRevision, new["currentRevisionId"])
        job = await enqueue_index(session, revision, embedding_client.profile_id, reviewer.id)
        job.status, revision.index_status = "running", "indexing"
        job_id = job.id
    assert await recover_interrupted_jobs(sessions) >= 1
    async with sessions() as session:
        assert (await session.get(Job, job_id)).status == "failed"
        assert (await session.get(DocumentRevision, new["currentRevisionId"])).index_status == "failed"
        assert (await session.get(DocumentRevision, old_revision)).index_status == "ready"
        assert await DocumentRepository(session).resolve_snapshot(principal) == [old_revision]


@pytest.mark.asyncio
async def test_late_usage_after_cancel_retry_is_assigned_to_old_attempt(sessions, settings, reviewer, generation_client):
    from knowledge.jobs.service import JobService
    from knowledge.jobs.worker import process_one

    class CancelAndRetryDuringCall(FixtureEmbeddingClient):
        async def embed(self, texts):
            jobs = JobService(sessions, self.profile_id)
            await jobs.cancel(reviewer, job_id)
            await jobs.retry(reviewer, job_id)
            return await super().embed(texts)

    embedding = CancelAndRetryDuringCall()
    document, job_id = await approve_and_queue(sessions, settings, reviewer, embedding)
    async with sessions() as session, session.begin():
        job = await session.get(Job, job_id)
        job.status = "pending"
    assert await process_one(sessions, embedding, generation_client, settings)
    async with sessions() as session:
        job = await session.get(Job, job_id)
        assert job.status == "pending" and job.usage is None
        assert job.result["attemptHistory"][-1]["usage"]["fixtureCalls"] == 1
        assert job.result["attemptHistory"][-1]["usage"]["calls"] == 0
        assert (await session.get(Document, document["id"])).active_revision_id is None
