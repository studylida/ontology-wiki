"""Real isolated PostgreSQL tests; generation clients below are explicit JSON fakes."""
import hashlib
import json

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from knowledge.conversations.dto import ConversationPatch
from knowledge.conversations.entities import Conversation, Message
from knowledge.conversations.service import ConversationService
from knowledge.core.errors import AppError
from knowledge.core.ids import new_id
from knowledge.documents.entities import Document, DocumentRevision, Passage
from knowledge.identity.entities import User
from knowledge.integrations.providers import FixtureEmbeddingClient, FixtureGenerationClient, ProviderDelta
from knowledge.jobs.entities import Job
from knowledge.jobs.worker import process_one
from knowledge.personal_wiki.dto import OrganizeRequest, WikiPatch, WikiSettingsPatch, WikiUndo
from knowledge.personal_wiki.entities import PersonalWikiMessageState, PersonalWikiPage
from knowledge.personal_wiki.service import PersonalWikiService, enqueue_for_message


class JsonGenerationFake:
    model = "fixture-personal-wiki-json"

    def __init__(self, proposal, hook=None):
        self.proposal, self.hook = proposal, hook
        self.calls, self.messages = 0, []

    async def stream(self, messages, *, effort=None, cancel_event=None):
        self.calls += 1
        self.messages = messages
        if self.hook:
            await self.hook()
        yield ProviderDelta(text=json.dumps(self.proposal, ensure_ascii=False), model=self.model)
        yield ProviderDelta(usage={"model": self.model, "source": "fixture", "calls": 1,
            "inputTokens": 11, "outputTokens": 22, "totalTokens": 33,
            "costUsd": None, "costStatus": "fixture"}, model=self.model)


@pytest_asyncio.fixture
async def wiki_owner(seed_user):
    return await seed_user("wiki-owner", auto_wiki=True)


async def answer(sessions, owner, *, conversation_id=None, with_source=True):
    async with sessions() as session, session.begin():
        if conversation_id:
            conversation = await session.get(Conversation, conversation_id)
        else:
            conversation = Conversation(id=new_id("conv"), owner_id=owner.id, auto_wiki=True,
                                        title="본딩 검증 대화")
            session.add(conversation)
        evidence, document_id, revision_id = [], None, None
        if with_source:
            document = Document(id=new_id("doc"), owner_id=owner.id, title="개인 검증 원문", visibility="private")
            source = "테스트용 원문입니다. 실제 반도체 사실의 근거가 아닙니다. 본딩 조건 A."
            revision = DocumentRevision(id=new_id("rev"), document_id=document.id, content=source,
                content_hash=hashlib.sha256(source.encode()).hexdigest(), raw_path="test-fixture-only",
                metadata_json={"publisher": "fixture", "sourceType": "fixture"}, metadata_hash="fixture-meta-v1",
                review_status="pending")
            passage = Passage(id=new_id("psg"), source_revision_id=revision.id, ordinal=0,
                text=source, locator="검증 구간", embedding_text=source, input_hash=revision.content_hash)
            document.current_revision_id = revision.id
            session.add_all([document, revision, passage])
            document_id, revision_id = document.id, revision.id
            evidence = [{"id": passage.id, "passageId": passage.id, "sourceRevisionId": revision.id,
                         "title": document.title, "locator": passage.locator, "excerpt": source}]
        question = Message(id=new_id("msg"), conversation_id=conversation.id, role="user", content="본딩 조건을 정리해 줘")
        session.add(question)
        await session.flush()
        message = Message(id=new_id("msg"), conversation_id=conversation.id, role="assistant", status="completed",
                          content="본딩 조건 A에 관한 검증용 답변. 원문과 개인 대화 정리의 구분을 보존한다.", citations=evidence)
        session.add(message)
        await session.flush()
        return {"messageId": message.id, "conversationId": conversation.id,
                "documentId": document_id, "revisionId": revision_id, "citations": evidence}


def proposal(item, *, action="add", target=None, conditions=None):
    return {"action": action, "title": "본딩 조건별 개인 메모", "topic": "본딩",
            "summary": "검증용 개인 정리", "content": "검증용 본딩 정리. 조건과 한계를 보존한다.",
            "conditions": conditions or ["조건 A"], "limitations": ["fixture 데이터"],
            "citationIds": [c["id"] for c in item["citations"]], "targetPageId": target,
            "reason": "명시적 테스트 JSON"}


