"""Persist public case explanations independently of source/approval transactions."""
import asyncio
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from types import SimpleNamespace

from backend.app.core.database import async_session_factory
from backend.app.core.security import mask_tier3_perspective
from backend.app.repositories.concept_repo import concept_repo
from backend.app.schemas.ontology import CaseContextExplanationDTO
from backend.app.services.comparison_service import public_evidence

logger = logging.getLogger(__name__)
GENERATOR_VERSION = 'case-context-v1'


class CaseExplanationChanged(Exception):
    pass


class CaseExplanationUnavailable(Exception):
    pass


class CaseExplanationService:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory or async_session_factory
        # shortcut: process-local coordination; distributed workers need shared coordination.
        self.inflight = {}
        self.scheduled = Counter()

    @staticmethod
    def raw_case(case):
        return dict(id=case.id, perspectiveTitle=case.perspective_title,
                    perspectiveBadge=case.perspective_badge, contextNarrative=case.context_narrative,
                    specifications=case.specifications or [], caution=case.caution,
                    evidenceId=case.evidence_id)

    async def public_input(self, db, concept, case):
        raw = self.raw_case(case)
        from backend.app.repositories.source_repo import source_repo
        is_public = case.id in await source_repo.public_case_ids(db, concept.id, [case]) if not raw['specifications'] else False
        masked = mask_tier3_perspective(dict(context_narrative=raw['contextNarrative'],
            caution=raw['caution'], specifications=raw['specifications'], evidence_id=raw['evidenceId'], is_public_case=is_public), False)
        if masked['isMasked']:
            return None
        evidence_ids = {raw['evidenceId']} if raw['evidenceId'] else set()
        for spec in raw['specifications']:
            evidence_ids.update(spec.get('evidenceIds') or [])
        if not evidence_ids:
            return None
        evidence = await concept_repo.get_case_evidences(db, sorted(evidence_ids))
        if {e.id for e in evidence} != evidence_ids or not all(public_evidence(e) for e in evidence):
            return None
        fields = ('parameter', 'value', 'unit', 'safetyMargin', 'criteria', 'role', 'tradeoff', 'rationale',
                  'evidenceQuote', 'fieldEvidenceQuotes', 'evidenceIds')
        raw['specifications'] = [{key: spec.get(key) for key in fields if key in spec}
                                 for spec in raw['specifications']]
        return dict(concept=dict(title=concept.title, summary=concept.summary, purpose=concept.purpose),
                    case=raw, evidence=[dict(id=e.id, sourceName=e.source_name, quote=e.quote,
                        sectionContext=e.section_context, externalUrl=e.external_url) for e in sorted(evidence, key=lambda e: e.id)])

    @staticmethod
    def basis_hash(value):
        return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    async def fields(self, db, concept, case):
        value = await self.public_input(db, concept, case)
        if value is None:
            return dict(contextExplanation=None, contextExplanationState='restricted', contextExplanationBasisHash=None)
        basis = self.basis_hash(value)
        saved = None
        if case.context_explanation:
            try:
                saved = CaseContextExplanationDTO.model_validate(case.context_explanation).model_dump()
            except ValueError:
                pass
        ready = saved and saved['basisHash'] == basis and saved['generatorVersion'] == GENERATOR_VERSION
        state = 'ready' if ready else ('generating' if (concept.id, case.id) in self.inflight or self.scheduled[concept.id]
                                      else 'stale' if case.context_explanation else 'missing')
        return dict(contextExplanation=saved if ready else None, contextExplanationState=state,
                    contextExplanationBasisHash=basis)

    async def preview_fields(self, db, concept_id, title, state):
        """Enrich a response copy only; never change materialized source history/signatures."""
        concept = await concept_repo.get_by_id(db, concept_id)
        candidate = SimpleNamespace(id=concept_id, title=title, summary=state['summary'], purpose=state['purpose'])
        saved_cases = {case.id: case for case in concept.perspectives} if concept else {}
        result = {}
        for raw in state['perspectiveCases']:
            stored = saved_cases.get(raw['id'])
            case = SimpleNamespace(id=raw['id'], perspective_title=raw['perspectiveTitle'],
                perspective_badge=raw['perspectiveBadge'], context_narrative=raw['narrative'],
                specifications=raw['specifications'], caution=raw['caution'], evidence_id=raw.get('evidenceId'),
                context_explanation=stored.context_explanation if stored else None)
            fields = await self.fields(db, candidate, case)
            # Public draft evidence may not exist in the DB until application/approval.
            public_case = not mask_tier3_perspective(dict(context_narrative=case.context_narrative,
                caution=case.caution, specifications=case.specifications), False)['isMasked']
            if fields['contextExplanationState'] == 'restricted' and public_case:
                ids = {case.evidence_id} if case.evidence_id else set()
                for spec in case.specifications:
                    ids.update(spec.get('evidenceIds') or [])
                known = await concept_repo.get_case_evidences(db, sorted(ids))
                if ids and {e.id for e in known} != ids and all(public_evidence(e) for e in known):
                    fields['contextExplanationState'] = 'missing'
            result[case.id] = fields
        return result

    async def generate(self, concept_id, case_id, **keys):
        key = (concept_id, case_id)
        if key not in self.inflight:
            task = asyncio.create_task(self._generate(concept_id, case_id, **keys))
            self.inflight[key] = task
            task.add_done_callback(lambda finished: self._finish(key, finished))
        return await asyncio.shield(self.inflight[key])

    def _finish(self, key, task):
        if self.inflight.get(key) is task:
            self.inflight.pop(key, None)
        if not task.cancelled():
            task.exception()  # Observe failures even if every HTTP waiter disconnected.

    async def _generate(self, concept_id, case_id, **keys):
        async with self.session_factory() as db:
            concept = await concept_repo.get_by_id(db, concept_id)
            case = await concept_repo.get_case(db, concept_id, case_id)
            if concept is None or case is None:
                raise LookupError('개념 또는 사례를 찾을 수 없습니다.')
            value = await self.public_input(db, concept, case)
            if value is None:
                raise PermissionError('공개 근거가 확인된 사례만 공용 해설을 생성할 수 있습니다.')
            current = await self.fields(db, concept, case)
            if current['contextExplanationState'] == 'ready':
                return current
            basis = self.basis_hash(value)
        # No transaction or request session remains open while waiting for the model.
        from backend.app.agents.explainer_agent import explainer_agent
        try:
            content = await explainer_agent.explain_case_context(value, f'case-context-{case_id}-{basis}', **keys)
        except Exception as error:
            raise CaseExplanationUnavailable('쉬운 해설을 생성하지 못했습니다. 다시 시도해 주세요.') from error
        payload = CaseContextExplanationDTO(basisHash=basis, generatorVersion=GENERATOR_VERSION,
            generatedAt=datetime.now(timezone.utc).isoformat(), content=content).model_dump()
        async with self.session_factory() as db:
            concept = await concept_repo.get_by_id(db, concept_id)
            case = await concept_repo.get_case(db, concept_id, case_id)
            if concept is None or case is None:
                raise CaseExplanationChanged('생성 중 사례가 삭제되었습니다.')
            value = await self.public_input(db, concept, case)
            if value is None or self.basis_hash(value) != basis:
                raise CaseExplanationChanged('생성 중 내용이 변경되었습니다. 현재 사례에서 다시 시도해 주세요.')
            updated = await concept_repo.save_case_explanation(db, concept_id, case_id,
                case.updated_at, concept.updated_at, payload)
            if not updated:
                raise CaseExplanationChanged('생성 중 내용이 변경되었습니다. 현재 사례에서 다시 시도해 주세요.')
            await db.commit()
        return dict(contextExplanation=payload, contextExplanationState='ready', contextExplanationBasisHash=basis)

    def schedule(self, background_tasks, concept_ids, **keys):
        ids = list(dict.fromkeys(concept_ids))
        self.scheduled.update(ids)
        background_tasks.add_task(self.generate_concepts, ids, **keys)

    async def generate_concepts(self, concept_ids, **keys):
        try:
            for concept_id in concept_ids:
                async with self.session_factory() as db:
                    concept = await concept_repo.get_by_id(db, concept_id)
                    ids = [case.id for case in concept.perspectives] if concept else []
                for case_id in ids:
                    try:
                        await self.generate(concept_id, case_id, **keys)
                    except PermissionError:
                        pass
                    except Exception as error:
                        logger.warning('Case explanation failed (%s)', type(error).__name__)
        except Exception as error:
            logger.warning('Case explanation scheduling failed (%s)', type(error).__name__)
        finally:
            self.scheduled.subtract(concept_ids)
            self.scheduled += Counter()


case_explanation_service = CaseExplanationService()
