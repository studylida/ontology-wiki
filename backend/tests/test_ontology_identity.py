import asyncio
import json

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from knowledge.documents.dto import ReviewRequest
from knowledge.documents.entities import Passage
from knowledge.documents.service import DocumentService
from knowledge.integrations.providers import ProviderDelta
from knowledge.jobs.entities import Job
from knowledge.ontology.entities import Concept, ConceptRelation, ConceptSourceView
from knowledge.ontology.extraction import ExtractedConcept, process_ontology_job
from knowledge.ontology.identity import canonical_type
from knowledge.ontology.repository import OntologyRepository
from test_rag_contract import indexed_source


class IdentityGenerator:
    model = "fixture-ontology-identity"

    def __init__(self, concepts, *, relations=None, barrier=None):
        self.concepts, self.relations, self.barrier = concepts, relations or [], barrier

    async def stream(self, messages, **kwargs):
        source = json.loads(messages[1]["content"])
        passage_id = source["passages"][0]["passageId"]
        if self.barrier:
            await self.barrier.wait()
        concepts = [{"aliases": [], "description": "이 문헌의 조건을 가진 설명", "aspect": "definition",
                     "conditions": None, **item, "passageIds": [passage_id]} for item in self.concepts]
        relations = [{"summary": "이 문헌의 관계", "conditions": None, **item,
                      "passageIds": [passage_id]} for item in self.relations]
        yield ProviderDelta(text=json.dumps({"concepts": concepts, "relations": relations}, ensure_ascii=False))
        yield ProviderDelta(usage={"source": "fixture", "model": self.model, "calls": 0,
                                  "fixtureCalls": 1, "costUsd": None, "costStatus": "fixture"})


async def prepare_job(sessions, settings, principal, reviewer, embedding_client, publisher):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client, publisher=publisher,
        text=f"{publisher}의 원문은 HBM과 Wire Bonding의 명시된 개념과 적용 조건을 설명한다.")
    async with sessions() as session, session.begin():
        revision_id = source["currentRevisionId"]
        job = await session.scalar(select(Job).where(Job.kind == "ontology_extract",
            Job.payload["sourceRevisionId"].astext == revision_id))
        job.status, job.attempts = "running", 1
        passage = await session.scalar(select(Passage).where(Passage.source_revision_id == revision_id))
        return source, job.id, [{"sourceRevisionId": revision_id, "passageId": passage.id}]


@pytest.mark.parametrize("items", [
    [{"name": "HBM", "type": "메모리 제품"},
     {"name": "HBM", "type": "메모리 반도체", "aliases": ["High Bandwidth Memory"]},
     {"name": "High Bandwidth Memory", "type": "device"}],
    [{"name": "와이어본딩", "type": "공정", "aliases": ["Wire Bonding"]},
     {"name": "와이어 본딩 (Wire Bonding)", "type": "칩 연결 방식", "aliases": ["Ｗｉｒｅ　Ｂｏｎｄｉｎｇ", "와이어 본딩"]},
     {"name": "와이어 본딩", "type": "process"}],
])
@pytest.mark.asyncio
async def test_three_sources_reuse_one_identity_and_keep_each_explanation(sessions, settings, principal, reviewer, embedding_client, items):
    source_ids = []
    for i, item in enumerate(items):
        source, job_id, _ = await prepare_job(sessions, settings, principal, reviewer, embedding_client, f"publisher-{i}")
        source_ids.append(source["currentRevisionId"])
        item = {**item, "description": f"출처 {i}의 고유 해석", "conditions": f"출처 {i}의 조건"}
        result = await process_ontology_job(sessions, IdentityGenerator([item]), job_id, settings)
        assert result["identityIssues"] == [] and result["sourceViews"] == 1
        assert result["createdConcepts"] == (1 if i == 0 else 0)
        assert result["reusedConcepts"] == (0 if i == 0 else 1)
    async with sessions() as session:
        concepts = list((await session.scalars(select(Concept))).all())
        assert len(concepts) == 1
        assert concepts[0].description == "출처 0의 고유 해석"
        assert concepts[0].aliases == items[0].get("aliases", [])
        views = list((await session.scalars(select(ConceptSourceView).where(ConceptSourceView.status == "active"))).all())
        assert len(views) == 3 and {v.concept_id for v in views} == {concepts[0].id}
        assert {v.source_revision_id for v in views} == set(source_ids)
        assert {v.conditions for v in views} == {f"출처 {i}의 조건" for i in range(3)}
        assert {v.attribution["publisherId"] for v in views} == {f"publisher-{i}" for i in range(3)}


