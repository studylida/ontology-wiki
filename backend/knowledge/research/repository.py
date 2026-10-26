from sqlalchemy import select

from knowledge.core.errors import AppError
from knowledge.research.entities import ResearchItem


class ResearchRepository:
    def __init__(self, session):
        self.session = session

    async def owned_items(self, principal, item_ids, *, lock=False):
        ids = set(item_ids)
        statement = select(ResearchItem).where(ResearchItem.id.in_(ids), ResearchItem.owner_id == principal.id).order_by(ResearchItem.id)
        if lock:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        rows = list((await self.session.scalars(statement)).all())
        if len(rows) != len(ids):
            raise AppError(404, "research_item_not_found", "조사 문헌을 찾을 수 없거나 현재 소유 자료가 아닙니다.")
        return {row.id: row for row in rows}