async def queued(sessions, owner, item, *, explicit=False):
    return await enqueue_for_message(sessions, owner, item["messageId"], explicit=explicit)


async def execute(sessions, settings, job_id, fake):
    assert await process_one(sessions, FixtureEmbeddingClient(), fake, settings)
    async with sessions() as session:
        job = await session.get(Job, job_id)
        return job


async def page_count(sessions):
    async with sessions() as session:
        return await session.scalar(select(func.count()).select_from(PersonalWikiPage))


async def saved(sessions, settings, owner, item):
    job = await queued(sessions, owner, item)
    done = await execute(sessions, settings, job["jobId"], JsonGenerationFake(proposal(item)))
    assert done.status == "succeeded", done.error
    return done.result["pageId"]


@pytest.mark.asyncio
async def test_automatic_organization_is_private_idempotent_and_evidence_linked(sessions, settings, wiki_owner, other_principal):
    item = await answer(sessions, wiki_owner)
    first, duplicate = await queued(sessions, wiki_owner, item), await queued(sessions, wiki_owner, item)
    assert first["jobId"] == duplicate["jobId"]
    fake = JsonGenerationFake(proposal(item))
    done = await execute(sessions, settings, first["jobId"], fake)
    assert done.status == "succeeded" and fake.calls == 1
    service = PersonalWikiService(sessions, settings)
    page = await service.get(wiki_owner, done.result["pageId"])
    assert page["originMessages"] == [{"messageId": item["messageId"], "conversationId": item["conversationId"]}]
    assert page["citations"][0]["sourceRevisionId"] == item["revisionId"]
    assert page["evidenceStatus"] == "source_linked"
    assert (await service.list(wiki_owner, "조건 A"))["items"][0]["id"] == page["id"]
    assert (await service.list(other_principal))["items"] == []
    with pytest.raises(AppError) as error:
        await service.get(other_principal, page["id"])
    assert error.value.status_code == 404
    assert (await queued(sessions, wiki_owner, item))["reason"] == "already_organized"
    assert await page_count(sessions) == 1
    assert done.usage["source"] == "fixture" and done.usage["costUsd"] is None


@pytest.mark.asyncio
async def test_settings_change_while_provider_runs_cancels_without_saving(sessions, settings, wiki_owner):
    item = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, item)
    async def disable():
        await PersonalWikiService(sessions, settings).patch_settings(wiki_owner, WikiSettingsPatch(autoOrganize=False))
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(proposal(item), disable))
    assert done.status == "cancelled"
    assert await page_count(sessions) == 0
    assert done.usage["totalTokens"] == 33  # observed fake usage survives cancellation


@pytest.mark.asyncio
async def test_conversation_exclusion_survives_reenable_and_policy_change(sessions, settings, wiki_owner, monkeypatch):
    item = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, item)
    conversations = ConversationService(sessions, settings)
    async def exclude():
        await conversations.patch(wiki_owner, item["conversationId"], ConversationPatch(autoWiki=False))
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(proposal(item), exclude))
    assert done.status == "cancelled" and await page_count(sessions) == 0
    await conversations.patch(wiki_owner, item["conversationId"], ConversationPatch(autoWiki=True))
    monkeypatch.setattr("knowledge.personal_wiki.service.POLICY_VERSION", "personal-wiki-v2")
    assert (await queued(sessions, wiki_owner, item))["reason"] == "message_excluded"
    async with sessions() as session:
        state = await session.get(PersonalWikiMessageState, (wiki_owner.id, item["messageId"]))
        assert state.suppression_reason == "conversation_excluded"


@pytest.mark.asyncio
async def test_answer_completed_while_conversation_excluded_is_not_backfilled(sessions, settings, wiki_owner):
    first = await answer(sessions, wiki_owner)
    conversations = ConversationService(sessions, settings)
    await conversations.patch(wiki_owner, first["conversationId"], ConversationPatch(autoWiki=False))
    later = await answer(sessions, wiki_owner, conversation_id=first["conversationId"])
    assert (await queued(sessions, wiki_owner, later))["reason"] == "message_excluded"
    await conversations.patch(wiki_owner, first["conversationId"], ConversationPatch(autoWiki=True))
    assert (await queued(sessions, wiki_owner, later))["reason"] == "message_excluded"


