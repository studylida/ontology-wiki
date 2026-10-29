"""One owner for shared source visibility and retrieval SQL; no approval gate."""
from __future__ import annotations
import hashlib
import re
from collections import defaultdict
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import aliased
from ..core.errors import AppError
from ..rag.ranking import query_terms, rank_score
from .entities import Document, DocumentRevision, EmbeddingRecord, Passage, PassageEmbedding


def public_scope():
    return and_(Document.withdrawn.is_(False), Document.active_revision_id == DocumentRevision.id,
                DocumentRevision.index_status == 'ready')


def group_predicate(group):
    parts = [DocumentRevision.metadata_json[key].astext == group[key]
             for key in ('publisherId','sourceType') if group.get(key)]
    return and_(*parts) if parts else True


def group_match(metadata, group):
    return all(metadata.get(k) == group[k] for k in ('publisherId','sourceType') if group.get(k))


def author_ranking(hits, terms):
    terms = [t for t in terms if len(t) >= 3 and t.isalpha()]
    matches = {}
    for hit in hits:
        author = str(hit.get('author') or '').casefold()
        count = sum(bool(re.search(rf'(?<!\w){re.escape(t)}(?!\w)', author)) for t in terms)
        if count:
            matches[hit['sourceRevisionId']] = count
    return {revision: 1 / (61 + sum(other > count for other in matches.values())) for revision, count in matches.items()}


def select_ranked_hits(hits, source_groups=None, limit=12, *, per_document_limit=3):
    groups = source_groups or []
    chosen, seen, per_doc = [], set(), defaultdict(int)
    def add(hit):
        chosen.append(hit)
        seen.add(hit['passageId'])
        per_doc[hit.get('lineageKey') or hit.get('documentId',hit['sourceRevisionId'])] += 1
    for group in groups:
        for hit in hits:
            if len(chosen) < limit and group_match(hit,group) and hit['passageId'] not in seen:
                add(hit)
                break
    for hit in hits:
        if len(chosen) >= limit:
            break
        key = hit.get('lineageKey') or hit.get('documentId',hit['sourceRevisionId'])
        if hit['passageId'] not in seen and (per_document_limit is None or per_doc[key] < per_document_limit):
            add(hit)
    return {'hits': chosen, 'groupCoverage': [
        {'groupId': g['groupId'], 'hitCount': sum(group_match(h,g) for h in chosen),
         'status': 'available' if any(group_match(h,g) for h in chosen) else 'missing'} for g in groups]}


def citation_dict(passage, revision, document):
    meta = revision.metadata_json
    return {'id': passage.id, 'passageId': passage.id, 'sourceRevisionId': revision.id,
            'documentId': document.id, 'title': revision.title, 'locator': passage.locator,
            'excerpt': passage.text, 'readScope': revision.read_scope,
            **{k: meta.get(k) for k in ('publisher','publisherId','author','sourceType','documentForm','publishedAt','url','lineageKey')}}


