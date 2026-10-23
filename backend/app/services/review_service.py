"""Grounded review drafts. Preview and approval materialize the same pending contributions."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from types import SimpleNamespace
from fastapi import HTTPException
from backend.app.core.security import mask_tier3_perspective
from backend.app.repositories.review_repo import review_repo
from backend.app.repositories.research_repo import research_repo
from backend.app.repositories.source_repo import source_repo
from backend.app.repositories.concept_repo import concept_repo
from backend.app.schemas.review import DirectiveKnowledgePatch
from backend.app.services.source_service import source_service
from backend.app.services.comparison_service import public_evidence
from backend.app.services.auth_service import AccessControlService
FIELDS = [('summary', '개요 및 기술 정의'), ('principles', '작동 및 물리 원리'), ('limitations', '물리적 한계 및 트레이드오프'), ('perspectiveCases', '적응형 실무 사례 및 파라미터'), ('relations', '관계망 및 규모 계층'), ('evidences', '출처 원문')]
LINKS = [('previousSteps', 'previous_step'), ('nextSteps', 'next_step'), ('alternatives', 'alternative_to'), ('partOf', 'part_of'), ('isA', 'is_a')]

import uuid
from backend.app.agents.directive_agent import directive_agent, DirectiveAgent
from backend.app.schemas.review import ReviewPreviewRequest

import hmac, hashlib, logging
from fastapi import status
from backend.app.core.config import settings
from backend.app.core.cache import cache_manager
from backend.app.models.entities import ReviewTicketModel, AuditLogModel, ConceptModel, CausalEdgeModel
from backend.app.schemas.review import ReviewTicketDTO, AuditLogDTO, ReviewTicketApproveRequest, ReviewTicketActionResponse
logger = logging.getLogger(__name__)

def _convert_ticket_to_dto(ticket: ReviewTicketModel) -> ReviewTicketDTO:
    """Helper to convert ReviewTicketModel to ReviewTicketDTO with proper ISO dates."""
    return ReviewTicketDTO(
        id=ticket.id,
        concept_id=ticket.concept_id,
        concept_title=ticket.concept_title,
        title=ticket.title,
        review_type=ticket.review_type,
        author=ticket.author,
        department=ticket.department,
        submitted_at=ticket.submitted_at.isoformat() if ticket.submitted_at else None,
        status=ticket.status,
        source_session_id=ticket.source_session_id,
        origin_type=ticket.origin_type,
        current_version=ticket.current_version,
        target_version=ticket.target_version,
        current_content=ticket.current_content,
        ai_merged_draft=ticket.ai_merged_draft,
        human_edits=ticket.human_edits,
        structured_patches=[p for p in ticket.structured_patches or [] if isinstance(p,dict) and p.get('path') not in ('/workingDraft','/wikiDraft')],
        editingMode='structured' if review_service.working(ticket) else 'legacy',
        canUndo=bool(ticket.directive_history and ('previousPatches' in ticket.directive_history[-1])),
        integrity_report=ticket.integrity_report or {},
        directive_history=[{k:v for k,v in item.items() if k in ('directiveText','timestamp','targetLayer','overrideReason')} for item in ticket.directive_history or []],
        override_reason=ticket.override_reason,
        approved_at=ticket.approved_at.isoformat() if ticket.approved_at else None,
        approved_by=ticket.approved_by,
        applied_concept_version=ticket.applied_concept_version,
        ticket_version=ticket.ticket_version
    )


def _convert_audit_to_dto(audit: AuditLogModel) -> AuditLogDTO:
    """Helper to convert AuditLogModel to AuditLogDTO."""
    return AuditLogDTO(
        audit_id=audit.audit_id,
        ticket_id=audit.ticket_id,
        concept_id=audit.concept_id,
        action_type=audit.action_type,
        actor=audit.actor or {},
        governance_snapshot=audit.governance_snapshot or {},
        previous_log_hash=audit.previous_log_hash,
        entry_hash=audit.entry_hash,
        digital_signature=audit.digital_signature,
        timestamp=audit.timestamp.isoformat() if audit.timestamp else None
    )



class ReviewService:
    signature = staticmethod(DirectiveAgent.signature)
    patch = staticmethod(DirectiveAgent.patch)
    retained_evidences = staticmethod(DirectiveAgent.retained_evidences)

    @staticmethod
    def working(ticket):
        return next((p.get('value') for p in ticket.structured_patches or [] if isinstance(p, dict) and p.get('path') == '/workingDraft'), None)

    @staticmethod
    def identify(state, evidences):
        for field in ('principles', 'limitations', 'perspectiveCases', *[key for key, _ in LINKS]):
            for index, row in enumerate(state[field]):
                row.setdefault('editorId', field + ':' + sha256(json.dumps([index, row], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24])
                for i, spec in enumerate(row.get('specifications') or []):
                    spec.setdefault('editorId', row['editorId'] + ':' + str(i))
        for row in evidences:
            row.setdefault('editorId', row['id'])

    async def full_draft(self, ticket, db):
        state, evidences, _ = await self.materialize(ticket, db)
        _, original = await review_repo.content(db, ticket.concept_id)
        linked = await review_repo.linked_evidences(db, ticket.concept_id)
        snapshot = self.working(ticket)
        linked_signature = self.signature(linked)
        values = {e['id']: e for e in linked}
        values.update({e['id']: e for e in evidences})
        if snapshot:
            values = {e['id']: e for e in snapshot['evidences']}
        evidences = list(values.values())
        self.identify(state, evidences)
        return dict(schemaVersion=1, baseSignature=snapshot['baseSignature'] if snapshot else self.signature(original),
                    baseEvidenceSignature=snapshot['baseEvidenceSignature'] if snapshot else linked_signature,
                    state=state, evidences=evidences, deprecatedCitations=(snapshot or {}).get('deprecatedCitations',[]))

    async def editable(self, ticket, db, user):
        draft = await self.full_draft(ticket, db)
        allowed = await AccessControlService.can_view_confidential_l3(user, ticket.concept_id, db)
        result = deepcopy(draft['state'])
        result['conceptOptions'] = [dict(id=c.id,title=c.title) for c in await concept_repo.get_all_concepts(db)]
        result['availableEvidences'] = [dict(id=e.id,sourceName=e.source_name) for e in await research_repo.evidences(db) if public_evidence(e)]
        result['evidences'] = []
        for value in draft['evidences']:
            if public_evidence(SimpleNamespace(**value)):
                result['evidences'].append(dict(editorId=value['editorId'], id=value['id'], sourceName=value['source_name'],
                    publisher=value.get('publisher') or '', quote=value['quote'], externalUrl=value.get('external_url') or '',
                    isNew=value['id'].startswith('review:' + ticket.id + ':')))
        for case in result['perspectiveCases']:
            raw = dict(context_narrative=case['narrative'], caution=case['caution'], specifications=case['specifications'], evidence_id=case.get('evidenceId'), is_public_case=case.get('isPublic',False))
            masked = mask_tier3_perspective(raw, allowed)
            case['narrative'], case['caution'] = masked['context_narrative'], masked['caution']
            case['isMasked'] = masked['isMasked']
            case['evidenceId'] = masked.get('evidence_id')
            specs = []
            for original, visible in zip(raw['specifications'], masked['specifications']):
                restricted = original.get('isConfidential', original.get('is_confidential', True)) is not False
                # Hidden values are not valid form values and never round-trip as ***.
                specs.append(dict(editorId=original['editorId'], parameter=visible.get('parameter') or '',
                    **({k:v for k,v in visible.items() if k in {'value','unit','safetyMargin','role','tradeoff','rationale','evidenceIds'}} if allowed or not restricted else {}),
                    isConfidential=restricted, readOnly=restricted and not allowed))
            case['specifications'] = specs
        return dict(schemaVersion=1, content=result, permissions=dict(canEdit=bool(user and user.is_active and user.level >= 2 and ticket.status == 'pending'),
                    canEditConfidential=allowed, canChangeConfidentiality=bool(user and user.level >= 3)))

    @staticmethod
    def require_editor(user):
        if not user:
            raise HTTPException(401, '로그인이 필요합니다.')
        if not user.is_active or user.level < 2:
            raise HTTPException(403, '현장 엔지니어 이상만 초안을 편집할 수 있습니다.')

    @staticmethod
    def invalidate(row):
        row['evidenceVerified'] = False
        for key in ('fieldEvidenceQuotes',):
            row.pop(key, None)

    def apply_rows(self, rows, change, field, allowed, level, ticket_id):
        if change is None:
            raise HTTPException(422, '목록 변경은 null일 수 없습니다.')
        indexed = {r['editorId']: r for r in rows}
        upserts, removed = change.get('upsert', []), change.get('remove', [])
        keys = [r['editorId'] for r in upserts]
        if len(set(keys)) != len(keys) or len(set(removed)) != len(removed) or set(keys) & set(removed):
            raise HTTPException(422, '항목 변경 키가 중복됐습니다.')
        if not set(removed) <= indexed.keys():
            raise HTTPException(422, '삭제할 항목을 현재 작업본에서 찾지 못했습니다.')
        def restricted(row):
            return field == 'evidences' and not public_evidence(SimpleNamespace(**row)) or field == 'specifications' and row.get('isConfidential', row.get('is_confidential', True)) is not False or field == 'perspectiveCases' and (not row['specifications'] and not row.get('isPublic') or any(s.get('isConfidential', s.get('is_confidential', True)) is not False for s in row['specifications']))
        if not allowed and any(restricted(indexed[k]) for k in removed):
            raise HTTPException(403, '보호된 항목은 삭제할 수 없습니다.')
        for key in removed:
            indexed.pop(key)
        order = [r['editorId'] for r in rows if r['editorId'] not in removed]
        for patch in upserts:
            patch = deepcopy(patch)
            key = patch.pop('editorId')
            new = key not in indexed
            row = indexed.get(key)
            if new:
                if key in {r['editorId'] for r in rows}:
                    raise HTTPException(422, '삭제 항목을 동시에 변경할 수 없습니다.')
                defaults = {'principles':dict(title='',content='',formula=None), 'limitations':dict(title='',description=''),
                    'perspectiveCases':dict(id='case-'+uuid.uuid4().hex,isPublic=True,perspectiveTitle='',perspectiveBadge='',narrative='',caution='',specifications=[],evidenceId=None),
                    'specifications':dict(parameter='',value=None,unit=None,safetyMargin=None,role=None,tradeoff=None,rationale=None),
                    'evidences':dict(id='review:'+ticket_id+':'+sha256(key.encode()).hexdigest()[:12],source_name='',source_type='source_document',publisher='',quote='',external_url='',url_label='원문 출처',credibility_tier='사용자 입력·미검증',referenced_concepts=[])}
                row = dict(editorId=key, **defaults.get(field, {})); indexed[key]=row; order.append(key)
            if not allowed and not new and restricted(row) and patch:
                if field != 'perspectiveCases' or any(k in patch for k in ('narrative','caution','evidenceId')) or not row['specifications'] and not row.get('isPublic') and 'specifications' in patch:
                    raise HTTPException(403, '보호된 항목은 수정할 수 없습니다.')
            if field == 'specifications':
                if new and ('isConfidential' not in patch or patch['isConfidential'] is None):
                    raise HTTPException(422, '새 파라미터의 공개/기밀을 선택해 주세요.')
                if not new and 'isConfidential' in patch and patch['isConfidential'] != row.get('isConfidential',row.get('is_confidential',True)) and level < 3:
                    raise HTTPException(403, '기밀 지정·해제는 수석 검토관 이상만 가능합니다.')
                if new and patch.get('isConfidential') and not allowed:
                    raise HTTPException(403, '기밀 파라미터 작성 권한이 없습니다.')
            if 'specifications' in patch and patch['specifications'] is None:raise HTTPException(422,'파라미터 변경은 null일 수 없습니다.')
            specs = patch.pop('specifications', None)
            for k, value in patch.items():
                if value is None and k in {'title','content','description','perspectiveTitle','perspectiveBadge','narrative','caution','parameter','isConfidential','evidenceIds','sourceName','publisher','quote','externalUrl'}:
                    raise HTTPException(422, k + ' 값은 null일 수 없습니다.')
            if field == 'evidences':
                if not new and not row['id'].startswith('review:'+ticket_id+':'):
                    raise HTTPException(422, '등록 공용 출처는 연결 해제 후 새 발췌로 추가해 주세요.')
                for k,v in patch.items():
                    row[{'sourceName':'source_name','externalUrl':'external_url'}.get(k,k)] = v
                if row.get('external_url') and not re.match(r'^https?://', row['external_url']):
                    raise HTTPException(422, '출처 URL은 http 또는 https여야 합니다.')
            else:
                if any(row.get(k) != v for k,v in patch.items()):self.invalidate(row)
                row.update(patch)
            if specs is not None:
                row['specifications'] = self.apply_rows(row['specifications'], specs, 'specifications', allowed, level, ticket_id)
            if field == 'evidences' and (not row['source_name'].strip() or not row['quote'].strip()):
                raise HTTPException(422, '출처 이름과 발췌가 필요합니다.')
        if change.get('order') is not None:
            requested=change['order']
            if len(requested)!=len(indexed) or set(requested)!=indexed.keys():raise HTTPException(422, '항목 순서가 현재 목록과 다릅니다.')
            if not allowed and any(restricted(indexed[k]) and requested.index(k)!=order.index(k) for k in order):raise HTTPException(403, '보호된 항목은 재정렬할 수 없습니다.')
            order=requested
        return [indexed[k] for k in order]

    async def save(self, ticket, body, db, user):
        self.require_editor(user)
        if ticket.status != 'pending':raise HTTPException(409, '이미 처리된 티켓입니다.')
        if body.ticketVersion is not None and body.ticketVersion != ticket.ticket_version:raise HTTPException(409, '다른 편집 내용이 저장되었습니다. 입력을 보존하고 최신 판본을 확인해 주세요.')
        expected=ticket.ticket_version
        if body.changes is None:
            if self.working(ticket):raise HTTPException(409, 'REVIEW_CLIENT_UPGRADE_REQUIRED')
            from backend.app.core.citation_manager import EvidenceCitationManager
            content,_,_=await EvidenceCitationManager.validate_and_restore(original_text=f'{ticket.current_content or ""}\n{ticket.ai_merged_draft or ""}',edited_text=body.editedContent,allow_citation_deletion=body.allowCitationDeletion,deprecated_citations=body.deprecatedCitations,override_reason=body.overrideReason)
            values=dict(human_edits=content)
        else:
            draft=await self.full_draft(ticket,db)
            allowed=await AccessControlService.can_view_confidential_l3(user,ticket.concept_id,db)
            original_state=deepcopy(draft['state'])
            original_evidences=deepcopy(draft['evidences'])
            changes=body.changes.model_dump(exclude_unset=True)
            if not changes and self.working(ticket):
                return dict(ticketId=ticket.id,ticketVersion=ticket.ticket_version,humanEdits=ticket.human_edits or '',workingDraft=await self.editable(ticket,db,user),integrityReport=ticket.integrity_report or {},updatedAt=ticket.updated_at.isoformat())
            for field, change in changes.items():
                if change is None:raise HTTPException(422, field+'는 null일 수 없습니다.')
                if field in ('summary','purpose'):
                    if change is None:raise HTTPException(422, field+'는 null일 수 없습니다.')
                    draft['state'][field]=change
                elif field=='evidences':
                    for item in (change or {}).get('upsert',[]):
                        if item.get('existingId'):
                            if set(item)-{'editorId','existingId'}:raise HTTPException(422,'등록 출처 연결과 내용 수정을 함께 요청할 수 없습니다.')
                            evidence=await review_repo.evidence(db,item['existingId'])
                            if not evidence or not public_evidence(SimpleNamespace(**evidence)):raise HTTPException(422,'공개 등록 출처를 찾지 못했습니다.')
                            if any(e['editorId']==item['editorId'] or e['id']==item['existingId'] for e in draft['evidences']):raise HTTPException(422,'이미 연결된 출처입니다.')
                            evidence['editorId']=item['editorId'];draft['evidences'].append(evidence)
                    change=deepcopy(change)
                    change['upsert']=[v for v in change.get('upsert',[]) if not v.get('existingId')]
                    draft['evidences']=self.apply_rows(draft['evidences'],change,field,allowed,user.level,ticket.id)
                else:
                    draft['state'][field]=self.apply_rows(draft['state'][field],change,field,allowed,user.level,ticket.id)
            for i,row in enumerate(draft['state']['principles']):row['step']=i+1
            for field in [key for key,_ in LINKS]:
                for row in draft['state'][field]:
                    target=row.get('id') or row.get('targetId')
                    if not target or target==ticket.concept_id:raise HTTPException(422,'관계 대상이 없거나 자기 자신입니다.')
                    # Existing unresolved references survive; new targets must be registered.
                    existing=original_state.get(field,[])
                    registered = await concept_repo.get_by_id(db,target)
                    if not registered and not any((r.get('id') or r.get('targetId'))==target for r in existing):raise HTTPException(422,'등록된 관계 대상을 선택해 주세요.')
                    if registered:
                        row['targetId' if field=='alternatives' else 'id']=registered.id
                        row['targetName' if field=='alternatives' else 'name']=registered.title
            aliases={'draft:'+e['editorId']:e['id'] for e in draft['evidences']}
            entries=[r for f in ('principles','limitations','perspectiveCases',*[k for k,_ in LINKS]) for r in draft['state'][f]]
            entries += [v for c in draft['state']['perspectiveCases'] for v in c['specifications']]
            for row in entries:
                if row.get('evidenceId'):row['evidenceId']=aliases.get(row['evidenceId'],row['evidenceId'])
                if 'evidenceIds' in row:row['evidenceIds']=[aliases.get(e,e) for e in row['evidenceIds']]
            for field in ('summary','purpose'):
                for old,new in aliases.items():draft['state'][field]=draft['state'][field].replace('['+old+']','['+new+']')
            self.validate_references(draft)
            original_ids={e['id'] for e in original_evidences}
            from backend.app.core.citation_manager import EvidenceCitationManager
            parse=EvidenceCitationManager.parse_citations
            removed_citations=set(parse(original_state['summary']+'\n'+original_state['purpose']))-set(parse(draft['state']['summary']+'\n'+draft['state']['purpose']))
            removed_citations |= {tag for e in original_ids-{e['id'] for e in draft['evidences']} for tag in parse('['+e+']')}
            permitted={tag for value in body.deprecatedCitations or [] for tag in parse('['+str(value).strip('[]')+']')}
            if removed_citations and (not body.allowCitationDeletion or not (body.overrideReason or '').strip() or not removed_citations<=permitted):
                raise HTTPException(422,'공인 출처 폐기는 대상 출처와 사유를 명시해 인가해야 합니다.')
            draft['deprecatedCitations']=sorted(set(draft.get('deprecatedCitations',[]))|removed_citations)
            for evidence in draft['evidences']:
                evidence['referenced_concepts']=[dict(conceptId=ticket.concept_id,name=ticket.concept_title,
                    bodyFields={f:draft['state'][f] for f in ('summary','purpose') if f'[{evidence["id"]}]' in draft['state'][f] or any(r.get('conceptId')==ticket.concept_id and r.get('bodyFields',{}).get(f)==draft['state'][f] for r in evidence.get('referenced_concepts',[]))},
                    citationTag=f'[{evidence["id"]}]')]
            patches=[p for p in ticket.structured_patches or [] if p.get('path')!='/workingDraft']
            values=dict(structured_patches=patches+[dict(op='replace',path='/workingDraft',value=draft)],human_edits=draft['state']['summary'])
        if body.overrideReason:values['override_reason']=body.overrideReason
        await review_repo.update_pending(db,ticket,expected,values)
        editable=await self.editable(ticket,db,user) if body.changes is not None else None
        await db.commit()
        return dict(ticketId=ticket.id,ticketVersion=ticket.ticket_version,humanEdits=ticket.human_edits or '',
            workingDraft=editable,
            integrityReport=ticket.integrity_report or {},updatedAt=ticket.updated_at.isoformat())

    @staticmethod
    def validate_references(draft):
        ids={e['id'] for e in draft['evidences']}
        rows=[row for field in ('principles','limitations','perspectiveCases',*[k for k,_ in LINKS]) for row in draft['state'][field]]
        rows += [s for c in draft['state']['perspectiveCases'] for s in c['specifications']]
        for row in rows:
            if not set(row.get('evidenceIds') or [])<=ids or row.get('evidenceId') and row['evidenceId'] not in ids:raise HTTPException(422,'사용 중인 출처 연결을 먼저 수정해 주세요.')
        for field in ('summary','purpose'):
            if any(token not in ids for token in re.findall(r'\[([^\[\]\s]+)\]',draft['state'][field]) if token.startswith(('E-','EV-','review:'))):raise HTTPException(422,'본문에 연결되지 않은 출처가 있습니다.')

    async def preview_response(self, ticket, db, user, request):
        self.require_editor(user)
        if request.ticketVersion is not None and request.ticketVersion!=ticket.ticket_version:raise HTTPException(409,'미리보기 판본이 변경되었습니다.')
        if self.working(ticket) and request.editedContent is not None:raise HTTPException(409,'REVIEW_CLIENT_UPGRADE_REQUIRED')
        candidate=deepcopy(ticket)
        if request.conceptPlacement:
            placement=request.conceptPlacement.model_dump()
            candidate.structured_patches=[{**p,'value':{**p['value'],'domain_facet':placement['domainFacet'],'scale_level':placement['scaleLevel'],'process_category':placement['processCategory']}} if p.get('path')=='/concept' else p for p in candidate.structured_patches or []]
        state,evidences,_=await self.materialize(candidate,db,request.editedContent)
        signature=self.signature(dict(state=state,evidences=evidences,ticketVersion=ticket.ticket_version,targetVersion=request.targetVersion or ticket.target_version,placement=request.conceptPlacement.model_dump() if request.conceptPlacement else None))
        return dict(ticketId=ticket.id,conceptId=ticket.concept_id,targetVersion=request.targetVersion or ticket.target_version or ticket.current_version,
            ticketVersion=ticket.ticket_version,previewSignature=signature,workingDraft=await self.editable(ticket,db,user),
            previewConcept=await self.preview(candidate,db,user,request.editedContent),baselineConcept=await self.preview(ticket,db,user,current_wiki=True),
            diffSummary=dict(sections=(ticket.integrity_report or {}).get('sections',[]),status='preview'))


    async def materialize(self, ticket, db, editor_draft=None, seed_state=None):
        concept, state = await review_repo.content(db, ticket.concept_id)
        base_signature = self.signature(state)
        snapshot = self.working(ticket)
        if snapshot and ticket.status != 'approved':
            if snapshot.get('schemaVersion') != 1:
                raise HTTPException(409, '지원하지 않는 작업본 버전입니다.')
            if snapshot['baseSignature'] != base_signature or snapshot['baseEvidenceSignature'] != self.signature(await review_repo.linked_evidences(db, ticket.concept_id)):
                raise HTTPException(409, '위키 기준 내용이나 출처가 변경되었습니다. 작업본을 보존하고 재검토해 주세요.')
            for source in (self.patch(ticket) or {}).get('sources', []):
                if source.get('kind') == 'local':
                    file = source_repo.resolve_safe_file_path(SimpleNamespace(file_path=source['localPath']))
                    if source_repo.compute_file_hash(file) != source['sourceHash']:
                        raise HTTPException(409, '사용한 원문이 변경되었습니다.')
            state = deepcopy(snapshot['state'])
            return state, deepcopy(snapshot['evidences']), deepcopy(state['perspectiveCases'])
        if seed_state is not None:
            state = deepcopy(seed_state)
        if seed_state is None and concept is None and isinstance(ticket.structured_patches, list):
            placement = next((p.get('value', {}) for p in ticket.structured_patches if isinstance(p, dict) and p.get('path') == '/concept'), {})
            state['purpose'] = placement.get('purpose') or ''
        patch = self.patch(ticket)
        if not patch or ticket.status == 'approved':
            state['summary'] = editor_draft if editor_draft is not None else ticket.human_edits or ticket.ai_merged_draft or state['summary']
            return (state, self.retained_evidences(ticket, state), [])
        patch = DirectiveKnowledgePatch(**patch).model_dump(by_alias=True)
        if base_signature != patch['baseSignature']:
            raise HTTPException(409, '위키 원본이 변경되었습니다. 현재 원본으로 지시문을 다시 실행해주세요.')
        sources = {s['id']: s for s in patch['sources']}
        for source in sources.values():
            if source.get('kind') == 'local':
                file = source_repo.resolve_safe_file_path(SimpleNamespace(file_path=source['localPath']))
                if source_repo.compute_file_hash(file) != source['sourceHash']:
                    raise HTTPException(409, '사용한 원문이 변경되었습니다. 지시문을 다시 실행해주세요.')
        cases = []
        evidences = {}
        for contribution in patch['contributions']:
            source = sources.get(contribution['sourceId'])
            if not source:
                raise HTTPException(409, '변경안의 근거 자료를 확인할 수 없습니다.')
            raw = contribution['content']
            item = source_service.normalize_concept(source_service.validate_quotes(raw, source['quote']), source.get('originKey',source['id']))
            item['perspectiveCases']=[case for case in item['perspectiveCases'] if not any(source_service.case_content(case)==source_service.case_content(existing) for existing in state['perspectiveCases'])]
            source_service.merge_content(item, state, source.get('originKey',source['id']))
            cases.extend(item.get('_caseUpdates') or [])
            quotes = set()
            for field in ('summary', 'purpose'):
                if item.get(field + 'EvidenceVerified'):
                    quotes.add(item[field + 'EvidenceQuote'])
            for field in ('principles', 'limitations', 'perspectiveCases', *[key for key, _ in LINKS]):
                for value in item[field]:
                    if value.get('evidenceVerified'):
                        quotes.add(value['evidenceQuote'])
                        for spec in value.get('specifications') or []:
                            quotes.add(spec['evidenceQuote'])
                            quotes.update((q for q in (spec.get('fieldEvidenceQuotes') or {}).values() if q))
            for quote in filter(None, quotes):
                eid = source_service.evidence_id(source.get('originKey',source['id']), ticket.concept_id, quote)
                body_fields = {field: item[field] for field in ('summary', 'purpose')
                    if item.get(field + 'EvidenceVerified') and item.get(field) and quote == item.get(field + 'EvidenceQuote')}
                if eid in evidences:
                    body_fields = {**evidences[eid]['referenced_concepts'][0].get('bodyFields', {}), **body_fields}
                evidences[eid] = dict(id=eid, source_name=source['sourceName'], source_type='source_document', publisher=source.get('publisher') or '', quote=quote, section_context=source.get('localPath') or 'review-source:'+source.get('originKey',source['id']), external_url=source.get('externalUrl') or '', url_label='원문 출처', credibility_tier='초록 (전문 미확보)' if source.get('retrievalStatus') == 'abstract' else '등록 원문·발췌', referenced_concepts=[{'conceptId': ticket.concept_id, 'name': ticket.concept_title, 'bodyFields': body_fields}])
        if concept is None and isinstance(ticket.structured_patches, list):
            placement = next((p.get('value', {}) for p in ticket.structured_patches if p.get('path') == '/concept'), {})
            parent_id = placement.get('parent_concept_id')
            if parent_id and (not any((link.get('id') == parent_id for link in state['isA']))):
                parent = await concept_repo.get_by_id(db, parent_id)
                state['isA'].append(dict(id=parent_id, name=parent.title if parent else parent_id))
        if editor_draft is not None:
            state['summary'] = editor_draft
        else:
            state['summary'] = ticket.human_edits or ticket.ai_merged_draft or state['summary']
        for evidence in evidences.values():
            ref = evidence['referenced_concepts'][0]
            ref['bodyFields'] = {field: value for field, value in ref['bodyFields'].items() if value == state[field]}
        aliases = {}
        for pending in self.retained_evidences(ticket, state):
            for eid, generated in list(evidences.items()):
                if all(generated[key] == pending[key] for key in ('source_name', 'external_url', 'quote')):
                    ref = pending['referenced_concepts'][0]
                    ref['bodyFields'] = {**generated['referenced_concepts'][0].get('bodyFields', {}), **ref.get('bodyFields', {})}
                    aliases[eid] = pending['id']
                    del evidences[eid]
            evidences[pending['id']] = pending
        # The directive may reuse an entire acquired excerpt; keep its citation ID.
        entries = [value for field in ('principles', 'limitations', 'perspectiveCases', *[key for key, _ in LINKS]) for value in state[field]] + cases
        entries += [spec for value in entries for spec in value.get('specifications') or []]
        for value in entries:
            if 'evidenceIds' in value:
                value['evidenceIds'] = list(dict.fromkeys(aliases.get(eid, eid) for eid in value['evidenceIds']))
            if value.get('evidenceId') in aliases:
                value['evidenceId'] = aliases[value['evidenceId']]
        return (state, list(evidences.values()), cases)

    async def process_directive(self, ticket, directive_text, override_reason, db, target_layer='hybrid', allow_citation_deletion=False, deprecated_citations=None, gemini_key=None, openai_key=None, edited_content=None, ticket_version=None, undo_last=False, structured_draft=False, target_sections=None, current_user=None):
        if ticket.status != 'pending':
            raise HTTPException(409, '검토 대기 중인 티켓만 수정할 수 있습니다.')
        if ticket_version is not None and ticket.ticket_version != ticket_version:
            raise HTTPException(409, '다른 편집 내용이 저장되었습니다. 티켓을 다시 열어주세요.')
        expected = ticket.ticket_version
        snapshot = self.working(ticket)
        if snapshot and not structured_draft:
            raise HTTPException(409, 'REVIEW_CLIENT_UPGRADE_REQUIRED')
        if structured_draft and ticket_version is None:
            raise HTTPException(422, '티켓 판본이 필요합니다.')
        if target_sections is not None and not target_sections:
            raise HTTPException(422, '보강할 목차가 비어 있습니다.')
        current = await self.full_draft(ticket, db) if structured_draft else None
        base = current['state']['summary'] if current else edited_content if edited_content is not None else ticket.human_edits or ticket.ai_merged_draft or ticket.current_content or ''
        previous = dict(previousDraft=base, previousPatches=deepcopy(ticket.structured_patches), previousIntegrity=deepcopy(ticket.integrity_report), previousWorking=deepcopy(current), previousSignature=self.signature(current) if current else None)
        if undo_last:
            history = list(ticket.directive_history or [])
            last = history[-1] if history else {}
            if 'previousPatches' not in last:
                raise HTTPException(409, '되돌릴 수 있는 지시문 결과가 없습니다.')
            if edited_content is not None and base != last.get('revisedDraft'):
                raise HTTPException(409, '지시문 이후 직접 편집한 내용이 있습니다. 보존할 내용을 확인한 뒤 되돌려주세요.')
            if structured_draft and last.get('afterSignature') != self.signature(current):
                raise HTTPException(409, '지시문 이후 직접 편집한 내용이 있습니다. 작업본을 보존했습니다.')
            ticket.ai_merged_draft = ticket.human_edits = last['previousDraft']
            ticket.structured_patches = last['previousPatches']
            ticket.integrity_report = last['previousIntegrity']
            ticket.directive_history = history[:-1]
            values = {k: deepcopy(getattr(ticket,k)) for k in ('ai_merged_draft','human_edits','structured_patches','integrity_report','directive_history')}
            await review_repo.update_pending(db, ticket, expected, values)
            return
        if not directive_text.strip():
            raise HTTPException(400, '보완 지시문이 비어있습니다.')
        public_draft = None
        if current:
            public_draft = deepcopy(current['state'])
            public_ids = {e['id'] for e in current['evidences'] if public_evidence(SimpleNamespace(**e))}
            for case in public_draft['perspectiveCases']:
                if not case['specifications'] and not case.get('isPublic') or case.get('evidenceId') and case['evidenceId'] not in public_ids or any(s.get('isConfidential',s.get('is_confidential',True)) is not False for s in case['specifications']):
                    case['narrative'] = case['caution'] = ''
                case['specifications'] = [s for s in case['specifications'] if s.get('isConfidential',s.get('is_confidential',True)) is False and set(s.get('evidenceIds') or []) <= public_ids and (not case.get('evidenceId') or case['evidenceId'] in public_ids)]
        sources, contributions, summary_draft, warnings = await directive_agent.propose(ticket, db, base, directive_text, gemini_key, openai_key, public_draft)
        if target_sections is not None:
            selected = set(target_sections)
            for contribution in contributions:
                content = contribution['content']
                for field in ('summary','purpose','principles','limitations','perspectiveCases',*[k for k,_ in LINKS]):
                    section = 'relations' if field in dict(LINKS) else 'summary' if field == 'purpose' else field
                    if section not in selected:content[field] = '' if field in ('summary','purpose') else []
            if 'summary' not in selected:summary_draft = base
        replacements=[item for item in contributions if item.get('_replaceField')]
        contributions=[item for item in contributions if not item.get('_replaceField')]
        _, original = await review_repo.content(db, ticket.concept_id)
        old = self.patch(ticket)
        combined = list(old['contributions']) if not snapshot and old and old.get('baseSignature') == self.signature(original) else []
        for item in contributions:
            if item not in combined:
                combined.append(item)
        if old:
            sources = list({s['id']: s for s in [*old['sources'], *sources]}.values())
        knowledge = DirectiveKnowledgePatch(baseSignature=self.signature(original), sources=sources, contributions=combined).model_dump(by_alias=True)
        patches = [p for p in ticket.structured_patches or [] if isinstance(p, dict) and p.get('path') not in ('/wikiDraft','/workingDraft')] if isinstance(ticket.structured_patches, list) else []
        candidate = SimpleNamespace(**{key: getattr(ticket, key) for key in ('concept_id', 'concept_title', 'human_edits', 'ai_merged_draft', 'status')}, structured_patches=patches + [dict(op='replace', path='/wikiDraft', value=knowledge)])
        candidate.human_edits = summary_draft
        candidate.ai_merged_draft = summary_draft
        state, evidences, _ = await self.materialize(candidate, db, editor_draft=summary_draft, seed_state=current['state'] if current else None)
        for replacement in replacements:
            field= replacement['_replaceField']
            target=next((r for r in state[field] if r.get('editorId')==replacement['_replaceEditorId']),None)
            if not current or target is None:
                warnings.append('교체 대상 항목을 확인하지 못해 제안을 보류했습니다.');continue
            if not replacement['content'].get(field):continue
            if field=='perspectiveCases' and (not target['specifications'] and not target.get('isPublic') or any(v.get('isConfidential',v.get('is_confidential',True)) is not False for v in target['specifications'])):
                warnings.append('기밀 사례의 모델 교체를 적용하지 않았습니다.');continue
            single=deepcopy(candidate)
            single.structured_patches=[p for p in single.structured_patches if p.get('path')!='/wikiDraft']+[dict(op='replace',path='/wikiDraft',value={**knowledge,'contributions':[replacement]})]
            empty={'summary':'','purpose':'',**{f:[] for f in ('principles','limitations','perspectiveCases',*[k for k,_ in LINKS])}}
            generated,refs,_=await self.materialize(single,db,editor_draft=summary_draft,seed_state=empty)
            if len(generated[field])!=1:
                warnings.append('교체 제안의 의미 검토 결과를 확인하지 못했습니다.');continue
            updated=generated[field][0]
            if field=='perspectiveCases':updated.update(id=target['id'],isPublic=target.get('isPublic',False))
            updated['editorId']=target['editorId']
            state[field]=[updated if r is target else r for r in state[field]]
            evidences=list({e['id']:e for e in [*evidences,*refs]}.values())
            knowledge['contributions'].append({k:v for k,v in replacement.items() if not k.startswith('_')})
        if current:
            evidences = list({e['id']:e for e in [*current['evidences'],*evidences]}.values())
            self.identify(state,evidences)
            current['state'], current['evidences'] = state, evidences
            candidate.structured_patches=[{**p,'value':knowledge} if p.get('path')=='/wikiDraft' else p for p in candidate.structured_patches]
            candidate.structured_patches.append(dict(op='replace',path='/workingDraft',value=current))
        sections = []
        for field, label in FIELDS:
            before = original.get(field)
            after = state.get(field)
            if field == 'summary':
                before = [base,original['purpose']]
                after = [state['summary'],state['purpose']]
            if field == 'relations':
                before = [original[key] for key, _ in LINKS]
                after = [state[key] for key, _ in LINKS]
            if field == 'evidences':
                before = []
                after = evidences
            populated = any(after) if isinstance(after, list) else bool(after)
            sections.append(dict(field=field, label=label, status='보강됨' if before != after else '변경 없음' if populated else '근거 부족'))
        report = dict(verified=False, evidenceMatchRate=None, hasOntologyConflict=None, impactScopeCount=None, validationDetails='이번 제안의 본문·관계·사례를 제공 발췌와 의미 검토한 보강안입니다. 근거 부족은 이번 제안에서 확인하지 못했다는 뜻이며 전체 원문에 없다는 판정은 아닙니다. 물리 안전성은 별도 검토가 필요합니다.', sections=sections, warnings=list(dict.fromkeys(warnings)), sources=[dict(id=s['id'], sourceName=s['sourceName'], externalUrl=s.get('externalUrl') or '', retrievalStatus=s.get('retrievalStatus')) for s in sources])
        await db.refresh(ticket)
        if ticket.ticket_version != expected or ticket.status != 'pending':
            raise HTTPException(409, '생성 중 티켓이 변경되었습니다. 새 편집 내용을 확인해주세요.')
        ticket.ai_merged_draft = ticket.human_edits = state['summary']
        ticket.structured_patches = candidate.structured_patches
        ticket.integrity_report = report
        now = datetime.now(timezone.utc)
        ticket.directive_history = [*(ticket.directive_history or []), dict(directiveText=directive_text, targetLayer='hybrid', timestamp=now.isoformat(), revisedDraft=state['summary'], afterSignature=self.signature(current) if current else None, **previous)]
        ticket.updated_at = now
        if override_reason:
            ticket.override_reason = override_reason
        values = {k: deepcopy(getattr(ticket,k)) for k in ('ai_merged_draft','human_edits','structured_patches','integrity_report','directive_history','override_reason')}
        await review_repo.update_pending(db, ticket, expected, values)

    async def preview(self, ticket, db, current_user, editor_draft=None, current_wiki=False):
        if current_wiki:
            _, state = await review_repo.content(db, ticket.concept_id)
            evidences = []
        else:
            state, evidences, _ = await self.materialize(ticket, db, editor_draft)
        concept = await concept_repo.get_by_id(db, ticket.concept_id)
        placement = next((p['value'] for p in ticket.structured_patches or [] if isinstance(p, dict) and p.get('path') == '/concept'), {}) if isinstance(ticket.structured_patches, list) else {}
        allowed = await AccessControlService.can_view_confidential_l3(current_user, ticket.concept_id, db)
        perspectives = []
        for case in state['perspectiveCases']:
            masked = mask_tier3_perspective(dict(context_narrative=case['narrative'], caution=case['caution'], specifications=case['specifications'], evidence_id=case.get('evidenceId'), is_public_case=case.get('isPublic',False)), allowed)
            perspectives.append(dict(id=case['id'], perspectiveTitle=case['perspectiveTitle'], perspectiveBadge=case['perspectiveBadge'], contextNarrative=masked['context_narrative'], specifications=masked['specifications'], caution=masked['caution'], evidenceId=masked.get('evidence_id'), isMasked=masked['isMasked']))
        from backend.app.services.case_explanation_service import case_explanation_service
        fields = await case_explanation_service.preview_fields(db, ticket.concept_id, ticket.concept_title, state)
        for case in perspectives:
            case.update(fields[case['id']])
        registered = {c.id: c for c in await concept_repo.get_all_concepts(db)}
        relations = {key: [{**link, 'isRegistered': (link.get('id') or link.get('targetId')) in registered} for link in state[field]] for field, key in LINKS}
        connected = {ticket.concept_id} if concept else set()
        queue = [link.get('id') for link in state['partOf']]
        while queue:
            cid = queue.pop()
            if cid in registered and cid not in connected:
                connected.add(cid)
                queue.extend((link.get('id') for link in concept_repo.relation_items((registered[cid].relations or {}).get('part_of'))))
        ladder = [dict(scaleLevel=registered[cid].scale_level, scaleName=registered[cid].scale_name, title=registered[cid].title, description=registered[cid].summary or '', isCurrent=cid == ticket.concept_id, entityId=cid, entityName=registered[cid].title) for cid in sorted(connected, key=lambda cid: -(registered[cid].scale_level or 0))] if len(connected) > 1 else []
        existing_evidence = [dict(id=e.id, sourceName=e.source_name, quote=e.quote, externalUrl=e.external_url or '', scopeLabel=e.credibility_tier) for e in await research_repo.evidences(db) if public_evidence(e) and any((ref.get('conceptId') == ticket.concept_id for ref in e.referenced_concepts or []))]
        visible_evidence = {e['id']: e for e in [*([] if self.working(ticket) and not current_wiki else existing_evidence), *[dict(id=e['id'], sourceName=e['source_name'], quote=e['quote'], externalUrl=e['external_url'], scopeLabel=e['credibility_tier']) for e in evidences if public_evidence(SimpleNamespace(**e))]]}
        return dict(id=ticket.concept_id, title=ticket.concept_title, isRegistered=concept is not None, engName=concept.eng_name if concept else placement.get('eng_name', ''), domainFacet=concept.domain_facet if concept else placement.get('domain_facet'), scaleLevel=concept.scale_level if concept else placement.get('scale_level'), processCategory=concept.process_category if concept else placement.get('process_category'), scaleName=concept.scale_name if concept else placement.get('scale_name'), summary=state['summary'], purpose=state['purpose'], principles=state['principles'], limitations=state['limitations'], perspectives=perspectives, l3AccessStatus=dict(hasAccess=allowed, requestStatus='approved' if allowed else 'none'), relations=relations, scaleLadder=ladder, evidences=list(visible_evidence.values()), version=ticket.target_version or ticket.current_version, sectionResults=(ticket.integrity_report or {}).get('sections', []))

    async def approve(self, ticket_id, background_tasks, body, current_user, x_gemini_key, x_openai_key, db):
        if body is None:
            body = ReviewTicketApproveRequest()

        # 🌟 수석검토관(Level 3) 이상 거버넌스 승인 인가 가드레일 (오직 인증된 수석검토관 토큰 필수)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "MISSING_TOKEN", "message": "위키 버전 승인 및 거버넌스 집행을 위해 로그인이 필요합니다."}
            )
        if current_user.level < 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_LEVEL",
                    "message": "위키 버전 승인 및 거버넌스 집행 권한은 '수석검토관(Level 3)' 이상 전용입니다. 현장 엔지니어(Level 2)는 승인 권한이 없습니다."
                }
            )
        approver_id = current_user.id
        approver_name = current_user.name
        approver_role = current_user.role
        approver_dept = current_user.department

        ticket = await review_repo.get(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"거버넌스 검토 티켓 '{ticket_id}'을(를) 찾을 수 없습니다."
            )

        if ticket.status != 'pending':
            raise HTTPException(409, '이미 처리된 티켓입니다.')
        if body.ticketVersion is not None and body.ticketVersion != ticket.ticket_version:
            raise HTTPException(409, '티켓이 변경되었습니다. 현재 변경안을 다시 확인해주세요.')
        approval_patches = deepcopy(ticket.structured_patches)
        # Research proposals keep unknown classification until a reviewer confirms it.
        if ticket.origin_type == "문헌조사" and any(p.get("path") == "/concept" for p in ticket.structured_patches or []):
            if body.conceptPlacement is None:
                raise HTTPException(422, "신규 문헌 개념의 분야·규모·분류를 확인하고 확정해 주세요.")
            from backend.app.services.placement_service import SCALE_NAMES
            approval_patches = [{**p, "value": {**p["value"],
                "domain_facet": body.conceptPlacement.domainFacet,
                "scale_level": body.conceptPlacement.scaleLevel,
                "scale_name": SCALE_NAMES[body.conceptPlacement.scaleLevel],
                "process_category": body.conceptPlacement.processCategory.strip()}} if p.get("path") == "/concept" else p
                for p in ticket.structured_patches]
        structured = bool(self.working(ticket))
        if structured:
            if body.humanEdits is not None or not body.previewSignature or body.ticketVersion is None:
                raise HTTPException(409, 'REVIEW_CLIENT_UPGRADE_REQUIRED')
            confirmation = await self.preview_response(ticket, db, current_user, ReviewPreviewRequest(ticketVersion=body.ticketVersion,targetVersion=body.targetVersion,conceptPlacement=body.conceptPlacement))
            if confirmation['previewSignature'] != body.previewSignature:
                raise HTTPException(409, '미리보기 이후 내용이나 분류가 변경되었습니다. 다시 확인해 주세요.')
        prepared_knowledge = await self.materialize(ticket, db, body.humanEdits)
        if structured and not prepared_knowledge[0]['summary'].strip():
            raise HTTPException(422, '승인할 개요를 작성해 주세요.')
        if structured:
            state=prepared_knowledge[0]
            if any(not r['content'].strip() for r in state['principles']) or any(not r['description'].strip() for r in state['limitations']):
                raise HTTPException(422, '빈 원리·한계 항목을 작성하거나 삭제해 주세요.')
            if any(not c['perspectiveTitle'].strip() or not c['narrative'].strip() or any(not v['parameter'].strip() for v in c['specifications']) for c in state['perspectiveCases']):
                raise HTTPException(422, '사례 제목·설명과 파라미터 명칭을 확인해 주세요.')
        # Reserve this pending revision atomically before any approval writes.
        await review_repo.update_pending(db, ticket, ticket.ticket_version, {})
        # Re-read after acquiring the DB write reservation: another ticket may have approved this concept.
        await db.run_sync(lambda session: session.expire_all())
        await db.refresh(ticket)
        latest_knowledge = await self.materialize(ticket, db, body.humanEdits)
        if self.signature(latest_knowledge) != self.signature(prepared_knowledge):
            await db.rollback()
            raise HTTPException(409, '승인 준비 중 위키 기준이 변경되었습니다.')
        ticket.structured_patches = approval_patches

        now_utc = datetime.utcnow()
        final_reason = body.overrideReason or ticket.override_reason or ""
        guide_tip = None

        # 1. 이전 최신 감사 로그 조회 (머클 해시 체인 연결)
        latest_audit = await review_repo.latest_audit(db)
        previous_log_hash = latest_audit.entry_hash if latest_audit else "0" * 64

        # 2. WORM 감사 로그 데이터 조립
        audit_id = f"aud-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        actor_info = {
            "userId": approver_id,
            "name": approver_name,
            "role": approver_role,
            "department": approver_dept,
            "action": "approve"
        }
        # 1. 온톨로지 세맨틱 버전(vMAJOR.MINOR.PATCH) 자동 계산
        concept = await concept_repo.get_by_id(db, ticket.concept_id)
        cur_ver = (concept.version if concept else ticket.current_version) or "v1.2.0"

        # 버전 승계 규칙:
        # 1. 신규 개념 등록 (new_concept) 또는 공인 출처 공식 폐기(Breaking Change) -> minor (v1.2.x -> v1.3.0)
        #    (명시적 플래그/목록 또는 Tier 1 AI 사유 문맥 의도 판별을 통해 Human-in-the-Loop 인가)
        # 2. 일상적 파라미터/문맥 수정 -> patch (v1.2.0 -> v1.2.1)
        from backend.app.core.citation_manager import EvidenceCitationManager
        is_new = "신규" in (ticket.review_type or "") or ticket.review_type == "new_concept"
        has_deprecation_flag = body.allowCitationDeletion or bool(body.deprecatedCitations)
        has_deprecation_reason = bool(self.working(ticket).get('deprecatedCitations')) if structured else await EvidenceCitationManager.is_deprecation_intended(
            final_reason,
            gemini_key=x_gemini_key,
            openai_key=x_openai_key
        )
        has_deprecation = has_deprecation_flag or has_deprecation_reason
        auto_bump_type = "minor" if (is_new or has_deprecation) else "patch"

        def _bump_version(v_str: str, b_type: str) -> str:
            cleaned = (v_str or "").strip().lstrip("v")
            parts = cleaned.split(".")
            maj, min_v, pat = 1, 0, 0
            try:
                if len(parts) >= 1 and parts[0].isdigit(): maj = int(parts[0])
                if len(parts) >= 2 and parts[1].isdigit(): min_v = int(parts[1])
                if len(parts) >= 3 and parts[2].isdigit(): pat = int(parts[2])
            except Exception:
                pass
            if b_type == "major": return f"v{maj + 1}.0.0"
            elif b_type == "minor": return f"v{maj}.{min_v + 1}.0"
            return f"v{maj}.{min_v}.{pat + 1}"

        applied_ver = body.targetVersion or ticket.target_version or _bump_version(cur_ver, auto_bump_type)
        gov_snapshot = {
            "ticketId": ticket.id,
            "conceptId": ticket.concept_id,
            "conceptTitle": ticket.concept_title,
            "appliedVersion": applied_ver,
            "previousVersion": cur_ver,
            "overrideReason": final_reason,
            "integrityReport": ticket.integrity_report or {},
            "humanEditsSummary": (body.humanEdits or ticket.human_edits or "")[:200],
            "deprecatedCitations": (self.working(ticket) or {}).get("deprecatedCitations",[])
        }

        if body.conceptPlacement is not None:
            gov_snapshot["conceptPlacement"] = body.conceptPlacement.model_dump()

        # Merkle SHA-256 Entry Hash 계산
        raw_hash_source = f"{previous_log_hash}|{audit_id}|{ticket.id}|approve|{json.dumps(actor_info, sort_keys=True)}|{json.dumps(gov_snapshot, sort_keys=True)}|{now_utc.isoformat()}"
        entry_hash = hashlib.sha256(raw_hash_source.encode("utf-8")).hexdigest()

        # HMAC 디지털 서명
        digital_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            entry_hash.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # 감사 로그 저장
        audit_entry = AuditLogModel(
            audit_id=audit_id,
            ticket_id=ticket.id,
            concept_id=ticket.concept_id,
            action_type="approve",
            actor=actor_info,
            governance_snapshot=gov_snapshot,
            previous_log_hash=previous_log_hash,
            entry_hash=entry_hash,
            digital_signature=digital_sig,
            timestamp=now_utc
        )
        review_repo.add(db, audit_entry)

        # 3. 티켓 상태 갱신
        ticket.status = "approved"
        ticket.approved_at = now_utc
        ticket.approved_by = approver_name
        ticket.applied_concept_version = applied_ver
        if body.humanEdits:
            ticket.human_edits = body.humanEdits
        if body.overrideReason:
            ticket.override_reason = body.overrideReason
        ticket.updated_at = now_utc

        # 4. 온톨로지 개념(ConceptModel) 본문 및 버전 영구 승계
        concept = await concept_repo.get_by_id(db, ticket.concept_id)
        concept_updated = False
        if concept:
            concept.version = applied_ver
            if ticket.human_edits:
                concept.summary = ticket.human_edits
            elif ticket.ai_merged_draft:
                concept.summary = ticket.ai_merged_draft
            concept.updated_at = now_utc
            concept_updated = True
        else:
            # 🌟 완전 신규 개념 승인 분기: ConceptModel 신규 생성 및 온톨로지 트리 영구 편입
            placement = {}
            if ticket.structured_patches and isinstance(ticket.structured_patches, list):
                for patch in ticket.structured_patches:
                    if patch.get("path") == "/concept" and isinstance(patch.get("value"), dict):
                        placement = patch.get("value")
                        break

            new_concept = ConceptModel(
                id=ticket.concept_id,
                title=ticket.concept_title or ticket.title,
                eng_name=placement.get("eng_name", ticket.concept_title or ticket.title),
                aliases=[],
                domain_facet=placement.get("domain_facet", "unit_process"),
                process_category=placement.get("process_category", "첨단 패키징"),
                scale_level=placement.get("scale_level", 3),
                scale_name=placement.get("scale_name", "Scale 3: 단위 공정"),
                version=applied_ver or "v1.0.0",
                status="adopted",
                last_reviewed_at=now_utc,
                last_reviewed_by=body.approvedBy,
                summary=ticket.human_edits or ticket.ai_merged_draft or "### 1. 기술 정의\n(신규 온톨로지 개념)",
                purpose=(placement.get("purpose") or "") if ticket.origin_type == "문헌조사" else ticket.override_reason or "신규 공정 개념 편입",
                principles=[],
                limitations=[],
                relations={"is_a": placement.get("parent_concept_id")} if placement.get("parent_concept_id") else {},
                created_at=now_utc,
                updated_at=now_utc
            )
            review_repo.add(db, new_concept)
            concept_updated = True

            # 상위 개념과의 인과 에지(CausalEdgeModel) 자동 연결
            parent_id = placement.get("parent_concept_id")
            if parent_id:
                parent_concept = await concept_repo.get_by_id(db, parent_id)
                if parent_concept:
                    new_edge = CausalEdgeModel(
                        source_concept_id=new_concept.id,
                        target_concept_id=parent_id,
                        relation_type="is_a",
                        polarity="+",
                        weight=1.00,
                        mechanism_label=f"{new_concept.title} is a subtype of {parent_concept.title}"
                    )
                    review_repo.add(db, new_edge)

        if prepared_knowledge:
            state, evidences, cases = prepared_knowledge
            try:
                await review_repo.save_content(db, concept if concept else new_concept, state, evidences, cases, replace_draft=structured)
            except ValueError as error:
                await db.rollback()
                raise HTTPException(422, str(error)) from error

        # Registering a concept also resolves earlier wiki links that referred to it.
        await db.flush()
        await concept_repo.reconcile_relation_edges(db)

        # 5. Presence Lock 자동 해제

        await db.commit()
        await db.refresh(ticket)
        await db.refresh(audit_entry)
        await cache_manager.release_presence_lock(ticket.id, approver_name)

        for evidence in prepared_knowledge[1] if prepared_knowledge else []:
            await cache_manager.delete(f"evidence:detail:{evidence['id']}")

        # 6. Stale Cache 방지를 위한 연관 캐시 즉시 무효화 (위키 상세 / 서브그래프 / 문맥해설 / 전역검색)
        await cache_manager.delete(f"concept:detail:{ticket.concept_id}")
        await cache_manager.delete_prefix("concept:subgraph:")
        await cache_manager.delete_prefix("concept:tree:")
        await cache_manager.delete_prefix(f"concept:explainer:{ticket.concept_id}:")
        await cache_manager.delete_prefix("spotlight:")

        from backend.app.services.case_explanation_service import case_explanation_service
        case_explanation_service.schedule(background_tasks, [ticket.concept_id], gemini_key=x_gemini_key, openai_key=x_openai_key)

        return ReviewTicketActionResponse(
            ticket=_convert_ticket_to_dto(ticket),
            audit_log=_convert_audit_to_dto(audit_entry),
            concept_updated=concept_updated,
            concept_version=applied_ver,
            guide_tip=guide_tip,
            message=f"거버넌스 티켓 [{ticket.id}]이(가) 공식 승인되었으며, 개념 '{ticket.concept_title}'이(가) {applied_ver} 버전으로 영구 승계되었습니다."
        )

review_service = ReviewService()
