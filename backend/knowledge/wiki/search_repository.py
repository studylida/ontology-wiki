"""Wiki search SQL. Only current revisions are candidates; never synthesize source documents."""
from sqlalchemy import Text, and_, case, cast, func, or_, select
from sqlalchemy.dialects.postgresql import array
from ..documents.entities import EmbeddingRecord
from ..rag.ranking import query_terms, rank_score
from .entities import WikiPage, WikiRevision
from .index_entities import WikiIndexJob, WikiPassage, WikiPassageEmbedding
from .names import name_key
from .repository import WikiRepository


class WikiSearchRepository:
    def __init__(self, session):
        self.session = session

    def _pages(self, exclude=None):
        stmt = select(WikiPage, WikiRevision).join(WikiRevision, and_(
            WikiRevision.page_id == WikiPage.id, WikiRevision.id == WikiPage.current_revision_id)).where(WikiPage.withdrawn.is_(False))
        return stmt.where(WikiPage.id != exclude) if exclude else stmt

    def _passages(self, exclude=None):
        stmt = select(WikiPassage, WikiRevision, WikiPage).join(WikiRevision,
            WikiPassage.revision_id == WikiRevision.id).join(WikiPage, and_(
                WikiRevision.page_id == WikiPage.id, WikiRevision.id == WikiPage.current_revision_id,
                WikiRevision.id == WikiPage.indexed_revision_id)).join(WikiIndexJob,
                WikiIndexJob.revision_id == WikiRevision.id).where(
                WikiPassage.excluded.is_(False), WikiIndexJob.status == 'succeeded', WikiPage.withdrawn.is_(False))
        return stmt.where(WikiPage.id != exclude) if exclude else stmt

    async def alternatives(self, page_id, limit=12):
        row = await WikiRepository(self.session).detail(page_id)
        keys = row[1].name_keys
        if not keys:
            return []
        stmt = self._pages(page_id).where(WikiRevision.name_keys.has_any(array(keys)))
        rows = (await self.session.execute(stmt.order_by(WikiRevision.title, WikiPage.id).limit(limit))).all()
        return [(p.id, sorted(set(keys) & set(r.name_keys))) for p, r in rows]

    async def has_vectors(self, profile, exclude=None):
        stmt = self._passages(exclude).join(WikiPassageEmbedding, WikiPassageEmbedding.passage_id == WikiPassage.id)
        stmt = stmt.where(WikiPassageEmbedding.profile_id == profile, WikiIndexJob.profile_id == profile).limit(1)
        return (await self.session.execute(stmt)).first() is not None

    async def candidates(self, query, vector, profile, *, name_query=None, exclude=None, limit=60, passages_only=False):
        terms, key = query_terms(query), name_key(name_query or query)
        # Names remain discoverable immediately, even before the index worker runs.
        names_text = func.lower(cast(WikiRevision.aliases, Text))
        tests = [or_(func.lower(WikiRevision.title).contains(t, autoescape=True),
                     names_text.contains(t, autoescape=True), func.lower(WikiRevision.meaning).contains(t, autoescape=True))
                 for t in terms]
        exact = WikiRevision.name_keys.contains([key])
        score = sum((case((condition, 1), else_=0) for condition in tests), case((exact, 5), else_=0))
        names = [] if passages_only else (await self.session.execute(self._pages(exclude).add_columns(score)
            .where(or_(exact, *tests)).order_by(score.desc(), WikiPage.id).limit(limit))).all()
        lexical, vectors = [], []
        if terms:
            conditions = [func.lower(WikiPassage.text).contains(t, autoescape=True) for t in terms]
            weight = sum(case((condition, 1), else_=0) for condition in conditions)
            lexical = (await self.session.execute(self._passages(exclude).add_columns(weight)
                .where(or_(*conditions)).order_by(weight.desc(), WikiPassage.id).limit(limit))).all()
        if vector is not None:
            distance = EmbeddingRecord.vector.cosine_distance(vector)
            stmt = self._passages(exclude).join(WikiPassageEmbedding,
                WikiPassageEmbedding.passage_id == WikiPassage.id).join(EmbeddingRecord,
                EmbeddingRecord.id == WikiPassageEmbedding.embedding_id).where(
                    WikiPassageEmbedding.profile_id == profile, EmbeddingRecord.profile_id == profile,
                    WikiIndexJob.profile_id == profile)
            vectors = (await self.session.execute(stmt.add_columns(distance).order_by(distance, WikiPassage.id).limit(limit))).all()
        hits = {}
        for rank, (page, revision, _) in enumerate(names, 1):
            identity = 'name-' + revision.id
            hits[identity] = {'pageId': page.id, 'sourceRevisionId': revision.id, 'passageId': identity,
                'hasPassage': False, 'text': f'{revision.title}\n{revision.meaning}\n별칭: {", ".join(revision.aliases)}',
                'locator': '제목·별칭·뜻', 'score': rank_score(rank), 'methods': ['name'],
                'nameMatch': key in revision.name_keys}
        for method, rows in [('lexical', lexical), ('vector', vectors)]:
            for rank, (passage, revision, page, value) in enumerate(rows, 1):
                hit = hits.setdefault(passage.id, {'pageId': page.id, 'sourceRevisionId': revision.id,
                    'passageId': passage.id, 'hasPassage': True, 'text': passage.embedding_text,
                    'excerpt': passage.text, 'locator': passage.locator, 'score': 0., 'methods': [],
                    'nameMatch': key in revision.name_keys})
                hit['score'] += rank_score(rank)
                hit['methods'].append(method)
                if method == 'vector':
                    hit['cosineDistance'] = float(value)
        # An exact name is useful navigation but never a duplicate verdict.
        return sorted(hits.values(), key=lambda h: (-int(h['nameMatch']), -h['score'], h['passageId']))[:limit]
