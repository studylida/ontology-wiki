"""Review draft persistence; callers own the approval transaction."""
from copy import deepcopy
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.attributes import set_committed_value
from fastapi import HTTPException
from backend.app.models.entities import ReviewTicketModel, EvidenceSourceModel
from backend.app.repositories.concept_repo import concept_repo
from backend.app.repositories.source_repo import source_repo

class ReviewRepository:

    async def get(self, db, ticket_id):
        return await db.get(ReviewTicketModel, ticket_id)

    async def update_pending(self, db, ticket, expected, values):
        values = {**values, 'ticket_version': expected + 1, 'updated_at': datetime.utcnow()}
        try:
            with db.no_autoflush:
                result = await db.execute(update(ReviewTicketModel).where(ReviewTicketModel.id == ticket.id,
                    ReviewTicketModel.ticket_version == expected, ReviewTicketModel.status == 'pending').values(**values).execution_options(synchronize_session=False))
        except OperationalError as error:
            await db.rollback()
            if 'locked' in str(error).lower():raise HTTPException(409, '다른 저장이 진행 중입니다. 작업본을 보존하고 다시 시도해 주세요.') from error
            raise
        if result.rowcount != 1:
            await db.rollback()
            raise HTTPException(409, '다른 편집 내용이 저장되었습니다. 입력을 보존하고 최신 판본을 확인해 주세요.')
        for key,value in values.items():set_committed_value(ticket,key,deepcopy(value))

    @staticmethod
    def evidence_value(row, concept_id=None):
        fields=('id','source_name','source_type','publisher','published_date','quote','section_context','external_url','url_label','credibility_tier')
        value={f:getattr(row,f) for f in fields}
        value['referenced_concepts']=[deepcopy(r) for r in row.referenced_concepts or [] if concept_id is None or r.get('conceptId')==concept_id]
        return value

    async def evidence(self, db, evidence_id):
        row=await db.get(EvidenceSourceModel,evidence_id)
        return self.evidence_value(row) if row else None

    async def linked_evidences(self, db, concept_id):
        rows=(await db.execute(select(EvidenceSourceModel).order_by(EvidenceSourceModel.id))).scalars().all()
        return [self.evidence_value(r,concept_id) for r in rows if any(v.get('conceptId')==concept_id for v in r.referenced_concepts or [])]

    async def latest_audit(self, db):
        from backend.app.models.entities import AuditLogModel
        return (await db.execute(select(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(1))).scalars().first()

    @staticmethod
    def add(db, row):db.add(row)

    async def content(self, db, concept_id):
        concept = await concept_repo.get_by_id(db, concept_id)
        cases = await source_repo.get_perspective_cases(db, concept_id)
        relations = concept.relations or {} if concept else {}
        state = {'summary': concept.summary or '' if concept else '', 'purpose': concept.purpose or '' if concept else '', 'principles': deepcopy(concept.principles or []) if concept else [], 'limitations': deepcopy(concept.limitations or []) if concept else [], 'perspectiveCases': [dict(id=c.id, isPublic=getattr(c,'review_is_public',False), perspectiveTitle=c.perspective_title, perspectiveBadge=c.perspective_badge, narrative=c.context_narrative, specifications=deepcopy(c.specifications or []), caution=c.caution, evidenceId=c.evidence_id) for c in cases], **{field: deepcopy(concept_repo.relation_items(relations.get(key))) for key, field in [('previous_step', 'previousSteps'), ('next_step', 'nextSteps'), ('alternative_to', 'alternatives'), ('part_of', 'partOf'), ('is_a', 'isA')]}}
        state['principles'] = [dict(step=index + 1, title='', content=value, formula=None) if isinstance(value, str) else value for index, value in enumerate(state['principles'])]
        state['limitations'] = [dict(title=value[:40], description=value) if isinstance(value, str) else value for value in state['limitations']]
        return (concept, state)

    async def save_content(self, db, concept, state, evidences, cases, replace_draft=False):
        _, previous = await self.content(db, concept.id)
        if replace_draft:await concept_repo.update_review_relations(db, concept.id, previous, state)
        concept.summary, concept.purpose = (state['summary'], state['purpose'])
        concept.principles, concept.limitations = ([{k:v for k,v in r.items() if k!='editorId'} for r in state['principles']], [{k:v for k,v in r.items() if k!='editorId'} for r in state['limitations']])
        relations = deepcopy(concept.relations or {})
        for key, field in [('previous_step', 'previousSteps'), ('next_step', 'nextSteps'), ('alternative_to', 'alternatives'), ('part_of', 'partOf'), ('is_a', 'isA')]:
            relations[key] = [{k:v for k,v in r.items() if k!='editorId'} for r in state[field]]
        concept.relations = relations
        for value in evidences:
            evidence = await db.get(EvidenceSourceModel, value['id'])
            if evidence is None:
                db.add(EvidenceSourceModel(**{k:v for k,v in value.items() if k != 'editorId'}))
            else:
                if evidence.quote != value['quote'] or evidence.external_url != value['external_url']:
                    raise ValueError('이미 등록된 출처의 인용문 또는 URL이 다릅니다. 변경안을 다시 생성해 주세요.')
                refs = deepcopy(evidence.referenced_concepts or [])
                incoming = next(ref for ref in value['referenced_concepts'] if ref['conceptId'] == concept.id)
                ref = next((ref for ref in refs if ref.get('conceptId') == concept.id), None)
                if ref is None:
                    refs.append(deepcopy(incoming))
                else:
                    ref['bodyFields'] = deepcopy(incoming.get('bodyFields', {})) if replace_draft else {**ref.get('bodyFields', {}), **incoming.get('bodyFields', {})}
                    if incoming.get('citationTag'):
                        ref['citationTag'] = incoming['citationTag']
                evidence.referenced_concepts = refs
        await db.flush()
        if replace_draft:
            existing = await source_repo.get_perspective_cases(db, concept.id)
            final_ids = {c['id'] for c in state['perspectiveCases']}
            for case in existing:
                if case.id not in final_ids:await db.delete(case)
            kept = {e['id'] for e in evidences}
            for value in await self.linked_evidences(db, concept.id):
                if value['id'] not in kept:
                    row = await db.get(EvidenceSourceModel, value['id'])
                    row.referenced_concepts = [r for r in row.referenced_concepts or [] if r.get('conceptId') != concept.id]
            cases = state['perspectiveCases']
        await source_repo.save_perspective_cases(db, concept.id, [{**c, 'specifications':[{k:v for k,v in s.items() if k!='editorId'} for s in c['specifications']]} for c in cases])
        removed = [dict(sourceId=concept.id,field=field,link=link) for field in ('previousSteps','nextSteps','alternatives','partOf','isA') for link in previous[field] if not any((link.get('id') or link.get('targetId'))==(r.get('id') or r.get('targetId')) for r in state[field])]
        await concept_repo.reconcile_relation_edges(db, removed_relations=removed)
        await db.flush()
review_repo = ReviewRepository()
