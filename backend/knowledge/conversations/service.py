from .dto import conversation_dto, message_dto
from .entities import Conversation
from .repository import ConversationRepository
from ..core.ids import utcnow
from sqlalchemy import select


async def protect_message(session, principal, data):
    """A hidden citation cannot make its derived answer safe to disclose."""
    from ..documents.repository import DocumentRepository
    references = list(data.get("citations", []))
    for card in data.get("relations", []) + data.get("sourceViews", []):
        references.extend(card.get("evidence", []))
    revision_ids = {c["sourceRevisionId"] for c in references if c.get("sourceRevisionId")}
    if revision_ids and not await DocumentRepository(session).ensure_readable(principal, list(revision_ids)):
        return {**data, "content": "", "citations": [], "relations": [], "sourceViews": [],
                "status": "restricted", "warnings": ["현재 접근 권한이 없는 자료에 근거한 내용입니다."]}
    if revision_ids:
        from ..documents.entities import DocumentRevision
        versions = dict((await session.execute(select(DocumentRevision.id, DocumentRevision.metadata_version).where(
            DocumentRevision.id.in_(revision_ids)))).all())
        stale = {c["sourceRevisionId"] for c in references if c.get("metadataVersion") is not None
                 and c["metadataVersion"] != versions.get(c.get("sourceRevisionId"))}
        stale.update(v["sourceRevisionId"] for v in data.get("sourceViews", []) if v.get("metadataVersion") is not None
                     and v["metadataVersion"] != versions.get(v.get("sourceRevisionId")))
        if stale:
            warning = "출처 메타데이터가 정정된 과거 답변입니다. 기존 본문은 당시 기록이며 출처별 해석은 최신 조회에서 확인하세요."
            return {**data, "sourceViews": [v for v in data.get("sourceViews", []) if v.get("sourceRevisionId") not in stale],
                "citations": [{**c, "historicalMetadata": True, "currentMetadataVersion": versions.get(c.get("sourceRevisionId"))}
                              if c.get("sourceRevisionId") in stale else c for c in data.get("citations", [])],
                "staleSourceRevisionIds": sorted(stale),
                "warnings": list(dict.fromkeys(data.get("warnings", []) + [warning]))}
    return data


class ConversationService:
    def __init__(self, session_factory, settings):
        self.session_factory, self.settings = session_factory, settings

    async def list(self, principal):
        async with self.session_factory() as session:
            return {"items": [conversation_dto(c) for c in await ConversationRepository(session).list(principal.id)]}

    async def create(self, principal, title=None):
        principal.require("rag:answer")
        async with self.session_factory() as session, session.begin():
            row = Conversation(owner_id=principal.id, title=(title or "새 대화").strip(),
                               auto_wiki=self.settings.auto_wiki_default and principal.kind == "user")
            session.add(row)
            await session.flush()
            return conversation_dto(row)

    async def get(self, principal, conversation_id):
        async with self.session_factory() as session:
            repo = ConversationRepository(session)
            row = await repo.owned(conversation_id, principal.id)
            messages = [await protect_message(session, principal, message_dto(m))
                        for m in await repo.messages(conversation_id)]
            return {**conversation_dto(row), "messages": messages}

    async def patch(self, principal, conversation_id, body):
        async with self.session_factory() as session, session.begin():
            row = await ConversationRepository(session).owned(conversation_id, principal.id, lock=True)
            if body.title is not None:
                row.title = body.title.strip()
            if body.auto_wiki is not None:
                auto_wiki = body.auto_wiki and principal.kind == "user"
                if row.auto_wiki and not auto_wiki:
                    from ..personal_wiki.service import exclude_conversation
                    await exclude_conversation(session, principal, conversation_id)
                row.auto_wiki = auto_wiki
            row.updated_at = utcnow()
            await session.flush()
            return conversation_dto(row)

    async def history(self, principal, conversation_id, before_message_id=None):
        if not conversation_id:
            return []
        result = await self.get(principal, conversation_id)
        messages = result["messages"]
        if before_message_id:
            messages = messages[:next((i for i, m in enumerate(messages) if m["id"] == before_message_id), len(messages))]
        return [{"role": m["role"], "content": m["content"], "citations": m.get("citations", []) +
                 [e for card in m.get("relations", []) + m.get("sourceViews", []) for e in card.get("evidence", [])]}
                for m in messages
                if m["status"] == "completed" and m["content"]][-8:]