@pytest.mark.asyncio
async def test_legacy_identity_is_reused_without_rewriting_original_fields(sessions, settings, principal, reviewer, embedding_client):
    _, old_job, old_refs = await prepare_job(sessions, settings, principal, reviewer, embedding_client, "old-public")
    async with sessions() as session, session.begin():
        original = Concept(name="HBM", type="메모리 제품", aliases=["High Bandwidth Memory"],
                           description="기존 전문가 설명", evidence_refs=old_refs, origin="legacy_source_linked")
        session.add(original)
        await session.flush()
        concept_id = original.id
    _, job_id, _ = await prepare_job(sessions, settings, principal, reviewer, embedding_client, "new-public")
    result = await process_ontology_job(sessions, IdentityGenerator([{"name": "HBM", "type": "메모리 반도체"}]), job_id, settings)
    assert result["createdConcepts"] == 0 and result["reusedConcepts"] == 1
    async with sessions() as session:
        concepts = list((await session.scalars(select(Concept))).all())
        assert len(concepts) == 1 and concepts[0].id == concept_id
        assert concepts[0].type == "메모리 제품" and concepts[0].description == "기존 전문가 설명"
        assert concepts[0].evidence_refs == old_refs and concepts[0].origin == "legacy_source_linked"


@pytest.mark.parametrize("existing_types,expected", [
    (["메모리 제품", "메모리 반도체"], "ambiguous"),
    (["process", "device"], "ambiguous"),
    (["process"], "type_conflict"),
    (["미확인 제품 범주"], "unknown_type"),
])
@pytest.mark.asyncio
async def test_existing_ambiguity_never_merges_deletes_or_creates_another_duplicate(sessions, settings, principal, reviewer, embedding_client, existing_types, expected):
    _, job_id, refs = await prepare_job(sessions, settings, principal, reviewer, embedding_client, "public")
    async with sessions() as session, session.begin():
        for kind in existing_types:
            session.add(Concept(name="HBM", type=kind, aliases=["High Bandwidth Memory"],
                                description="보존할 기존 설명", evidence_refs=refs))
    result = await process_ontology_job(sessions, IdentityGenerator([{"name": "HBM", "type": "device"}]), job_id, settings)
    assert result["createdConcepts"] == 0 and result["sourceViews"] == 0
    assert result["identityCoverage"] == "partial" and result["identityIssues"][0]["reason"] == expected
    async with sessions() as session:
        concepts = list((await session.scalars(select(Concept))).all())
        assert len(concepts) == len(existing_types)
        assert sorted(c.type for c in concepts) == sorted(existing_types)
        assert all(c.description == "보존할 기존 설명" for c in concepts)


@pytest.mark.asyncio
async def test_parallel_extractions_with_shared_alias_create_only_one_concept(sessions, settings, principal, reviewer, embedding_client):
    jobs = [await prepare_job(sessions, settings, principal, reviewer, embedding_client, f"parallel-{i}") for i in range(2)]
    barrier = asyncio.Barrier(2)
    generators = [IdentityGenerator([{"name": name, "type": "process", "aliases": ["Wire Bonding"]}], barrier=barrier)
                  for name in ("와이어본딩", "와이어 본딩")]
    results = await asyncio.wait_for(asyncio.gather(*[
        process_ontology_job(sessions, generator, job[1], settings) for generator, job in zip(generators, jobs)]), 10)
    assert sum(r["createdConcepts"] for r in results) == 1 and sum(r["reusedConcepts"] for r in results) == 1
    async with sessions() as session:
        assert len(list((await session.scalars(select(Concept))).all())) == 1
        assert len(list((await session.scalars(select(ConceptSourceView))).all())) == 2


