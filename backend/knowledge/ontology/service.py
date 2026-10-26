from datetime import date

from knowledge.core.errors import AppError
from knowledge.ontology.repository import OntologyRepository


class OntologyService:
    """Read policy shared by HTTP clients. Reading never invokes an LLM."""
    def __init__(self, sessions):
        self.sessions = sessions

    @staticmethod
    def validate_filters(limit, date_from=None, date_to=None):
        if not 1 <= limit <= 100:
            raise AppError(422, "invalid_page_size", "조회 개수는 1~100개여야 합니다.")
        try:
            start = date.fromisoformat(date_from) if date_from else None
            end = date.fromisoformat(date_to) if date_to else None
        except ValueError:
            raise AppError(422, "invalid_date_filter", "발행일 조건은 YYYY-MM-DD 형식이어야 합니다.") from None
        if start and end and start > end:
            raise AppError(422, "invalid_date_range", "시작 발행일은 끝 발행일보다 늦을 수 없습니다.")

    async def concepts(self, principal, query="", cursor=None, limit=40):
        principal.require("ontology:read")
        self.validate_filters(limit)
        async with self.sessions() as session:
            return await OntologyRepository(session).concepts(principal, query, cursor, limit)

    async def concept(self, principal, concept_id):
        principal.require("ontology:read")
        async with self.sessions() as session:
            return await OntologyRepository(session).concept(principal, concept_id)

    async def relations(self, principal, concept_id):
        principal.require("ontology:read")
        async with self.sessions() as session:
            repo = OntologyRepository(session)
            await repo.concept(principal, concept_id)
            allowed = await repo.visible_public_revisions(principal)
            return {"items": (await repo.context(principal, [concept_id], allowed))["relations"]}

    async def source_views(self, principal, concept_id, **filters):
        principal.require("ontology:read")
        self.validate_filters(filters.get("limit", 40), filters.get("date_from"), filters.get("date_to"))
        async with self.sessions() as session:
            repo = OntologyRepository(session)
            await repo.concept(principal, concept_id)
            return await repo.source_views(principal, [concept_id], **filters)