@pytest.mark.asyncio
async def test_delete_undo_and_explicit_reorganization_keep_cross_policy_exclusion(sessions, settings, wiki_owner, monkeypatch):
    item = await answer(sessions, wiki_owner)
    page_id = await saved(sessions, settings, wiki_owner, item)
    service = PersonalWikiService(sessions, settings)
    removed = await service.delete(wiki_owner, page_id)
    assert removed == {"id": page_id, "deleted": True, "version": 2}
    with pytest.raises(AppError) as error:
        await service.undo(wiki_owner, page_id, WikiUndo(expectedVersion=1))
    assert error.value.status_code == 409
    restored = await service.undo(wiki_owner, page_id, WikiUndo(expectedVersion=removed["version"]))
    assert restored["version"] == 3 and restored["content"]
    monkeypatch.setattr("knowledge.personal_wiki.service.POLICY_VERSION", "personal-wiki-v2")
    assert (await queued(sessions, wiki_owner, item))["reason"] == "message_excluded"
    manual = await queued(sessions, wiki_owner, item, explicit=True)
    assert manual["status"] == "pending"
    done = await execute(sessions, settings, manual["jobId"], JsonGenerationFake(proposal(item, action="merge", target=page_id)))
    assert done.status == "succeeded" and done.result["version"] == 4
    assert await page_count(sessions) == 1


@pytest.mark.asyncio
async def test_user_edit_during_generation_is_not_overwritten(sessions, settings, wiki_owner):
    item = await answer(sessions, wiki_owner)
    page_id = await saved(sessions, settings, wiki_owner, item)
    second = await answer(sessions, wiki_owner, conversation_id=item["conversationId"])
    pending = await queued(sessions, wiki_owner, second)
    service = PersonalWikiService(sessions, settings)
    async def edit():
        await service.patch(wiki_owner, page_id, WikiPatch(expectedVersion=1, content="사용자가 직접 고친 검증 문장"))
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(proposal(second, action="merge", target=page_id), edit))
    assert done.status == "superseded" and done.result["reason"] == "page_changed_by_user"
    page = await service.get(wiki_owner, page_id)
    assert page["content"] == "사용자가 직접 고친 검증 문장" and page["version"] == 2
    with pytest.raises(AppError) as error:
        await service.patch(wiki_owner, page_id, WikiPatch(expectedVersion=1, title="오래된 수정"))
    assert error.value.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", ["withdraw", "metadata", "answer_cancel", "job_cancel", "owner_disabled"])
async def test_current_permission_metadata_completion_and_cancellation_rechecked(sessions, settings, wiki_owner, mutation):
    item = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, item)
    async def mutate():
        async with sessions() as session, session.begin():
            if mutation == "withdraw":
                (await session.get(Document, item["documentId"])).withdrawn = True
            elif mutation == "metadata":
                row = await session.get(DocumentRevision, item["revisionId"])
                row.metadata_hash, row.metadata_version = "corrected-attribution", 2
            elif mutation == "answer_cancel":
                (await session.get(Message, item["messageId"])).status = "cancelled"
            elif mutation == "job_cancel":
                (await session.get(Job, pending["jobId"])).status = "cancelled"
            else:
                (await session.get(User, wiki_owner.id)).is_active = False
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(proposal(item), mutate))
    assert done.status in ("superseded", "cancelled")
    assert await page_count(sessions) == 0
    assert done.usage["totalTokens"] == 33


@pytest.mark.asyncio
async def test_revoked_source_redacts_titles_history_and_keyword_discovery(sessions, settings, wiki_owner):
    item = await answer(sessions, wiki_owner)
    page_id = await saved(sessions, settings, wiki_owner, item)
    async with sessions() as session, session.begin():
        (await session.get(Document, item["documentId"])).withdrawn = True
    service = PersonalWikiService(sessions, settings)
    page = await service.get(wiki_owner, page_id)
    assert page["title"] == "접근 제한된 개인 위키"
    assert page["status"] == "restricted" and page["content"] == "" and page["summary"] == ""
    assert page["versions"] == page["citations"] == page["originMessages"] == []
    assert (await service.list(wiki_owner, "본딩"))["items"] == []
    assert (await service.list(wiki_owner))["items"][0]["restricted"]