@pytest.mark.asyncio
async def test_unpublished_identity_does_not_leak_by_reuse(sessions, settings, principal, reviewer, embedding_client):
    _, job_id, _ = await prepare_job(sessions, settings, principal, reviewer, embedding_client, "public")
    async with sessions() as session, session.begin():
        hidden = Concept(name="비공개 내부 이름", type="device", aliases=["HBM"],
                         description="공개 근거가 없는 내부 내용", evidence_refs=[])
        session.add(hidden)
        await session.flush()
        hidden_id = hidden.id
    result = await process_ontology_job(sessions, IdentityGenerator([{"name": "HBM", "type": "device"}]), job_id, settings)
    assert result["createdConcepts"] == 1 and result["reusedConcepts"] == 0
    async with sessions() as session:
        view = await session.scalar(select(ConceptSourceView))
        assert view.concept_id != hidden_id


@pytest.mark.asyncio
async def test_source_specific_alias_stops_matching_after_source_withdrawal(sessions, settings, principal, reviewer, embedding_client):
    _, first_job, _ = await prepare_job(sessions, settings, principal, reviewer, embedding_client, "first")
    await process_ontology_job(sessions, IdentityGenerator([{"name": "HBM", "type": "device"}]), first_job, settings)
    source, second_job, _ = await prepare_job(sessions, settings, principal, reviewer, embedding_client, "second")
    await process_ontology_job(sessions, IdentityGenerator([{"name": "HBM", "type": "device", "aliases": ["High Bandwidth Memory"]}]), second_job, settings)
    async with sessions() as session:
        candidates = await OntologyRepository(session).identity_candidates()
        assert "High Bandwidth Memory" in candidates[0].labels
    await DocumentService(sessions, settings).review(reviewer, source["currentRevisionId"], ReviewRequest(decision="withdraw", reason="출처 철회"))
    async with sessions() as session:
        candidates = await OntologyRepository(session).identity_candidates()
        assert "High Bandwidth Memory" not in candidates[0].labels


@pytest.mark.parametrize("conditions,expected_count", [(None, 0), ("   ", 0), ("원문이 명시한 동일 목적과 적용 조건에서만", 1)])
@pytest.mark.asyncio
async def test_alternative_relation_requires_conditions_without_discarding_concepts(sessions, settings, principal, reviewer, embedding_client, conditions, expected_count):
    _, job_id, _ = await prepare_job(sessions, settings, principal, reviewer, embedding_client, "alternatives")
    generator = IdentityGenerator([{"name": "방법A", "type": "process"}, {"name": "방법B", "type": "process"}],
        relations=[{"fromName": "방법A", "toName": "방법B", "type": "alternative_to", "conditions": conditions}])
    result = await process_ontology_job(sessions, generator, job_id, settings)
    assert result["sourceViews"] == 2 and result["relations"] == expected_count
    if expected_count == 0:
        assert result["relationIssues"][0]["reason"] == "missing_alternative_conditions"
    async with sessions() as session:
        assert len(list((await session.scalars(select(ConceptRelation))).all())) == expected_count


def test_new_types_use_small_enum_and_do_not_guess_arbitrary_labels():
    assert canonical_type("메모리 제품") == canonical_type("메모리 반도체") == "device"
    assert canonical_type("공정") == canonical_type("칩 연결 방식") == "process"
    assert canonical_type("패키징 방식") is None
    assert canonical_type("미확인 특수 공정 범주") is None
    with pytest.raises(ValidationError):
        ExtractedConcept(name="시험 개념", type="미확인 특수 공정 범주", description="근거", passageIds=["p"])
