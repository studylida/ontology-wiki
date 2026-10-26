import asyncio

import pytest
from sqlalchemy import select

from knowledge.conversations.entities import Message
from knowledge.core.errors import AppError
from knowledge.core.ids import new_id
from knowledge.documents.dto import MetadataPatch
from knowledge.documents.entities import DocumentRevision, Passage
from knowledge.documents.service import DocumentService
from knowledge.ontology.entities import Concept, ConceptSourceView
from knowledge.ontology.service import OntologyService
from knowledge.rag.dto import AnswerRequest
from test_rag_contract import indexed_source


@pytest.mark.asyncio
async def test_metadata_correction_marks_history_and_removes_stale_cards_from_replay(app, sessions, settings, principal, reviewer, embedding_client):
    source = await indexed_source(sessions, settings, principal, reviewer, embedding_client)
    async with sessions() as session, session.begin():
        revision = await session.get(DocumentRevision, source["currentRevisionId"])
        passage = await session.scalar(select(Passage).where(Passage.source_revision_id == revision.id))
        refs = [{"sourceRevisionId": revision.id, "passageId": passage.id}]
        concept = Concept(id=new_id("concept"), name="DRAM", description="문헌의 DRAM 설명", evidence_refs=refs)
        session.add(concept)
        await session.flush()
        session.add(ConceptSourceView(concept_id=concept.id, source_revision_id=revision.id, aspect="definition",
            summary="기존 출처 해석", attribution={"publisher": "samsung", "publisherId": "samsung", "sourceType": "official",
                "attributionBasis": "publisher_metadata"}, metadata_version=1, metadata_hash=revision.metadata_hash,
            input_hash="test-input", evidence_refs=refs))
    answers = app.state.services.answers
    handle = await answers.create(principal, AnswerRequest(clientRequestId="history-metadata", message="DRAM 설명"))
    await asyncio.wait_for(answers.runtimes[handle["runId"]].task, 10)
    original = await answers.get(principal, handle["runId"])
    assert len(original["message"]["sourceViews"]) == 1
    await DocumentService(sessions, settings).patch_metadata(reviewer, source["currentRevisionId"],
        MetadataPatch(author="외부 기고자", attributedTo="외부 기고자", attributionBasis="author_byline"))
    protected = await answers.get(principal, handle["runId"])
    assert protected["message"]["content"] == original["message"]["content"]
    assert protected["message"]["sourceViews"] == []
    assert any("정정된 과거 답변" in text for text in protected["message"]["warnings"])
    assert protected["message"]["citations"][0]["historicalMetadata"] is True
    async with sessions() as session:
        saved = await session.get(Message, handle["messageId"])
        assert len(saved.source_views) == 1, "Historical DB snapshots are preserved"
    async def disconnected():
        return False
    events = [event async for event in answers.event_stream(principal, handle["runId"], 0, disconnected)]
    assert not any(event["type"] == "source_view.add" for event in events if event)
    assert any("정정된 과거 답변" in text for text in events[-1]["data"]["warnings"])


@pytest.mark.asyncio
async def test_unpublished_concept_names_are_not_exposed_by_read_api(sessions, settings, principal):
    async with sessions() as session, session.begin():
        concept = Concept(id=new_id("concept"), name="비공개 프로젝트 공정", aliases=["secret codename"],
                          description="미확인 내부 설명", evidence_refs=[])
        session.add(concept)
        await session.flush()
        concept_id = concept.id
    service = OntologyService(sessions)
    assert (await service.concepts(principal))["items"] == []
    with pytest.raises(AppError) as error:
        await service.concept(principal, concept_id)
    assert error.value.status_code == 404
