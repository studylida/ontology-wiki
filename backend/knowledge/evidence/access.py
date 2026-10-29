"""Shared access policy for retrieval, generation, history and replay.

The existing server-generated revision namespaces are rev_ and wrv_.
Unknown IDs are checked against storage and fail closed, never treated as public.
Source repositories own their own availability rules.
"""
from ..documents.repository import DocumentRepository
from ..wiki.evidence import WikiEvidenceRepository


def partition(ids):
    ids = set(ids or [])
    wiki = {key for key in ids if key.startswith('wrv_')}
    return ids - wiki, wiki


class EvidenceAccess:
    def __init__(self, session):
        self.documents = DocumentRepository(session)
        self.wiki = WikiEvidenceRepository(session)

    async def ensure_readable(self, principal, ids, *, lock=False):
        documents, wiki = partition(ids)
        # Fixed lock order for mixed completion checks; no provider I/O while held.
        if documents and not await self.documents.ensure_readable(principal, documents, lock=lock):
            return False
        return not wiki or set(await self.wiki.readable_ids(principal, wiki, lock=lock)) == wiki

    async def current_ids(self, principal, ids):
        documents, wiki = partition(ids)
        current = set(await self.documents.resolve_snapshot(principal, list(documents))) if documents else set()
        if wiki:
            current.update(await self.wiki.readable_ids(principal, wiki, current=True))
        return current

    async def state(self, principal, ids):
        ids = set(ids or [])
        if not await self.ensure_readable(principal, ids):
            return 'unavailable'
        return 'current' if await self.current_ids(principal, ids) == ids else 'historical'
