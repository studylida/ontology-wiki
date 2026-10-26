import asyncio
from pathlib import Path

import pytest
from sqlalchemy import func, select

from knowledge.conversations.entities import Conversation
from knowledge.core.errors import AppError
from knowledge.core.ids import new_id
from knowledge.documents.entities import Document, DocumentAttachment, DocumentRevision
from knowledge.documents.parsing import save_raw
from knowledge.research.dto import TransferRequest
from knowledge.research.entities import ResearchItem
from knowledge.research.service import ResearchService


async def seed_research(sessions, settings, principal):
    raw_path = save_raw(settings.storage_path, b"original public source bytes")
    async with sessions() as session, session.begin():
        conversation = Conversation(id=new_id("conv"), owner_id=principal.id, title="문헌 조사 대화")
        session.add(conversation)
        await session.flush()
        item = ResearchItem(id=new_id("paper"), owner_id=principal.id, conversation_id=conversation.id,
            query="개인 프로젝트 조건", title="공개 자료", url="https://example.org/source", content="공개 본문 설명",
            read_scope="partial", metadata_json={"publisher": "기술 커뮤니티", "author": "외부 작성자",
                "attributedTo": "외부 작성자", "attributionBasis": "author_byline", "sourceType": "community",
                "rawPath": raw_path, "mediaType": "application/pdf"})
        session.add(item)
        await session.flush()
        return conversation.id, item.id, raw_path


@pytest.mark.asyncio
async def test_concurrent_transfer_is_atomic_and_keeps_original_and_attribution(sessions, settings, principal, generation_client):
    conversation_id, item_id, raw_path = await seed_research(sessions, settings, principal)
    service = ResearchService(sessions, settings, generation_client)
    body = TransferRequest(conversationId=conversation_id, items=[{"id": item_id}], query="개인 질문", conditions="비밀 실험 조건")
    first, second = await asyncio.gather(service.transfer(principal, body), service.transfer(principal, body))
    assert first["attachmentIds"] == second["attachmentIds"]
    assert len(first["submittedDocumentIds"] + second["submittedDocumentIds"]) == 1
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(Document)) == 1
        assert await session.scalar(select(func.count()).select_from(DocumentRevision)) == 1
        assert await session.scalar(select(func.count()).select_from(DocumentAttachment)) == 1
        revision = await session.scalar(select(DocumentRevision))
        assert revision.raw_path == raw_path and revision.media_type == "application/pdf"
        assert revision.review_status == "pending"
        assert revision.metadata_json["attributedTo"] == "외부 작성자"
        assert "비밀 실험 조건" not in str(revision.metadata_json) + revision.content
        assert "개인 질문" not in str(revision.metadata_json) + revision.content
    assert (Path(settings.storage_path) / raw_path).read_bytes() == b"original public source bytes"


@pytest.mark.asyncio
async def test_transfer_rejects_an_inaccessible_item_without_partial_documents(sessions, settings, principal, other_principal, generation_client):
    conversation_id, item_id, _ = await seed_research(sessions, settings, principal)
    _, other_item, _ = await seed_research(sessions, settings, other_principal)
    service = ResearchService(sessions, settings, generation_client)
    with pytest.raises(AppError) as caught:
        await service.transfer(principal, TransferRequest(conversationId=conversation_id,
            items=[{"id": item_id}, {"id": other_item}], query="검토"))
    assert caught.value.status_code == 404
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(Document)) == 0
        assert await session.scalar(select(func.count()).select_from(DocumentAttachment)) == 0
