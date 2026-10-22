"""Comparison persistence; services own interpretation and transaction boundaries."""
from sqlalchemy import select
from backend.app.models.entities import ComparisonSessionModel, EvidenceSourceModel, ReviewTicketModel


class ComparisonRepository:
    async def get(self, db, session_id):
        return await db.get(ComparisonSessionModel, session_id)

    async def list(self, db, limit):
        result = await db.execute(select(ComparisonSessionModel).order_by(
            ComparisonSessionModel.is_pinned.desc(), ComparisonSessionModel.created_at.desc()).limit(limit))
        return list(result.scalars())

    async def evidences(self, db, ids):
        if not ids:
            return {}
        result = await db.execute(select(EvidenceSourceModel).where(EvidenceSourceModel.id.in_(ids)))
        return {item.id: item for item in result.scalars()}

    def add(self, db, session):
        db.add(session)

    def add_ticket(self, db, values):
        ticket = ReviewTicketModel(**values)
        db.add(ticket)
        return ticket


comparison_repo = ComparisonRepository()