class DocumentRepository:
    def __init__(self, session):
        self.session = session

    async def get(self, document_id, *, lock=False):
        stmt = select(Document).where(Document.id == document_id)
        if lock:
            stmt = stmt.with_for_update()
        row = await self.session.scalar(stmt)
        if row is None:
            raise AppError(404, 'document_not_found', '문헌을 찾을 수 없습니다.')
        return row

    @staticmethod
    def require_manage(document, principal):
        if document.owner_id != principal.id and principal.role != 'admin':
            raise AppError(403, 'document_manage_denied', '등록자 또는 운영자만 문헌을 변경할 수 있습니다.')

    @staticmethod
    def require_enabled(document):
        if document.withdrawn:
            raise AppError(409, 'document_inactive', '비활성화된 문헌은 처리하거나 활성화하지 않습니다.')

    async def list(self, limit=100):
        return list(await self.session.scalars(select(Document).order_by(Document.updated_at.desc(),Document.id).limit(limit)))

    async def revision(self, principal, revision_id, *, for_update=False):
        stmt = select(DocumentRevision,Document).join(Document,Document.id == DocumentRevision.document_id).where(
            DocumentRevision.id == revision_id, Document.withdrawn.is_(False))
        if for_update:
            stmt = stmt.with_for_update()
        row = (await self.session.execute(stmt)).first()
        if row is None:
            raise AppError(404,'source_not_found','문헌이 없거나 비활성화되었습니다.')
        return row

    async def ensure_readable(self, principal, revision_ids, *, lock=False):
        ids = set(revision_ids)
        stmt = select(DocumentRevision.id).join(Document,Document.id == DocumentRevision.document_id).where(
            DocumentRevision.id.in_(ids),Document.withdrawn.is_(False))
        if lock:
            stmt = stmt.with_for_update()
        return set(await self.session.scalars(stmt)) == ids

    async def passages(self, revision_id, *, include_excluded=False):
        stmt = select(Passage).where(Passage.source_revision_id == revision_id).order_by(Passage.ordinal)
        if not include_excluded:
            stmt = stmt.where(Passage.excluded.is_(False))
        return list(await self.session.scalars(stmt))

    async def resolve_snapshot(self, principal, source_revision_ids=None, source_groups=None):
        stmt = select(DocumentRevision.id).join(Document,Document.id == DocumentRevision.document_id).where(public_scope())
        if source_revision_ids is not None:
            stmt = stmt.where(DocumentRevision.id.in_(source_revision_ids))
        if source_groups:
            stmt = stmt.where(or_(*(group_predicate(g) for g in source_groups)))
        return list(await self.session.scalars(stmt.order_by(DocumentRevision.id)))

    def _base(self, principal, revision_ids, groups):
        stmt = select(Passage,DocumentRevision,Document).join(DocumentRevision,Passage.source_revision_id == DocumentRevision.id).join(Document,Document.id == DocumentRevision.document_id).where(
            Passage.excluded.is_(False),DocumentRevision.id.in_(revision_ids),public_scope())
        if groups:
            stmt = stmt.where(or_(*(group_predicate(g) for g in groups)))
        return stmt

    async def search_candidates(self, principal, query_vector, profile_id, query_text,
                                source_revision_ids=None, source_groups=None, candidate_limit=60):
        return await self.search(principal,query_vector,profile_id,query_text,source_revision_ids,
                                 source_groups,candidate_limit,candidates_only=True)

    async def search(self, principal, query_vector, profile_id, query_text, source_revision_ids=None,
                     source_groups=None, limit=12, *, candidates_only=False):
        # Reuse hybrid ranking and per-document diversity; every path uses active shared sources.
        ids = await self.resolve_snapshot(principal,source_revision_ids,source_groups)
        snapshot = 'idx-' + hashlib.sha256('|'.join(sorted(ids)).encode()).hexdigest()[:24]
        groups, warnings = source_groups or [], []
        if not ids:
            return {**select_ranked_hits([],groups,limit), 'indexSnapshotId': snapshot,
                    'warnings': ['검색 가능한 활성 문헌이 없습니다. 처리 상태를 확인하세요.']}
        base = self._base(principal,ids,groups)
        vectors = base.join(PassageEmbedding,PassageEmbedding.passage_id == Passage.id).join(
            EmbeddingRecord,EmbeddingRecord.id == PassageEmbedding.embedding_id).where(
            PassageEmbedding.profile_id == profile_id, EmbeddingRecord.profile_id == profile_id)
        distance = EmbeddingRecord.vector.cosine_distance(query_vector)
        vector_rows, lexical_rows = [], []
        method_limit = max(60,limit if candidates_only else limit * 4)
        terms = query_terms(query_text)
        anchor = aliased(Passage)
        first_visible = select(func.min(anchor.ordinal)).where(anchor.source_revision_id == DocumentRevision.id,
            anchor.excluded.is_(False)).correlate(DocumentRevision).scalar_subquery()
        for group in groups or [{}]:
            vector_rows.extend((await self.session.execute(vectors.where(group_predicate(group)).add_columns(distance).order_by(distance,Passage.id).limit(method_limit))).all())
            if terms:
                author = func.lower(func.coalesce(DocumentRevision.metadata_json['author'].astext,''))
                matches = [or_(func.lower(Passage.text).contains(t,autoescape=True),
                    and_(Passage.ordinal == first_visible,or_(func.lower(DocumentRevision.title).contains(t,autoescape=True),
                        author.op('~')(rf'(^|[^[:alnum:]]){re.escape(t)}([^[:alnum:]]|$)') if t.isalpha() else False))) for t in terms]
                score = sum(case((condition,1),else_=0) for condition in matches)
                lexical_rows.extend((await self.session.execute(base.where(group_predicate(group)).add_columns(score).where(or_(*matches)).order_by(score.desc(),Passage.id).limit(method_limit))).all())
        vector_rows = sorted({row[0].id: row for row in vector_rows}.values(),key=lambda row:(float(row[3]),row[0].id))
        lexical_rows = sorted({row[0].id: row for row in lexical_rows}.values(),key=lambda row:(-int(row[3]),row[0].id))
        if not vector_rows:
            warnings.append('선택 프로필의 벡터가 없습니다. 현재 결과는 명시적 문자열 검색입니다.')
        candidates = {}
        for method,rows in (('vector',vector_rows),('lexical',lexical_rows)):
            for rank,row in enumerate(rows,1):
                p,r,d = row[:3]
                hit = candidates.setdefault(p.id,{**citation_dict(p,r,d),'text':p.text,'score':0.0,'methods':[]})
                hit['score'] += rank_score(rank)
                hit['methods'].append(method)
                if method == 'vector':
                    hit['cosineDistance'] = float(row[3])
        scores = author_ranking(list(candidates.values()),terms)
        for hit in candidates.values():
            if hit['sourceRevisionId'] in scores:
                hit['score'] += scores[hit['sourceRevisionId']]
                hit['methods'].append('author')
        ordered = sorted(candidates.values(),key=lambda h:(-h['score'],h['passageId']))
        return {**select_ranked_hits(ordered,groups,limit,per_document_limit=None if candidates_only else 3),
                'indexSnapshotId':snapshot,'warnings':warnings,'candidateCount':len(ordered)}

    async def get_neighbors(self, principal, passage_ids, source_revision_ids=None, source_groups=None):
        origins = list(await self.session.scalars(select(Passage).where(Passage.id.in_(passage_ids))))
        if not origins:
            return []
        ids = await self.resolve_snapshot(principal,source_revision_ids,source_groups)
        conditions = [and_(Passage.source_revision_id == p.source_revision_id,Passage.ordinal.in_([p.ordinal-1,p.ordinal+1])) for p in origins]
        rows = (await self.session.execute(self._base(principal,ids,source_groups).where(or_(*conditions))
                .order_by(Passage.source_revision_id,Passage.ordinal).limit(24))).all()
        return [{**citation_dict(p,r,d),'text':p.text,'score':None,'methods':['neighbor'],
                 'neighborOf':[o.id for o in origins if o.source_revision_id == p.source_revision_id and abs(o.ordinal-p.ordinal) == 1]}
                for p,r,d in rows]
