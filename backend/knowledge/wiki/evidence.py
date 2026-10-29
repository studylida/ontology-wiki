"""Wiki evidence persistence. Identity stays wiki/page/revision, never a fake document."""
from sqlalchemy import select
from ..identity.authorization import is_employee
from .entities import WikiPage, WikiRevision
from .index_entities import WikiPassage
from .search_repository import WikiSearchRepository


def wiki_hit(passage, revision, page):
    return {'sourceKind': 'wiki', 'pageId': page.id, 'sourceRevisionId': revision.id,
            'revisionNumber': revision.number, 'passageId': passage.id,
            'title': revision.title, 'locator': passage.locator, 'text': passage.text,
            'excerpt': passage.text, 'lineageKey': 'wiki:' + page.id,
            'sourceType': 'internal', 'documentForm': 'staff_wiki', 'readScope': 'full',
            'sourceNote': revision.source_note, 'editorId': revision.editor_id,
            'publishedAt': revision.created_at.isoformat()}


class WikiEvidenceRepository:
    def __init__(self, session):
        self.session = session

    async def readable_ids(self, principal, ids, *, lock=False, current=False):
        if not ids or (principal is not None and not is_employee(principal)):
            return []
        stmt = select(WikiRevision.id).join(WikiPage, WikiPage.id == WikiRevision.page_id).where(
            WikiRevision.id.in_(ids), WikiPage.withdrawn.is_(False))
        if current:
            stmt = stmt.where(WikiPage.current_revision_id == WikiRevision.id)
        if lock:
            stmt = stmt.order_by(WikiPage.id, WikiRevision.id).with_for_update(of=WikiPage)
        return list(await self.session.scalars(stmt))

    async def indexed_ids(self, principal):
        if not is_employee(principal):
            return []
        stmt = WikiSearchRepository(self.session)._passages().with_only_columns(WikiRevision.id).distinct()
        return list(await self.session.scalars(stmt.order_by(WikiRevision.id)))

    async def candidates(self, principal, query, vector, profile, revision_ids, limit):
        if not revision_ids or not is_employee(principal):
            return []
        found = await WikiSearchRepository(self.session).candidates(
            query, vector, profile, limit=limit, passages_only=True)
        ids = [h['passageId'] for h in found if h['sourceRevisionId'] in revision_ids]
        stmt = WikiSearchRepository(self.session)._passages().where(WikiPassage.id.in_(ids))
        rows = {p.id: wiki_hit(p, r, w) for p, r, w in (await self.session.execute(stmt)).all()}
        return [{**h, **rows[h['passageId']]} for h in found if h['passageId'] in rows]

    async def neighbors(self, principal, passage_ids, revision_ids):
        if not passage_ids or not is_employee(principal):
            return []
        anchors = list(await self.session.scalars(select(WikiPassage).where(
            WikiPassage.id.in_(passage_ids), WikiPassage.revision_id.in_(revision_ids))))
        result = []
        # Small bounded anchor set, same original-revision and hold filters as candidates.
        for anchor in anchors:
            stmt = WikiSearchRepository(self.session)._passages().where(
                WikiPassage.revision_id == anchor.revision_id,
                WikiPassage.ordinal.between(anchor.ordinal - 1, anchor.ordinal + 1)).order_by(WikiPassage.ordinal)
            for p, r, w in (await self.session.execute(stmt)).all():
                result.append({**wiki_hit(p, r, w), 'methods': ['neighbor'], 'score': 0.})
        return result