@pytest.mark.asyncio
async def test_non_json_fixture_fails_job_without_failing_original_answer(sessions, settings, wiki_owner):
    item = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, item)
    done = await execute(sessions, settings, pending["jobId"], FixtureGenerationClient())
    assert done.status == "failed" and done.error["code"] == "structured_output_invalid"
    assert done.usage["source"] == "fixture" and done.usage["costUsd"] is None
    assert await page_count(sessions) == 0
    async with sessions() as session:
        assert (await session.get(Message, item["messageId"])).status == "completed"


@pytest.mark.asyncio
async def test_invented_citation_is_not_stored_and_usage_is_preserved(sessions, settings, wiki_owner):
    item = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, item)
    invalid = proposal(item) | {"citationIds": ["invented-reference"]}
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(invalid))
    assert done.status == "failed" and done.error["code"] == "WIKI_INVALID_ORGANIZATION"
    assert done.usage["totalTokens"] == 33 and await page_count(sessions) == 0


@pytest.mark.asyncio
async def test_different_conditions_cannot_merge_but_can_be_separate_topic(sessions, settings, wiki_owner):
    first = await answer(sessions, wiki_owner)
    page_id = await saved(sessions, settings, wiki_owner, first)
    second = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, second)
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(
        proposal(second, action="merge", target=page_id, conditions=["조건 B"])))
    assert done.status == "superseded"
    assert done.result["reason"] == "conditions_differ_or_target_incomplete"
    explicit = await queued(sessions, wiki_owner, second, explicit=True)
    done = await execute(sessions, settings, explicit["jobId"], JsonGenerationFake(proposal(second, conditions=["조건 B"])))
    assert done.status == "succeeded" and await page_count(sessions) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("original,changed", [("1 mW", "1 MW"), ("10² nm", "102 nm")])
async def test_case_sensitive_units_remain_different_conditions(sessions, settings, wiki_owner, original, changed):
    first = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, first)
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(proposal(first, conditions=[original])))
    page_id = done.result["pageId"]
    second = await answer(sessions, wiki_owner)
    pending = await queued(sessions, wiki_owner, second)
    done = await execute(sessions, settings, pending["jobId"], JsonGenerationFake(
        proposal(second, action="merge", target=page_id, conditions=[changed])))
    assert done.status == "superseded" and done.result["reason"] == "conditions_differ_or_target_incomplete"
    page = await PersonalWikiService(sessions, settings).get(wiki_owner, page_id)
    assert page["conditions"] == [original] and page["version"] == 1


@pytest.mark.asyncio
async def test_initial_creation_undo_suppresses_the_origin(sessions, settings, wiki_owner):
    item = await answer(sessions, wiki_owner, with_source=False)
    page_id = await saved(sessions, settings, wiki_owner, item)
    service = PersonalWikiService(sessions, settings)
    assert (await service.get(wiki_owner, page_id))["evidenceStatus"] == "conversation_only"
    undone = await service.undo(wiki_owner, page_id, WikiUndo(expectedVersion=1))
    assert undone["deleted"] and (await service.list(wiki_owner))["items"] == []
    assert (await queued(sessions, wiki_owner, item))["reason"] == "message_excluded"


@pytest.mark.asyncio
async def test_service_account_cannot_read_organize_or_use_owner_settings(sessions, settings, seed_user):
    actor = await seed_user("scoped-service", kind="service", permissions=["personal_wiki:write"], auto_wiki=True)
    service = PersonalWikiService(sessions, settings)
    for operation in (service.list, service.settings):
        with pytest.raises(AppError) as error:
            await operation(actor)
        assert error.value.status_code == 403
    with pytest.raises(AppError) as error:
        await service.organize(actor, OrganizeRequest(messageId="not-a-personal-message", explicit=True))
    assert error.value.status_code == 403
    assert (await enqueue_for_message(sessions, actor, "api-answer"))["reason"] == "service_account"


@pytest.mark.asyncio
async def test_http_settings_are_explicit_and_validation_does_not_write(client, auth_headers):
    initial = await client.get("/api/v1/personal-wiki/settings", headers=auth_headers)
    assert initial.status_code == 200 and initial.json()["defaultIsAssumption"] is True
    updated = await client.patch("/api/v1/personal-wiki/settings", headers=auth_headers, json={"autoOrganize": True})
    assert updated.status_code == 200 and updated.json()["autoOrganize"] is True
    malformed = await client.patch("/api/v1/personal-wiki/missing", headers=auth_headers, json={"content": "x"})
    assert malformed.status_code == 422
    unauthenticated = await client.get("/api/v1/personal-wiki")
    assert unauthenticated.status_code == 401
