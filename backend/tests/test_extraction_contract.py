import json

import pytest
from sqlalchemy import select

from knowledge.core.errors import AppError
from knowledge.integrations.providers import ProviderDelta
from knowledge.jobs.entities import Job
from knowledge.ontology.entities import ConceptRelation, ConceptSourceView
from knowledge.ontology.extraction import process_ontology_job
from knowledge.documents.parsing import model_source_metadata
from test_rag_contract import indexed_source


class SourceContractGenerator:
    model = "fixture-structured-contract"

    def __init__(self, *, invalid_conditions=False):
        self.invalid_conditions = invalid_conditions
        self.input = None
        self.schema = None

    async def stream(self, messages, **kwargs):
        self.schema = json.loads(messages[0]["content"].split("RESPONSE_SCHEMA_JSON\n", 1)[1])
        self.input = json.loads(messages[1]["content"])
        passage_id = self.input["passages"][0]["passageId"]
        conditions = ["조건 배열"] if self.invalid_conditions else None
        concepts = [{"name": name, "type": "process", "aliases": [], "description": f"원문이 설명하는 {name}",
            "passageIds": [passage_id], "aspect": "principle", "conditions": conditions} for name in ("식각", "세정")]
        result = {"concepts": concepts, "relations": [{"fromName": "식각", "toName": "세정", "type": "precedes",
            "summary": "이 문헌의 공정 순서", "conditions": None, "passageIds": [passage_id]}]}
        yield ProviderDelta(text=json.dumps(result, ensure_ascii=False), model=self.model)
        yield ProviderDelta(usage={"provider": "fixture", "model": self.model, "source": "fixture", "calls": 0,
            "fixtureCalls": 1, "costUsd": None, "costStatus": "fixture", "totalTokens": None})


def test_model_metadata_excludes_old_corrections_and_local_artifact_paths():
    stored = {"publisher": "원자료 발행처", "documentForm": "edited_derivative", "url": "https://example.org/source",
              "editorialCorrections": ["오류였던 과거 주장"], "originalFile": "C:/private/source.md",
              "sourceMapPath": "internal.bin", "reviewScope": "검토자용 기록"}
    supplied = model_source_metadata(stored)
    assert set(supplied) == {"publisher", "documentForm", "url"}
    assert stored["editorialCorrections"] == ["오류였던 과거 주장"]


async def setup_job(sessions, settings, principal, reviewer, embedding_client):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client,
                                  text="이 문헌의 공정에서는 식각 후 세정을 수행한다.")
    async with sessions() as session, session.begin():
        job = await session.scalar(select(Job).where(Job.kind == "ontology_extract"))
        job.status, job.attempts = "running", 1
        return source, job.id


@pytest.mark.asyncio
async def test_source_extraction_uses_typed_schema_and_only_public_source_input(sessions, settings, principal, reviewer, embedding_client):
    source, job_id = await setup_job(sessions, settings, principal, reviewer, embedding_client)
    generator = SourceContractGenerator()
    result = await process_ontology_job(sessions, generator, job_id, settings)
    assert result["sourceViews"] == 2 and result["relations"] == 1
    assert result["semanticValidation"] == "not_human_reviewed"
    assert set(generator.input) == {"title", "metadata", "passages"}
    schema = generator.schema["$defs"]["ExtractedConcept"]["properties"]
    assert {item["type"] for item in schema["conditions"]["anyOf"]} == {"string", "null"}
    async with sessions() as session:
        views = list((await session.scalars(select(ConceptSourceView))).all())
        assert all(view.source_revision_id == source["currentRevisionId"] for view in views)
        assert all(view.attribution["attributedTo"] is None for view in views)
        relation = await session.scalar(select(ConceptRelation))
        assert relation.type == "precedes" and relation.status == "machine_extracted"


@pytest.mark.asyncio
async def test_schema_failure_preserves_observed_usage_and_writes_no_claims(sessions, settings, principal, reviewer, embedding_client):
    _, job_id = await setup_job(sessions, settings, principal, reviewer, embedding_client)
    with pytest.raises(AppError) as invalid:
        await process_ontology_job(sessions, SourceContractGenerator(invalid_conditions=True), job_id, settings)
    assert invalid.value.code == "extraction_schema_invalid"
    assert invalid.value.usage["fixtureCalls"] == 1 and invalid.value.usage["costUsd"] is None
    async with sessions() as session:
        assert await session.scalar(select(ConceptSourceView)) is None
        assert await session.scalar(select(ConceptRelation)) is None
