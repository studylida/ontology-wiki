"""Single persistent embedding cache keyed by exact input and provider profile."""
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from ..core.ids import new_id
from ..documents.entities import EmbeddingRecord


class EmbeddingCache:
    def __init__(self, session):
        self.session = session

    async def lookup(self, profile, hashes):
        rows = await self.session.scalars(select(EmbeddingRecord).where(
            EmbeddingRecord.scope == 'shared', EmbeddingRecord.profile_id == profile,
            EmbeddingRecord.input_hash.in_(list(hashes))))
        return {row.input_hash: row.id for row in rows}

    async def store(self, profile, vectors):
        # Sorted keys make concurrent inserts use the same lock order.
        for hashed in sorted(vectors):
            await self.session.execute(insert(EmbeddingRecord).values(id=new_id('vec'), scope='shared',
                profile_id=profile, input_hash=hashed, vector=vectors[hashed])
                .on_conflict_do_nothing(index_elements=['scope','profile_id','input_hash']))
        return await self.lookup(profile, vectors)
