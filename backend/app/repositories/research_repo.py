"""Stored literature and public Crossref metadata I/O. Never manufacture results."""
from pathlib import Path
import httpx
from sqlalchemy import select
from backend.app.models.entities import ResearchSessionModel, EvidenceSourceModel


class ResearchRepository:
    async def get(self, db, session_id):
        return await db.get(ResearchSessionModel, session_id)

    async def list(self, db, limit):
        result = await db.execute(select(ResearchSessionModel).order_by(
            ResearchSessionModel.created_at.desc()).limit(limit))
        return list(result.scalars())

    async def evidences(self, db):
        result = await db.execute(select(EvidenceSourceModel))
        return list(result.scalars())

    def source_documents(self):
        root = Path(__file__).resolve().parents[3] / "sources"
        for path in sorted(root.rglob("*.md")):
            # Only the configured source tree is readable, including through symlinks.
            if path.resolve().is_relative_to(root.resolve()):
                yield path.relative_to(root).as_posix(), path.read_text(encoding="utf-8-sig")

    async def crossref(self, query):
        async with httpx.AsyncClient(timeout=12, headers={"User-Agent": "OntologyWiki/1.0"}) as client:
            response = await client.get("https://api.crossref.org/works", params={
                "query.bibliographic": query, "rows": 8, "sort": "score"})
            response.raise_for_status()
            return response.json()["message"]["items"]

    def add(self, db, session):
        db.add(session)


research_repo = ResearchRepository()
