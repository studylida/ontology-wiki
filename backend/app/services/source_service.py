"""[계층 3] Source Document Knowledge Ingestion Service Layer.

Executes sequential, deterministic technical knowledge extraction from whitepapers:
- Single-process sequential execution (DocumentLockManager)
- Preprocessing and publisher-specific prompt engineering (playbook rules)
- 4-Tier LLM Gateway integration with structured JSON response
- Wiki DTO conversion (purpose, principles, limitations, perspectives, relations)
- Multi-Source Additive Merging & Idempotent Apply with version checks
"""
import os
import re
import json
import asyncio
import logging
import hashlib
from copy import deepcopy
from datetime import datetime
from uuid import uuid4
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Any, Optional, Set, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.core.database import async_session_factory
from backend.app.core.llm_gateway import llm_gateway
from backend.app.core.cache import cache_manager
from backend.app.models.entities import (
    SourceDocumentModel,
    ConceptModel,
    CausalEdgeModel,
    EvidenceSourceModel,
    PerspectiveCaseModel
)
from backend.app.repositories.source_repo import source_repo
from backend.app.repositories.concept_repo import ID_ALIASES, concept_repo
from backend.app.schemas.source_ingestion import (
    SourceDocumentItemDTO, ExtractionStateDTO,
    ExtractedConceptDiffDTO, ExtractedSpecificationDTO,
    DocumentExtractionResultDTO,
    ExtractionPreviewResponseDTO,
    ApplyExtractionResponseDTO
)
from backend.app.schemas.source_ingestion import ConceptClassificationDTO
from backend.app.schemas.ontology import PrincipleStep, LimitationItem

logger = logging.getLogger("source_service")


class DocumentLockManager:
    """In-memory concurrency lock to prevent duplicate runs or race conditions."""

    def __init__(self):
        self._running_docs: Set[str] = set()
        self._lock = asyncio.Lock()

    async def acquire(self, doc_ids: List[str]) -> bool:
        async with self._lock:
            for did in doc_ids:
                if did in self._running_docs:
                    return False
            for did in doc_ids:
                self._running_docs.add(did)
            return True

    async def release(self, doc_ids: List[str]):
        async with self._lock:
            for did in doc_ids:
                self._running_docs.discard(did)


lock_manager = DocumentLockManager()


class SourceExtractionService:
    """Domain service for scanning, extracting, previewing, and applying whitepapers."""

    def __init__(self, use_examples: bool = False, session_factory=None):
        self.lock_mgr = lock_manager
        self.use_examples = use_examples
        self.session_factory = session_factory or async_session_factory
        # shortcut: latest run is kept in this process; server restart requires explicit recovery.
        self._extraction_run = None

    async def _resume_plan(self, session):
        documents = await source_repo.list_documents(session)
        interrupted = [index for index, doc in enumerate(documents) if doc.attempt_status == "running"]
        if len(interrupted) != 1:
            return [], [], None
        index = interrupted[0]
        prefix = documents[:index]
        # Legacy requests did not save their selection. Recovery explicitly uses the full catalog order.
        if any(doc.attempt_status != "success" or not doc.last_preview_payload for doc in prefix):
            return [], [], documents[index].doc_id
        return [doc.doc_id for doc in documents], [doc.doc_id for doc in prefix], documents[index].doc_id

    async def get_extraction_state(self, session):
        if self._extraction_run is not None:
            run = self._extraction_run
            return ExtractionStateDTO(state=run["state"], runId=run["id"], docIds=run["docIds"],
                                      preservedCount=run["preservedCount"])
        doc_ids, preserved, interrupted = await self._resume_plan(session)
        return ExtractionStateDTO(state="interrupted" if interrupted else "idle", docIds=doc_ids,
                                  preservedCount=len(preserved), interruptedDocId=interrupted)

    async def start_extraction(self, session, doc_ids, force_reextract=False, resume_interrupted=False,
                               openai_key=None, gemini_key=None):
        preserved = []
        if resume_interrupted:
            planned, preserved, _ = await self._resume_plan(session)
            if not planned or doc_ids != planned:
                raise HTTPException(status_code=409, detail="중단된 전체 목록과 완료 이력을 다시 확인해주세요.")
            force_reextract = True
        # No await between this check and registration: one worker owns the latest run.
        if self._extraction_run is not None and not self._extraction_run["done"]:
            raise HTTPException(status_code=409, detail="이미 추출이 실행 중입니다. 진행 상황을 다시 열어주세요.")
        run = {"id": uuid4().hex, "docIds": list(doc_ids), "preservedCount": len(preserved),
               "state": "running", "events": [], "changed": asyncio.Event(), "done": False}
        self._extraction_run = run
        run["task"] = asyncio.create_task(self._produce_extraction(run, force_reextract, preserved, openai_key, gemini_key))
        return run["id"]

    async def _produce_extraction(self, run, force_reextract, preserved, openai_key, gemini_key):
        def record(event):
            run["events"].append(event)
            run["changed"].set()
        try:
            async with self.session_factory() as session:
                async for event in self.stream_sequential_extraction(session, run["docIds"], force_reextract,
                        openai_key, gemini_key, preserved_doc_ids=preserved):
                    if event.startswith("event: start\n"):
                        data = json.loads(event.split("data: ", 1)[1])
                        event = "event: start\ndata: " + json.dumps({**data, "runId": run["id"]}, ensure_ascii=False) + "\n\n"
                    if event.startswith("event: finished\n"):
                        run["state"] = "finished"
                    elif event.startswith("event: error\n"):
                        run["state"] = "error"
                    record(event)
        except asyncio.CancelledError:
            run["state"] = "error"
            record('event: error\ndata: {"message":"서버 종료로 추출이 중단되었습니다. 완료 문서는 보존됩니다."}\n\n')
            raise
        except Exception:
            logger.exception("Source extraction worker failed")
            run["state"] = "error"
            record('event: error\ndata: {"message":"추출 작업을 완료하지 못했습니다. 저장된 문서 결과를 확인해주세요."}\n\n')
        finally:
            if run["state"] == "running":
                run["state"] = "error"
                record('event: error\ndata: {"message":"추출 종료 결과를 확인하지 못했습니다."}\n\n')
            run["done"] = True
            run["changed"].set()

    def extraction_events(self, run_id):
        run = self._extraction_run
        if run is None or run["id"] != run_id:
            raise HTTPException(status_code=404, detail="해당 추출 진행 기록이 없습니다. 문서 이력을 확인해주세요.")
        return self._subscribe_extraction(run)

    async def _subscribe_extraction(self, run):
        index = 0
        while True:
            while index < len(run["events"]):
                event = run["events"][index]
                index += 1
                yield event
            if run["done"]:
                return
            run["changed"].clear()
            try:
                await asyncio.wait_for(run["changed"].wait(), timeout=15)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"


    def judgment_examples(self, stage, source_text):
        """Select bounded source-backed examples; they never supply current-document facts."""
        if not self.use_examples:
            return ""
        book = json.loads(Path(__file__).with_name("source_extraction_examples.json").read_text(encoding="utf-8"))
        text = source_text.casefold()
        scored = [(sum(keyword.casefold() in text for keyword in example["keywords"]), example)
                  for example in book["examples"] if stage in example["expected"]]
        ranked = sorted(scored, key=lambda pair: -pair[0])
        selected = []
        size = 0
        for score, example in ranked:
            if score == 0:
                continue
            value = json.dumps({"judgment": example["judgment"], "sourcePath": example["sourcePath"],
                "excerpt": example["excerpt"], "partialExpected": example["expected"][stage],
                "rationale": example["rationale"], "commonMistake": example["commonMistake"]}, ensure_ascii=False)
            if size + len(value) > 6000:
                continue
            selected.append(value)
            size += len(value)
            if len(selected) == 2:
                break
        if not selected:
            return ""
        return ("\n[다른 원문의 판단 연습 예시 — 현재 입력의 지식·근거가 아님]\n"
                "판단 방법만 참고하라. 예시의 개념·회사·수치·ID를 현재 원문에 없는 채로 출력하지 마라. "
                "예시 줄 번호는 발췌 안의 번호이며 현재 입력의 근거 줄로 사용할 수 없다. "
                "부분 JSON의 생략된 필드는 현재 입력과 본래 출력 스키마에 따라 처리하라. "
                "예시 목록 밖의 새로운 기술·판단도 같은 원칙으로 처리하라.\n" + "\n".join(selected))


    @staticmethod
    def extraction_classification(item):
        fields = {"domainFacet": item.get("domainFacet"), "category": item.get("category") or "미분류",
                  "scaleLevel": item.get("scaleLevel")}
        try:
            return ConceptClassificationDTO(**fields).model_dump(by_alias=True), item.get("classificationNote")
        except ValidationError as error:
            for issue in error.errors():
                field = issue["loc"][0]
                fields[field] = "미분류" if field == "category" else None
            note = "분류 응답 형식을 확인하지 못해 미확정으로 남겼습니다. 관리자 검토가 필요합니다."
            return ConceptClassificationDTO(**fields).model_dump(by_alias=True), note

    @staticmethod
    def evidence_id(doc_id: str, concept_id: str, quote: str) -> str:
        key = f"{concept_id}:{quote}"
        return f"E-SRC-{doc_id}-{hashlib.sha256(key.encode()).hexdigest()[:8]}"

    def validate_quotes(self, item: Dict[str, Any], source_text: str) -> Dict[str, Any]:
        """Normalize candidates; citation spelling/location does not decide acceptance."""
        result = deepcopy(item)
        # Compatibility flags control merging, not literal quote verification.
        result["evidenceVerified"] = bool(result.get("evidenceQuote"))
        for field in ("summary", "purpose"):
            result[f"{field}EvidenceVerified"] = bool(result.get(field))
        warnings = list(result.get("validationWarnings") or [])
        for field in ("principles", "limitations", "perspectiveCases"):
            values = []
            for raw in result.get(field) or []:
                value = ({"content": raw} if field == "principles" else {"description": raw}) if isinstance(raw, str) else dict(raw)
                value["evidenceVerified"] = True
                if field == "perspectiveCases":
                    specs = []
                    for raw_spec in value.get("specifications") or []:
                        try:
                            spec = ExtractedSpecificationDTO(**raw_spec).model_dump()
                        except (ValidationError, TypeError):
                            warnings.append("사례 파라미터 형식을 확인하지 못해 제외합니다.")
                            continue
                        if not spec["parameter"].strip():
                            warnings.append("이름이 없는 사례 파라미터를 제외합니다.")
                            continue
                        spec["fieldEvidenceQuotes"] = {key: quote for key, quote in spec["fieldEvidenceQuotes"].items()
                            if key in ("value", "unit", "safetyMargin", "role", "tradeoff", "rationale")}
                        for key in ("value", "unit", "safetyMargin", "role", "tradeoff", "rationale"):
                            spec[key] = spec[key].strip() or None if spec[key] is not None else None
                        spec["evidenceVerified"] = True
                        if spec["value"] and spec["unit"]:
                            spec["value"] = spec["value"].replace(spec["unit"], "").strip()
                        specs.append(spec)
                    value["specifications"] = specs
                values.append(value)
            result[field] = values
        for field in ("previousSteps", "nextSteps", "alternatives", "partOf", "isA"):
            for relation in result.get(field) or []:
                relation["evidenceVerified"] = True
        result["validationWarnings"] = list(dict.fromkeys(warnings))
        return result

    def normalize_concept(self, item: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Use the existing wiki contract for both new extractions and saved previews."""
        result = dict(item)
        evidence_id = self.evidence_id(doc_id, item["conceptId"], item.get("evidenceQuote") or "")
        def evidence_ids(value):
            return [self.evidence_id(doc_id, item["conceptId"], value["evidenceQuote"])] if value.get("evidenceVerified") and value.get("evidenceQuote") else []
        for field in ("previousSteps", "nextSteps", "alternatives", "partOf", "isA"):
            result[field] = [{**rel, "evidenceIds": [self.evidence_id(doc_id, item["conceptId"], rel["evidenceQuote"])]
                              if rel.get("evidenceVerified") and rel.get("evidenceQuote") else []}
                             for rel in item.get(field) or []]
        principles = []
        for index, raw in enumerate(item.get("principles") or [], start=1):
            p = {"content": raw} if isinstance(raw, str) else raw
            normalized = PrincipleStep(
                step=p.get("step") or index,
                title=p.get("title") or p.get("name") or "",
                content=p.get("content") or p.get("mechanism") or "",
                formula=p.get("formula")
            ).model_dump()
            principles.append({**p, **normalized, "evidenceIds": evidence_ids(p)})
        limitations = []
        for raw in item.get("limitations") or []:
            lim = {"title": raw[:40], "description": raw} if isinstance(raw, str) else raw
            normalized = LimitationItem(
                title=lim.get("title") or lim.get("description", "")[:40],
                description=lim.get("description") or lim.get("title", ""),
                evidence_ids=evidence_ids(lim)
            ).model_dump(by_alias=True)
            limitations.append({**lim, **normalized})
        cases = [{**case, "narrative": case.get("narrative") or case.get("contextNarrative") or "",
                  "specifications": [{**spec, "evidenceIds": list(dict.fromkeys(
                      self.evidence_id(doc_id, item["conceptId"], quote) for quote in
                      [spec["evidenceQuote"], *spec.get("fieldEvidenceQuotes", {}).values()] if quote))}
                      for spec in case.get("specifications") or [] if spec.get("evidenceVerified")],
                  "evidenceIds": evidence_ids(case)}
                 for case in item.get("perspectiveCases") or []]
        result.update(principles=principles, limitations=limitations, perspectiveCases=cases)
        return result

    @staticmethod
    def case_content(case):
        return {"perspectiveTitle": case.get("perspectiveTitle") or "", "perspectiveBadge": case.get("perspectiveBadge") or "",
                "narrative": case.get("narrative") or case.get("contextNarrative") or "",
                "specifications": case.get("specifications") or [], "caution": case.get("caution") or ""}

    def case_history(self, doc, raw):
        if "_appliedCases" in raw:
            return deepcopy(raw["_appliedCases"])
        # Existing previews used positional IDs; retain their last applied content for edit protection.
        if doc.is_applied:
            history = {}
            for i, case in enumerate(raw.get("perspectiveCases") or [], start=1):
                key = f"{raw['conceptId']}:{doc.doc_id}:{i}"
                history[f"case-{hashlib.sha256(key.encode()).hexdigest()[:24]}"] = self.case_content(
                    {**case, "perspectiveBadge": case.get("perspectiveBadge") or doc.publisher})
            return history
        return {}

    @staticmethod
    def relation_content(link):
        ignored = {"id", "targetId", "name", "targetName", "evidenceIds", "evidenceQuote", "evidenceLine", "evidenceVerified", "_preserve"}
        return {**{key: value for key, value in link.items() if key not in ignored},
                "target": link.get("id") or link.get("targetId"), "name": link.get("name") or link.get("targetName")}

    @staticmethod
    def relation_history(doc, raw):
        if "_appliedRelations" in raw:
            return deepcopy(raw["_appliedRelations"])
        if doc.is_applied:
            return {field: deepcopy(raw.get(field) or []) for field in ("previousSteps", "nextSteps", "alternatives", "partOf", "isA")}
        return {}

    def merge_content(self, item, state, doc_id):
        """The preview and apply use the same preservation and enrichment rules."""
        warnings = item.setdefault("validationWarnings", [])
        for field in ("summary", "purpose"):
            incoming = (item.get(field) or "").strip()
            if not incoming or not item.get(f"{field}EvidenceVerified"):
                continue
            if not (state.get(field) or "").strip():
                state[field] = incoming
            elif state[field].strip() != incoming:
                warnings.append(f"{field}: 기존 본문을 유지합니다. 새 추출 설명은 덮어쓰지 않습니다.")
        if not (state.get("summary") or "").strip() and (state.get("purpose") or "").strip():
            state["summary"] = state["purpose"]
        for field, keys in (("principles", ("title", "content", "formula")), ("limitations", ("title", "description"))):
            for value in item[field]:
                if not value.get("evidenceVerified") or not (value.get("content") or value.get("description") or "").strip():
                    continue
                match = next((old for old in state[field] if all(old.get(k) == value.get(k) for k in keys)), None)
                if match is None:
                    state[field].append(deepcopy(value))
                else:
                    match["evidenceIds"] = list(dict.fromkeys((match.get("evidenceIds") or []) + value["evidenceIds"]))
        removed = []
        preserved = set()
        retained = {}
        for field, links in item.get("_appliedRelations", {}).items():
            for prior in links:
                target = prior.get("id") or prior.get("targetId")
                current = next((link for link in state[field] if (link.get("id") or link.get("targetId")) == target), None)
                if current is None:
                    continue
                if (field, target) in item.get("_retainRelations", set()):
                    retained.setdefault(field, []).append(deepcopy(prior))
                    warnings.append(f"{field}/{target}: 이번 추출의 누락만으로 기존 관계를 삭제하지 않습니다.")
                    continue
                if self.relation_content(current) != self.relation_content(prior):
                    warnings.append(f"{field}/{target}: 이전 적용 이후 수정된 관계를 보존합니다.")
                    preserved.add((field, target))
                    continue
                remaining = [eid for eid in current.get("evidenceIds") or [] if eid not in (prior.get("evidenceIds") or [])]
                if remaining or prior.get("_preserve") or (field, target) in item.get("_sharedRelations", set()):
                    current["evidenceIds"] = remaining
                    if prior.get("_preserve"):
                        preserved.add((field, target))
                    continue
                state[field].remove(current)
                removed.append({"sourceId": item["conceptId"], "field": field, "link": deepcopy(prior)})
        item["_removedRelations"] = removed
        applied_relations = {}
        for field in ("previousSteps", "nextSteps", "alternatives", "partOf", "isA"):
            applied_relations[field] = retained.get(field, [])
            for link in item[field]:
                if not link.get("evidenceVerified"):
                    continue
                target = link.get("id") or link.get("targetId")
                match = next((old for old in state[field] if (old.get("id") or old.get("targetId")) == target), None)
                recorded = next((old for old in applied_relations[field] if (old.get("id") or old.get("targetId")) == target), None)
                preserve = (recorded.get("_preserve", False) if recorded else
                    (field, target) in preserved or (match is not None and
                     (not match.get("evidenceIds") or self.relation_content(match) != self.relation_content(link))))
                if match is None:
                    match = deepcopy(link)
                    state[field].append(match)
                else:
                    for key, value in link.items():
                        if not match.get(key):
                            match[key] = deepcopy(value)
                    match["evidenceIds"] = list(dict.fromkeys((match.get("evidenceIds") or []) + link["evidenceIds"]))
                own_ids = list(dict.fromkeys((recorded.get("evidenceIds", []) if recorded else []) + link["evidenceIds"]))
                entry = {**deepcopy(match), "evidenceIds": own_ids, "_preserve": preserve}
                if recorded:
                    recorded.update(entry)
                else:
                    applied_relations[field].append(entry)
        item["_appliedRelations"] = applied_relations

        history = deepcopy(item.get("_appliedCases") or {})
        prior_history = deepcopy(history)
        updates = []
        for incoming in item["perspectiveCases"]:
            if not incoming.get("evidenceVerified") or not incoming.get("narrative", "").strip():
                continue
            content = self.case_content(incoming)
            title = content["perspectiveTitle"].strip().casefold()
            matches = [key for key, old in prior_history.items() if old["perspectiveTitle"].strip().casefold() == title]
            if sum(self.case_content(case)["perspectiveTitle"].strip().casefold() == title for case in item["perspectiveCases"]) > 1:
                matches = []
            key = f"{item['conceptId']}:{doc_id}:{json.dumps(content, sort_keys=True)}"
            case_id = matches[0] if len(matches) == 1 else f"case-{hashlib.sha256(key.encode()).hexdigest()[:24]}"
            current = next((case for case in state["perspectiveCases"] if case["id"] == case_id), None)
            if current and case_id in history and self.case_content(current) != history[case_id]:
                warnings.append(f"적용 사례 '{content['perspectiveTitle']}': 기존 사례가 추출 이후 수정되어 보존합니다. 새 사례안은 보류합니다.")
                continue
            case = {**content, "id": case_id, "evidenceId": next(iter(incoming["evidenceIds"]), None)}
            if current:
                current.update(case)
            else:
                state["perspectiveCases"].append(case)
            history[case_id] = content
            updates.append(case)
        item["_appliedCases"] = history
        item["_caseUpdates"] = updates
        item["mergedPreview"] = state
        self.check_completion(item)

    @staticmethod
    def check_completion(item):
        state = item["mergedPreview"]
        item["missingFields"] = [label for field, label in (("summary", "개요"), ("purpose", "목적"), ("principles", "원리"), ("limitations", "한계"), ("perspectiveCases", "적용 사례")) if not state[field]]
        blockers = [message for message in item.get("applyBlockers", []) if message.startswith("원문이 변경")]
        coverage = item.get("sourceCoverage") or {}
        if not (coverage.get("complete") and coverage.get("processedParts", 0) > 0
                and coverage.get("processedParts") == coverage.get("totalParts")
                and coverage.get("processedCharacters", 0) > 0
                and coverage.get("processedCharacters") == coverage.get("totalCharacters")):
            blockers.append("전체 원문 처리 이력이 없습니다. 문서를 다시 추출해주세요.")
        if not (state.get("summary") or "").strip():
            blockers.append("개요가 없어 새 위키를 적용할 수 없습니다.")
        item["applyBlockers"] = blockers

    async def prepare_preview(self, session, doc, raw_items, states=None):
        states = states if states is not None else {}
        catalog = await concept_repo.get_all_concepts(session)
        applied_documents = await source_repo.get_documents_with_applied_history(session)
        def resolve_links(links):
            result = deepcopy(links)
            for link in result:
                key = "targetId" if "targetId" in link else "id"
                link[key] = concept_repo.resolve_reference_id(link.get(key), link.get("name") or link.get("targetName"), catalog)
            return result
        file_path = source_repo.resolve_safe_file_path(doc)
        source_text = file_path.read_text(encoding="utf-8")
        _, _, source_url = source_repo.extract_title_and_metadata(file_path)
        previews = []
        for raw in raw_items:
            cid = concept_repo.resolve_reference_id(raw["conceptId"], raw.get("title"), catalog)
            item = self.normalize_concept(self.validate_quotes({**raw, "conceptId": cid, "sourceUrl": source_url}, source_text), doc.doc_id)
            existing = next((c for c in catalog if c.id == cid), None)
            item["classificationProposals"] = raw.get("classificationProposals") or [{
                **ConceptClassificationDTO(**raw).model_dump(by_alias=True), "classificationNote": raw.get("classificationNote")}]
            if existing:
                item.update(domainFacet=existing.domain_facet, category=existing.process_category, scaleLevel=existing.scale_level)
            item["isNew"] = existing is None
            item["existingClassification"] = ({"domainFacet": existing.domain_facet, "category": existing.process_category,
                                               "scaleLevel": existing.scale_level} if existing else None)
            if cid not in states:
                relations = (existing.relations or {}) if existing else {}
                cases = await source_repo.get_perspective_cases(session, cid)
                states[cid] = {"summary": existing.summary if existing else "", "purpose": existing.purpose if existing else "",
                               "principles": deepcopy(existing.principles or []) if existing else [],
                               "limitations": deepcopy(existing.limitations or []) if existing else [],
                               "perspectiveCases": [{"id": c.id, "perspectiveTitle": c.perspective_title, "perspectiveBadge": c.perspective_badge,
                                  "narrative": c.context_narrative, "specifications": deepcopy(c.specifications or []), "caution": c.caution, "evidenceId": c.evidence_id} for c in cases],
                               **{field: deepcopy(concept_repo.relation_items(relations.get(key))) for key, field in
                                  (("previous_step", "previousSteps"), ("next_step", "nextSteps"), ("alternative_to", "alternatives"), ("part_of", "partOf"), ("is_a", "isA"))}}
            item["_appliedCases"] = self.case_history(doc, raw)
            item["_appliedRelations"] = {field: resolve_links(links) for field, links in self.relation_history(doc, raw).items()}
            shared = set()
            for other in applied_documents:
                if other.doc_id == doc.doc_id:
                    continue
                for previous in other.last_preview_payload or []:
                    if concept_repo.resolve_reference_id(previous["conceptId"], previous.get("title"), catalog) != cid:
                        continue
                    for field, links in self.relation_history(other, previous).items():
                        shared.update((field, link.get("id") or link.get("targetId")) for link in resolve_links(links))
            item["_sharedRelations"] = shared
            retained = set()
            corrections = {(entry["field"], concept_repo.resolve_reference_id(entry["targetId"], entry.get("targetName"), catalog))
                           for entry in item.get("relationCorrections", [])}
            for field in ("previousSteps", "nextSteps", "alternatives", "partOf", "isA"):
                item[field] = resolve_links(item[field])
                states[cid][field] = resolve_links(states[cid][field])
                incoming = {link.get("id") or link.get("targetId") for link in item[field] if link.get("evidenceVerified")}
                for prior in item["_appliedRelations"].get(field, []):
                    target = prior.get("id") or prior.get("targetId")
                    if target in incoming:
                        continue
                    if (field, target) in corrections:
                        continue
                    normalized = lambda value: re.sub(r"\s+", "", value or "").casefold()
                    target_concept = next((concept for concept in catalog if concept.id == target), None)
                    names = [prior.get("name"), prior.get("targetName")]
                    if target_concept:
                        names += [target_concept.title, target_concept.eng_name, *(target_concept.aliases or [])]
                    mentioned = any(len(normalized(name)) >= 2 and normalized(name) in normalized(source_text) for name in names)
                    # Missing model output is not a retraction; only uncited, unmentioned legacy alternatives retire automatically.
                    if field != "alternatives" or mentioned or prior.get("evidenceIds") or prior.get("evidenceQuote"):
                        retained.add((field, target))
                    else:
                        item["validationWarnings"].append(f"{field}/{target}: 이전 원문 기여의 대안 대상명·별칭을 원문에서 확인하지 못해 정정합니다.")
            item["_retainRelations"] = retained
            self.merge_content(item, states[cid], doc.doc_id)
            coverage = item.get("sourceCoverage") or {}
            if coverage.get("sourceHash") != source_repo.compute_file_hash(file_path):
                item["applyBlockers"].append("원문이 변경되었거나 처리 범위를 확인할 수 없습니다. 다시 추출해주세요.")
            previews.append(item)
        return previews

    async def get_document_preview(self, session: AsyncSession, doc_id: str) -> Dict[str, Any]:
        doc = await source_repo.get_by_doc_id(session, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        previews = await self.prepare_preview(session, doc, doc.last_preview_payload or [])
        from backend.app.services.case_explanation_service import case_explanation_service
        for item in previews:
            state = deepcopy(item["mergedPreview"])
            fields = await case_explanation_service.preview_fields(session, item["conceptId"], item["title"], state)
            for case in state["perspectiveCases"]:
                case.update(fields[case["id"]])
            item["mergedPreview"] = state
        return {
            "docId": doc.doc_id, "title": doc.title, "filePath": doc.file_path,
            "attemptStatus": doc.attempt_status,
            "lastSucceededAt": doc.last_succeeded_at.isoformat() if doc.last_succeeded_at else None,
            "isApplied": doc.is_applied,
            "preview": [ExtractedConceptDiffDTO(**item).model_dump(by_alias=True) for item in previews]
        }

    def clean_web_noise(self, text: str) -> str:
        """Strip navigation bars, headers, social buttons, and cookie banners."""
        metadata = re.match(r"\A---[^\S\n]*\n(.*?)\n---[^\S\n]*(?:\n|$)", text, flags=re.DOTALL)
        if metadata and re.search(r"^[A-Za-z_][\w-]*:\s", metadata[1], re.MULTILINE):
            text = text[metadata.end():]
        # Captured web navigation is not part of the article's technical evidence.
        navigation = re.search(r"^메뉴 열기\s*$", text, re.MULTILINE)
        if navigation:
            article = re.search(r"^#{1,6}\s+\[[^\n]+", text[navigation.end():], re.MULTILINE)
            if article:
                text = text[navigation.end() + article.start():]
        skip_patterns = [
            r"본문 바로가기",
            r"Internet Explorer를 지원하지 않습니다",
            r"메뉴 열기",
            r"검색 레이어 열기",
            r"프레스센터",
            r"통합검색",
            r"검색어 입력",
            r"검색어 삭제",
            r"최신순",
            r"조회순",
            r"전체 날짜",
            r"공유 레이어 열기",
            r"인쇄하기",
            r"페이스북",
            r"카카오톡",
            r"주소복사",
            r"구독과 좋아요",
            r"패밀리 사이트",
            r"뉴스룸 소개",
            r".*All rights reserved.*",
            r"circle-arrow\d.*"
        ]
        regex = re.compile("|".join(skip_patterns), re.IGNORECASE)
        cleaned_lines = []
        for line in text.splitlines():
            trimmed = line.strip()
            if trimmed in ["-", "*", "#", ">"]:
                continue
            if regex.fullmatch(trimmed):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def build_publisher_prompt(self, publisher: str) -> str:
        """Use one source-grounded wiki contract regardless of the publisher."""
        base_instruction = """당신은 반도체 지식 위키의 공정·소자·운영·소재 지식을 구조화하는 엔지니어다.
주어진 원문에서 확인할 수 있는 정보만 분석하여 다음 JSON 스키마 규격으로만 지식을 구조화하여 출력하라.
절대로 허구의 정보를 날조하지 마라. 원문에 명시된 내용만 객관적으로 기술하라.

[출력 JSON 구조]:
{
  "concepts": [
    {
      "id": "개념을 구분하는 영문 소문자 ID. 등록 목록의 동일 개념 ID를 재사용",
      "title": "개념의 국문명. 제품·소자·공정·설비를 서로 혼동하지 말 것",
      "engName": "원문에 있는 영문명. 없으면 빈 문자열",
      "domainFacet": "device(소자·제품·구조), unit_process(제조 공정), operations(팹 운영·제어), materials_infra(소재·설비·인프라) 중 맞는 값. 판단 불가 시 null",
      "category": "해당 분야에 맞는 분류명. 제품을 제조 공정군으로 강제 분류하지 말 것. 판단 불가 시 미분류",
      "scaleLevel": "개념 자체의 대상 규모: 1 원자·물성·계면, 2 박막·소자·회로·패키지, 3 공정·레시피, 4 설비·시스템·모듈, 5 팹·운영·인프라. 회로·칩·패키지 구조와 이를 만드는 공정·장비를 구분하고 사용처의 규모로 대신하지 마라. 판단 불가 시 null. 정수 또는 null",
      "classificationNote": "분야와 규모를 선택한 원문상 이유. 지식 분류와 물리적 규모는 별개로 판단",
      "summary": "이 원문 구간이 설명하는 개념 정의와 이를 구분하는 정량 조건. 없으면 빈 문자열",
      "summaryEvidenceLine": "개요를 뒷받침하는 이번 원문 구간의 줄 번호 (정수). 없으면 null",
      "purpose": "이 원문 구간에 명시된 도입 목적. 없으면 빈 문자열",
      "purposeEvidenceLine": "목적을 뒷받침하는 이번 원문 구간의 줄 번호 (정수). 없으면 null",
      "principles": [
        {
          "step": 1,
          "title": "원리 단계명",
          "content": "원문 원리·메커니즘, 수식 변수의 의미와 명시된 값·조건",
          "formula": null,
          "equipment": "사용되는 챔버/설비 모듈",
          "materials": "투입 가스/소재/케미컬",
          "evidenceLine": null
        }
      ],
      "limitations": [
        {"title": "한계 제목", "description": "원문에 명시된 한계", "evidenceLine": null}
      ],
      "perspectiveCases": [
        {
          "perspectiveTitle": "원문에 명시된 회사·제품·상황을 구분하는 사례 제목",
          "perspectiveBadge": "원문에 명시된 제품·도메인. 없으면 빈 문자열",
          "narrative": "해당 회사·제품·상황의 적용 맥락. 적용 예정·전망·설명용 예시를 실제 양산 사례로 바꾸지 말 것",
          "caution": "원문에 있는 주의사항. 없으면 빈 문자열",
          "evidenceLine": null,
          "specifications": [{
            "parameter": "해당 사례의 파라미터명",
            "value": "원문에 적힌 수치·범위·부등호 그대로. 없으면 null",
            "unit": "원문 단위 그대로. 없으면 null",
            "safetyMargin": "명시된 허용 공차·안전 마진 그대로. 없으면 null",
            "role": "원문이 설명한 제어 목적. 없으면 null",
            "tradeoff": "원문이 설명한 트레이드오프. 없으면 null",
            "rationale": "원문이 설명한 마진 설정 근거. 없으면 null",
            "isConfidential": false,
            "evidenceLine": null,
            "fieldEvidenceLines": {"value": null, "unit": null, "safetyMargin": null, "role": null, "tradeoff": null, "rationale": null}
          }]
        }
      ],
      "previousSteps": [
        {"id": "선행공정ID", "name": "선행 공정명", "reason": "연결 사유 및 물리적 진입 조건", "evidenceLine": null}
      ],
      "nextSteps": [
        {"id": "후속공정ID", "name": "후속 공정명", "reason": "연결 사유 및 후속 공정 투입 목적", "evidenceLine": null}
      ],
      "alternatives": [
        {
          "targetId": "대체기술ID",
          "targetName": "대체 기술명",
          "commonGoal": "공통 기술적 목표",
          "tradeoff": "원문에서 비교한 장단점. 원문에 없으면 null",
          "evidenceLine": null
        }
      ],
      "partOf": [
        {"id": "상위개념ID", "name": "실제 상위 대상명", "reason": "소속 관계. 단순 연관·연결을 소속 관계로 바꾸지 말 것", "evidenceLine": null}
      ],
      "isA": [{"id": "상위분류ID", "name": "상위 분류명", "reason": "원문상 분류 관계", "evidenceLine": null}],
      "evidenceLine": null
    }
  ]
}
관련 정보가 없으면 빈 배열 또는 null을 반환하라. 모든 칸을 채우려고 추론하지 말 것.
정보가 없는 선택 필드는 키를 생략해도 된다. 용어 정의만 있는 항목은 신원·분류·summary·summaryEvidenceLine만 반환하라. 정보가 있는 원리·한계·사례·관계는 생략하지 말 것. 공백 들여쓰기 없이 간결한 JSON으로 반환하라.
요약·목적·원리·한계·사례·관계는 원문 전체 맥락으로 추출하라. 참고 줄 번호는 선택 메타데이터이며 한 줄로 설명할 수 없으면 null이어도 내용을 생략하지 마라. 근거 없는 내용을 생성하지 마라.
원문 줄 번호를 제공할 수 있으면 summaryEvidenceLine/purposeEvidenceLine/evidenceLine에 기록하라. 줄 번호나 인용문 문자열의 일치는 추출 조건이 아니다. 소제목·앞뒤 문장에 걸친 근거도 함께 해석하라.
주어진 구간의 기술 개념과 용어 정의를 끝까지 처리하라. 대표 개념만 골라 나머지를 생략하지 마라.
원문의 기술·세대별 정량 조건, 수식 변수의 값·이론 한계·도달 수준은 정의·원리·한계의 일부다. 회사·제품 적용 사례가 없어도 해당 summary·principles·limitations에 맥락과 함께 보존하라. 정의를 짧게 요약하면서 이를 생략하거나 수치를 담기 위해 가상 사례를 만들지 마라. 이론 한계와 도달 수준, 이전과 이후 조건을 구분하고 약/수준/근접 등 한정어를 유지하라. 원문에 없는 값은 채우지 않으며, 수치가 없는 유용한 정의·원리·사례도 그대로 추출하라.
원문에서 비교하는 기술·제품 대안은 보존하되, 제조 전후 순서와 원인·결과를 혼동하지 말 것.
관계 배열의 주체는 그 배열을 가진 현재 개념이다. 문서 안의 다른 기술끼리 비교한 내용을 문서의 대표 개념의 alternatives로 붙이지 마라. 광범위한 최종 목표가 같다는 이유만으로 선행·후속 공정을 대체 기술로 만들지 마라.
원문이 정의한 상위 개념과 하위 방식은 구분하라. 문서의 주제와 비교 문장의 실제 주체는 다를 수 있다. 각 정의·순서·대조를 그 원문에서 확인되는 주체와 대상에만 귀속하라.
isA는 대상의 종류에 포함되는 관계이고 partOf는 실제 구성요소의 소속 관계이다. 사용하는 장비·연결 대상·적용 분야·평가 기준·도입 목적을 종류나 소속으로 바꾸지 마라.
비유와 홍보 문구는 정의에서 제외하되, 원문에 기술적 설명이 없으면 사전 지식으로 공학적 메커니즘을 보충하지 마라.
단순 특성·지표·표준·설비를 제조 공정으로 강제 분류하지 마라. 분류가 모호하면 null 또는 미분류로 남겨 관리자 검토에 전달하라.
교육 시리즈의 다음 편 소개는 실제 후속 공정의 근거가 아니다.
회사·제품·상황별 사례는 해당 기술 개념의 perspectiveCases로 각각 추출하라. 단순 발행처 이름을 적용 회사로 추정하지 마라. 수치는 원문에 있는 해당 사례에만 귀속하라. 일반 원리의 수치를 모든 회사 사례에 복사하지 마라.
원문에 여러 회사·제품의 적용 사례가 있으면 대표 사례 하나만 고르지 말고 각 맥락을 분리하라. 수치가 없는 사례도 보존하고 specifications는 빈 배열로 두어라. 특정 제품·설계 조건의 피치·적층 수·높이·공차·성능 지표가 설명되면 그 조건의 사례에 파라미터로 추출하라. 개발/출시 연도·날짜는 공정 파라미터가 아니므로 narrative에만 남겨라. value에서는 단위를 분리하되 수치·범위·약/이상/이하·부등호를 보존하라.
사례 내 파라미터의 evidenceLine 및 fieldEvidenceLines에 각각 근거 줄 번호를 반환하라. value/unit/safetyMargin은 원문 표기를 그대로 복사하라.
보호 토큰 [RATIO_REGIME_METRIC: ...], [DIM_REGIME_SCALE: ...], [TEMP_REGIME_PEAK: ...] 등의 내부 숫자는 실제 수치가 아니다. 값에는 전체 토큰을 그대로 복사하고 원문 한정어를 보존하라. 토큰을 환산하거나 내부 숫자로 바꾸지 마라. 서버가 복원한다. 단위가 확인되지 않으면 null로 두어라. '돌파'·'약'·'이상'·'이하'도 수치 의미의 일부이며 제거하지 마라. 목표치·실측치·전망·일반 한계값을 안전 마진으로 바꾸거나 마진을 계산하지 마라. 공개 문서의 수치는 회사명만으로 대외비로 분류하지 마라. 근거가 없는 필드는 null로 유지하라.
기존 등록 개념 목록과 동일한 개념은 기존 ID를 재사용하라. 이름이 비슷하다는 이유로 서로 다른 개념을 합치지 말 것.
"""
        return base_instruction


    @staticmethod
    def document_parts(text, limit=3000):
        """Cover every character; prefer paragraph boundaries over cutting a sentence."""
        parts = []
        start = 0
        while start < len(text):
            end = min(start + limit, len(text))
            if end < len(text):
                boundary = text.rfind("\n\n", start + limit // 2, end)
                if boundary < 0:
                    boundary = text.rfind("\n", start + limit // 2, end)
                if boundary >= 0:
                    end = boundary + 1
            parts.append((start, end))
            start = end
        return parts

    @staticmethod
    def resolve_quote_lines(item, lines):
        """Attach an available source line as metadata without dropping extraction content."""
        result = deepcopy(item)
        def resolve(value, field="evidence"):
            key = field + "Line"
            number = value.get(key)
            if type(number) is int and number in lines:
                value[field + "Quote"] = lines[number]
        resolve(result)
        resolve(result, "summaryEvidence")
        resolve(result, "purposeEvidence")
        for field in ("principles", "limitations", "perspectiveCases", "previousSteps", "nextSteps", "alternatives", "partOf", "isA"):
            for value in result.get(field) or []:
                if isinstance(value, dict):
                    resolve(value)
                    if field == "perspectiveCases":
                        for spec in value.get("specifications") or []:
                            resolve(spec)
                            spec["fieldEvidenceQuotes"] = {**spec.get("fieldEvidenceQuotes", {}), **{key: lines[number]
                                for key, number in (spec.get("fieldEvidenceLines") or {}).items() if type(number) is int and number in lines}}
        return result

    async def complete_classifications(self, doc, items, openai_key=None, gemini_key=None):
        """Index an identified source subject without asking the model to invent wiki content."""
        pending = [item for item in items if not item.get("_classificationConflicts")
                   and (item.get("domainFacet") is None or item.get("scaleLevel") is None)]
        for start in range(0, len(pending), 20):
            batch = pending[start:start + 20]
            rows = [{"conceptId": item["conceptId"], "title": item["title"], "engName": item["engName"],
                     "definition": item.get("summary") or "", "sourceQuote": item.get("summaryEvidenceQuote"),
                     "domainFacet": item.get("domainFacet"), "scaleLevel": item.get("scaleLevel")} for item in batch]
            prompt = (f"- 파일경로: {doc.file_path}\n- 처리 구간: 분류 검토 {start // 20 + 1}\n"
                      + json.dumps(rows, ensure_ascii=False))
            instruction = """원문 정의가 설명하는 대상의 위키 색인 분류만 검토하라. 본문 지식이나 관계를 추가하지 마라.
분야 domainFacet: device(소자·제품·구조), unit_process(제조 공정), operations(팹 운영·제어), materials_infra(소재·설비·인프라).
대상 규모 scaleLevel: 1 원자·물질·물성·기초 현상, 2 박막·소자·회로·패키지, 3 공정·레시피, 4 설비·시스템·모듈, 5 팹·운영·인프라. 회로·칩·패키지 구조와 이를 만드는 공정·장비를 구분하고 사용처의 규모로 대신하지 마라.
분류는 원문 대상의 종류를 위키 탐색 기준에 대응시키는 색인 값이다. 원문에 'Scale N'이라는 표기가 없어도 대상이 명확하면 대응시켜라. 이 기준에 대응시키기 어렵거나 모호하면 null을 유지하라. 주어진 확정 값은 변경하지 마라.
JSON {"concepts":[{"conceptId":"입력 ID","domainFacet":"분야 또는 null","category":"대상에 맞는 분류명","scaleLevel":정수 또는 null,"classificationNote":"원문 정의에 근거한 대응 이유"}]}만 반환하라."""
            response = await llm_gateway.generate_text(prompt=prompt, system_instruction=instruction + self.judgment_examples("classification", prompt),
                openai_key=openai_key, gemini_key=gemini_key, tier="tier2_reasoning",
                preferred_provider=settings.SOURCE_EXTRACTION_PROVIDER, model_override=settings.SOURCE_EXTRACTION_MODEL, reasoning_effort=settings.SOURCE_EXTRACTION_REASONING_EFFORT, allow_fallback=False,
                timeout_sec=180.0, slow_call_threshold_ms=180000.0)
            if not response:
                continue
            try:
                clean = response.strip()
                fence = chr(96) * 3
                if clean.startswith(fence):
                    clean = clean.split("\n", 1)[1].rsplit(fence, 1)[0].strip()
                proposals = json.loads(clean)["concepts"]
                if not isinstance(proposals, list):
                    raise ValueError("분류 목록 형식을 확인하지 못했습니다.")
                by_id = {item["conceptId"]: item for item in batch}
                updates = []
                for proposal in proposals:
                    item = by_id.get(proposal.get("conceptId"))
                    if item is not None:
                        classification, note = self.extraction_classification(proposal)
                        updates.append((item, classification, note))
                for item, classification, note in updates:
                    for field in ("domainFacet", "scaleLevel"):
                        if item.get(field) is None:
                            item[field] = classification[field]
                    if item.get("category") == "미분류":
                        item["category"] = classification["category"]
                    item["classificationNote"] = note or item.get("classificationNote")
            except (ValueError, KeyError, TypeError, AttributeError):
                logger.warning("분류 보완 응답을 확인하지 못했습니다. 미확정 분류를 유지합니다.")

    async def extract_perspective_parameters(self, doc, lines, concepts, source_text, openai_key=None, gemini_key=None):
        """Check application-specific parameters that the general wiki pass can omit."""
        instruction = """원문의 회사·제품·구체적 설계 조건별 사례와 공정/설계 파라미터만 추출하라.
주어진 개념 ID만 사용하라. 원문에 구체적 사례가 없으면 concepts: []를 반환하라. 단순 정의를 가상 사례로 만들지 마라.
입력의 기존 사례와 같은 적용 맥락이면 perspectiveTitle을 정확히 재사용하고 파라미터만 보강하라. 기존 사례에 없는 별도 설계 조건일 때만 새 제목을 사용하라. 파라미터가 없는 사례는 이 보완 응답에서 생략하라.
회사 공통 기술 수치에 특정 회사명을 붙이지 마라. 특정 조건의 피치·높이·적층 수·성능 등 수치가 있으면 그 조건을 제목으로 사례를 구분하라. 여러 회사의 사례는 각각 보존하라. 일정·연도는 파라미터가 아니다. 전망/예시를 실제 양산값으로 바꾸지 마라. 변경 전후 수치를 화살표나 범위로 합치지 말고 별도 specifications 항목으로 추출하라. 숫자의 쉼표도 원문 그대로 보존하라.
JSON {"concepts":[{"id":"주어진 ID","perspectiveCases":[{"perspectiveTitle":"원문 회사·제품·상황","perspectiveBadge":"원문 제품/도메인 또는 빈 문자열","narrative":"원문 적용 맥락","caution":"원문 주의사항 또는 빈 문자열","specifications":[{"parameter":"원문 파라미터명","value":"원문의 수치·범위·부등호·약/이상/이하 그대로, 단위 제외","unit":"원문 단위","safetyMargin":null,"role":null,"tradeoff":null,"rationale":null,"isConfidential":false,"fieldEvidenceLines":{"value":정수,"unit":정수,"safetyMargin":null,"role":null,"tradeoff":null,"rationale":null}}]}]}]}만 반환하라.
없는 값·단위·설명은 null로 두고, 명시된 공차·안전 마진만 safetyMargin으로 추출하라. 일반 목표치/최대치/실측치를 마진으로 바꾸거나 마진을 계산하지 마라. role/tradeoff/rationale도 원문에 설명이 있을 때만 채워라. 참고 줄 번호는 선택 사항이며 줄 번호가 없다는 이유로 원문 내용을 생략하지 마라.
보호 토큰 [RATIO_REGIME_METRIC: ...], [DIM_REGIME_SCALE: ...], [TEMP_REGIME_PEAK: ...] 등의 내부 숫자는 실제 수치가 아니다. 값에는 전체 토큰을 그대로 복사하고 원문 한정어를 보존하라. 토큰을 환산하거나 내부 숫자로 바꾸지 마라. 서버가 복원한다. 단위가 확인되지 않으면 null로 두어라. '돌파'·'약'·'이상'·'이하'도 수치 의미의 일부이며 제거하지 마라."""
        prompt = (f"- 파일경로: {doc.file_path}\n- 처리 구간: 사례·파라미터 검토\n"
                  + json.dumps([{"id": c["id"], "title": c["title"], "perspectiveCases": [
                      {"perspectiveTitle": case.get("perspectiveTitle"), "narrative": case.get("narrative")}
                      for case in c.get("perspectiveCases") or []]} for c in concepts], ensure_ascii=False)
                  + "\n[원문]\n" + "\n".join(f"{number}: {line}" for number, line in lines.items()))
        known = {c["id"] for c in concepts}
        correction = ""
        for attempt in range(2):
            response = await llm_gateway.generate_text(prompt=prompt + correction, system_instruction=instruction + self.judgment_examples("parameters", "\n".join(lines.values())),
                openai_key=openai_key, gemini_key=gemini_key, tier="tier2_reasoning",
                preferred_provider=settings.SOURCE_EXTRACTION_PROVIDER, model_override=settings.SOURCE_EXTRACTION_MODEL, reasoning_effort=settings.SOURCE_EXTRACTION_REASONING_EFFORT, allow_fallback=False,
                timeout_sec=180.0, slow_call_threshold_ms=180000.0)
            if not response:
                continue
            try:
                clean = response.strip()
                fence = chr(96) * 3
                if clean.startswith(fence):
                    clean = clean.split("\n", 1)[1].rsplit(fence, 1)[0].strip()
                values = json.loads(clean)["concepts"]
                if not isinstance(values, list):
                    raise ValueError("사례 목록 형식 확인 필요")
                result = []
                for value in values:
                    if value["id"] not in known:
                        raise ValueError("원문 개념 목록에 없는 사례 대상")
                    resolved = self.resolve_quote_lines(value, lines)
                    resolved["perspectiveCases"] = [case for case in resolved.get("perspectiveCases") or [] if case.get("specifications")]
                    checked = self.validate_quotes(resolved, source_text)
                    if attempt == 0 and any(warning.startswith("사례 파라미터") for warning in checked["validationWarnings"]):
                        raise ValueError("파라미터 형식 확인 필요")
                    # Keep raw proposals so the shared preview validator shows withheld fields and reasons.
                    result.append({"id": value["id"], "perspectiveCases": [raw for raw, validated in
                        zip(resolved["perspectiveCases"], checked["perspectiveCases"]) if validated["specifications"]]})
                    prior_cases = next(c for c in concepts if c["id"] == value["id"]).get("perspectiveCases") or []
                    for case in result[-1]["perspectiveCases"]:
                        prior = next((old for old in prior_cases if old.get("perspectiveTitle") == case.get("perspectiveTitle")), None)
                        if prior and prior.get("narrative") and prior.get("evidenceQuote"):
                            case.update({key: prior.get(key) for key in ("narrative", "caution", "evidenceQuote")})
                return result
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                correction = f"\n[정정 요청] {error}. 원문에 없는 값은 null로 두고 형식에 맞는 전체 JSON을 다시 반환하라. 이전 응답:\n{response}"
                continue
        raise RuntimeError("사례·파라미터 원문 검토를 완료하지 못했습니다. 문서를 다시 추출해주세요.")

    async def review_relation_subjects(self, doc, items, source_text, openai_key=None, gemini_key=None, registered_concepts=None):
        """Review source/target ownership separately from the document's main topic."""
        fields = ("previousSteps", "nextSteps", "alternatives", "partOf", "isA")
        candidates = [(item, field, deepcopy(link)) for item in items for field in fields
                      for link in item.get(field) or [] if link.get("evidenceVerified")]
        if not candidates:
            return
        lines = {number: line for number, line in enumerate(source_text.splitlines(), 1) if line.strip()}
        subjects = {item["conceptId"]: item for item in items}
        identity_names = {c.id: [c.title, c.eng_name, *(c.aliases or [])] for c in registered_concepts or []}
        for cid, item in subjects.items():
            identity_names.setdefault(cid, [item["title"], item.get("engName")])
        for _, field, link in candidates:
            key = "targetId" if field == "alternatives" else "id"
            link[key] = concept_repo.resolve_reference_id(link.get(key), link.get("name") or link.get("targetName"), registered_concepts or [])
            target_name = link.get("name") or link.get("targetName")
            if isinstance(link[key], str) and link[key].strip() and target_name:
                identity_names.setdefault(link[key], [target_name])
        names = {cid: values[0] for cid, values in identity_names.items()}
        instruction = """원문의 관계 후보를 모두 검토하라. 인용문이 존재한다는 사실과 관계를 뒷받침한다는 사실은 다르다.
ownerId는 관계 배열을 소유할 개념이다. previousSteps는 ownerId가 후행 공정이고 targetId가 선행 공정이다. nextSteps는 ownerId가 선행 공정이고 targetId가 후행 공정이다. previousSteps를 정방향 그래프 표기로 바꾸어 두 ID를 뒤집지 마라. 교육 시리즈의 지난 편/다음 편 소개만으로 물리적 공정 순서를 인정하지 마라. 같은 문장에 실제 전후 공정 설명도 있으면 그 설명을 기준으로 판단하라.
alternatives는 동일한 구체적 목적에 대해 선택 가능한 동급 기술·방식의 비교이다. 상위 공정과 하위 방식, 선행과 후속 공정을 대안으로 인정하지 마라. 문서 안의 다른 두 기술 비교를 대표 개념에 붙이지 마라. 비교 주체는 문서 전체의 주제와 다를 수 있으므로 실제 비교되는 방식끼리만 연결하라.
isA는 주체가 대상의 한 종류라는 원문 분류 관계이다. 평가 기준·성능 지표·응용 분야·도입 목적은 종류가 아니다.
partOf는 주체가 대상 내부의 실제 구성요소라는 관계이다. 공정이 장비를 사용하거나 소자끼리 외부 연결·호환·함께 사용되는 것은 소속이 아니다.
각 관계 유형을 별도로 검토하라. 다른 유형의 관계로 보이더라도 지금 후보의 유형을 억지로 인정하거나 바꾸지 말고 supported:false로 보류하라.
각 후보의 관계 설명과 유형이 원문에 맞는지 판단하라. 잘못된 주체·대상만 확인되면 원문 개념 목록의 정확한 ID로 정정하되 관계 유형은 바꾸지 마라. 설명 자체가 원문에서 뒷받침되지 않으면 supported:false로 보류하라. 같은 후보를 누락하거나 중복하지 말고 모두 평가하라.
JSON {"decisions":[{"candidateIndex":0,"supported":true,"ownerId":"관계 배열을 소유할 개념 ID","targetId":"제공된 대상 ID","reason":"원문 맥락에 따른 검토 사유"},{"candidateIndex":1,"supported":false,"reason":"보류 사유"}]}만 반환하라. 문서 전체의 소제목·앞뒤 문장과 별칭을 함께 해석하라. 같은 줄에 두 명칭이 없거나 표현이 다르다는 이유로 보류하지 마라. 원문이 실제로 설명하는 관계인지 의미로 판단하라."""
        prompt = (f"- 파일경로: {doc.file_path}\n- 처리 구간: 관계 주체·대상 검토\n"
                  + json.dumps({"concepts": [{"id": cid, "title": item["title"]} for cid, item in subjects.items()],
                    "candidates": [{"candidateIndex": i, "ownerId": item["conceptId"], "field": field, **link}
                                   for i, (item, field, link) in enumerate(candidates)]}, ensure_ascii=False)
                  + "\n[원문]\n" + "\n".join(f"{number}: {line}" for number, line in lines.items()))
        correction = ""
        for attempt in range(2):
            response = await llm_gateway.generate_text(prompt=prompt + correction, system_instruction=instruction + self.judgment_examples("relations", source_text),
                openai_key=openai_key, gemini_key=gemini_key, tier="tier2_reasoning",
                preferred_provider=settings.SOURCE_EXTRACTION_PROVIDER, model_override=settings.SOURCE_EXTRACTION_MODEL, reasoning_effort=settings.SOURCE_EXTRACTION_REASONING_EFFORT, allow_fallback=False, timeout_sec=180.0, slow_call_threshold_ms=180000.0)
            if not response:
                continue
            try:
                clean = response.strip()
                fence = chr(96) * 3
                if clean.startswith(fence):
                    clean = clean.split("\n", 1)[1].rsplit(fence, 1)[0].strip()
                decisions = json.loads(clean)["decisions"]
                if len(decisions) != len(candidates) or {d["candidateIndex"] for d in decisions} != set(range(len(candidates))):
                    raise ValueError("모든 관계 후보를 중복 없이 평가해야 합니다")
                reviewed = []
                corrections = []
                for decision in decisions:
                    owner, field, link = candidates[decision["candidateIndex"]]
                    if not isinstance(decision.get("supported"), bool):
                        raise ValueError("supported는 boolean이어야 합니다")
                    if not decision["supported"]:
                        reviewed.append((owner, field, None, decision.get("reason") or "원문 관계 확인 필요"))
                        continue
                    cid, target = decision["ownerId"], decision["targetId"]
                    if not isinstance(target, str) or not target.strip() or cid not in subjects or target not in names or cid == target:
                        if attempt == 0:
                            raise ValueError("원문 관계 개념 ID 확인 필요. 모호한 관계는 supported:false로 보류하세요")
                        reviewed.append((owner, field, None, "관계 주체·대상 ID 확인 필요"))
                        continue
                    value = deepcopy(link)
                    value["targetId" if field == "alternatives" else "id"] = target
                    value["targetName" if field == "alternatives" else "name"] = names[target]
                    checked = self.validate_quotes({field: [value]}, source_text)[field][0]
                    reviewed.append((subjects[cid], field, checked, None))
                    original_target = link.get("id") or link.get("targetId")
                    if cid != owner["conceptId"] or target != original_target:
                        corrections.append((owner, {"field": field, "targetId": original_target,
                            "targetName": link.get("name") or link.get("targetName"),
                            "correctedOwnerId": cid, "correctedTargetId": target}))
                for item in items:
                    for field in fields:
                        item[field] = []
                for item, field, link, warning in reviewed:
                    if link is None:
                        item.setdefault("validationWarnings", []).append(f"{field}: 관계 원문 재검토 보류 — {warning}")
                    else:
                        item[field].append(link)
                for owner, correction in corrections:
                    owner.setdefault("relationCorrections", []).append(correction)
                return
            except (ValueError, KeyError, TypeError, IndexError) as error:
                correction = f"\n[정정 요청] {error}. 모든 후보와 원문 맥락을 다시 확인하라. 이전 응답:\n{response}"
        raise RuntimeError("관계 주체·대상 검토를 완료하지 못했습니다. 문서를 다시 추출해주세요.")

    async def review_perspective_cases(self, doc, items, source_text, openai_key=None, gemini_key=None):
        """Verify only new source candidates, without reinterpreting stored wiki knowledge."""
        candidates = [(item, case) for item in items for case in item["perspectiveCases"] if case.get("evidenceVerified")]
        if not candidates:
            return
        lines = {number: line for number, line in enumerate(source_text.splitlines(), 1) if line.strip()}
        instruction = """현재 원문에서 추출된 사례와 각 수치의 귀속을 모두 검토하라. 기존 위키 지식은 검토 대상이 아니다.
사례의 회사·제품·상황, 제목, narrative와 caution이 원문과 일치해야 supported:true이다. 발행처 이름만으로 적용 회사를 만들지 마라. 전망/로드맵/설명용 예시를 실제 양산 실적으로 만들지 마라.
각 specifications는 같은 회사·제품·설계 조건에 대한 값인지 따로 판단하라. 일반 기술의 수치를 인접한 특정 회사 사례에 붙이거나, 다른 세대·조건의 수치를 섞으면 해당 spec만 supported:false이다. 다른 사양이 틀렸다는 이유로 맞는 사례 설명을 버리지 마라.
숫자·단위가 인용문에 있다는 것만으로는 충분하지 않다. 파라미터명과 값의 의미, 조건, 주체까지 맞아야 한다. 웹 메뉴·푸터·메시지 식별자·서지 연도는 실제 측정값이나 레시피가 아니다. 목표/개선율/실측치를 안전 마진으로 인정하지 마라. 약/이상/이하/돌파 등 한정어를 잃은 값도 보류하라.
제목이나 설명의 표현이 원문 명칭과 다르다는 이유만으로 거부하지 말고 의미와 조건이 일치하는지 판단하라. 회사/제품 맥락은 앞 소제목에 있고 실제 값은 뒤 문장에 있을 수 있으므로 같은 줄만 강요하지 말고 문서 구조로 귀속을 확인하라. 모호하면 supported:false로 보류하고 원문에 없는 설명을 고쳐 쓰거나 새 수치를 만들지 마라.
모든 caseIndex와 각 specIndex를 빠짐없이 중복 없이 평가한다. JSON {"decisions":[{"caseIndex":0,"supported":true,"reason":"판정 이유","specifications":[{"specIndex":0,"supported":true,"reason":"그 조건의 실제 값임"}]}]}만 반환하라. supported:false에도 reason을 쓰고 모든 spec을 평가하라."""
        prompt = (f"- 파일경로: {doc.file_path}\n- 처리 구간: 사례·수치 귀속 검토\n"
                  + json.dumps([{"caseIndex":i,"conceptId":item["conceptId"],"conceptTitle":item["title"],
                      **case, "specifications":[{"specIndex":j,**spec} for j,spec in enumerate(case.get("specifications") or [])]}
                      for i,(item,case) in enumerate(candidates)],ensure_ascii=False)
                  + "\n[현재 원문]\n" + "\n".join(f"{number}: {line}" for number,line in lines.items()))
        def check_indices(values, key, count):
            if not isinstance(values,list) or len(values)!=count or any(type(v.get(key)) is not int for v in values) or {v[key] for v in values}!=set(range(count)):
                raise ValueError("모든 사례와 사양을 중복 없이 평가해야 합니다")
        correction=""
        for attempt in range(2):
            response=await llm_gateway.generate_text(prompt=prompt+correction,system_instruction=instruction,
                openai_key=openai_key,gemini_key=gemini_key,tier="tier2_reasoning",
                preferred_provider=settings.SOURCE_EXTRACTION_PROVIDER, model_override=settings.SOURCE_EXTRACTION_MODEL, reasoning_effort=settings.SOURCE_EXTRACTION_REASONING_EFFORT, allow_fallback=False,timeout_sec=180.0,slow_call_threshold_ms=180000.0)
            if not response:
                continue
            try:
                clean=response.strip()
                fence=chr(96)*3
                if clean.startswith(fence):
                    clean=clean.split("\n",1)[1].rsplit(fence,1)[0].strip()
                decisions=json.loads(clean)["decisions"]
                check_indices(decisions,"caseIndex",len(candidates))
                accepted=[]
                warnings=[]
                for decision in decisions:
                    item,case=candidates[decision["caseIndex"]]
                    specs=case.get("specifications") or []
                    reviews=decision["specifications"]
                    check_indices(reviews,"specIndex",len(specs))
                    for review in [decision,*reviews]:
                        if type(review.get("supported")) is not bool or not (review.get("reason") or "").strip():
                            raise ValueError("각 판정의 supported와 reason이 필요합니다")
                    if not decision["supported"]:
                        warnings.append((item,f"적용 사례 '{case['perspectiveTitle']}': 원문 귀속 확인 보류 — {decision['reason']}"))
                        continue
                    value=deepcopy(case)
                    value["specifications"]=[]
                    for review in reviews:
                        spec=deepcopy(specs[review["specIndex"]])
                        if not review["supported"]:
                            warnings.append((item,f"사례 파라미터 '{spec['parameter']}': 회사·제품·상황 귀속 검토 보류 — {review['reason']}"))
                            continue
                        value["specifications"].append(spec)
                    accepted.append((item,value))
                for item in items:
                    item["perspectiveCases"]=[]
                for item,case in accepted:
                    item["perspectiveCases"].append(case)
                for item,warning in warnings:
                    item.setdefault("validationWarnings",[]).append(warning)
                return
            except (ValueError,KeyError,TypeError,AttributeError,IndexError) as error:
                correction=f"\n[정정 요청] {error}. 모든 후보와 원문 맥락을 다시 확인하라. 이전 응답:\n{response}"
        raise RuntimeError("사례·수치 귀속 검토를 완료하지 못했습니다. 문서를 다시 추출해주세요.")

    async def extract_single_document(
        self, doc: SourceDocumentModel, openai_key: Optional[str] = None, gemini_key: Optional[str] = None,
        registered_concepts: Optional[List[ConceptModel]] = None
    ) -> List[ExtractedConceptDiffDTO]:
        """Publish a preview only after every source part has been processed successfully."""
        file_path = source_repo.resolve_safe_file_path(doc)
        source_hash = source_repo.compute_file_hash(file_path)
        raw_text = file_path.read_text(encoding="utf-8")
        doc.file_hash = source_hash
        cleaned_text = self.clean_web_noise(raw_text)
        if not cleaned_text.strip():
            raise RuntimeError("정제 후 분석할 원문이 없습니다.")
        _, _, source_url = source_repo.extract_title_and_metadata(file_path)
        parts = self.document_parts(cleaned_text)
        catalog = list(registered_concepts or [])
        extracted = {}
        for number, (start, end) in enumerate(parts, start=1):
            lines = {index: line for index, line in enumerate(cleaned_text[max(0, start - 400):end].splitlines(), start=1) if line.strip()}
            numbered_text = "\n".join(f"{index}: {line}" for index, line in lines.items())
            catalog_json = [{"id": c.id, "title": c.title, "engName": c.eng_name, "aliases": c.aliases} for c in catalog]
            user_prompt = f"""[기존 등록·앞 구간 추출 개념 (동일한 개념이면 ID 재사용)]
{json.dumps(catalog_json, ensure_ascii=False)}

[문서 메타데이터]
- 출처사: {doc.publisher}
- 문서명: {doc.title}
- 파일경로: {doc.file_path}
- 처리 구간: {number}/{len(parts)}, 문자 {start}~{end}, 전체 {len(cleaned_text)}자

[원문 텍스트 (직전 400자 연결 문맥 포함)]:
{numbered_text}

이번 원문 구간 전체에서 기술 개념·정의·원리·한계와 명시된 정량 조건·관계를 추출하라. 지식이 없는 구간만 concepts: []로 반환하라.
관계나 목적이 없는 용어도 정의에 딸린 정량 조건과 수식 변수의 값은 해당 개요·원리·한계에 함께 보존하라. 없는 필드는 꾸며내지 마라."""
            payload = None
            correction = ""
            for attempt in range(2):
                response = await llm_gateway.generate_text(
                    prompt=user_prompt + correction, system_instruction=self.build_publisher_prompt(doc.publisher) + self.judgment_examples("extract", numbered_text),
                    openai_key=openai_key, gemini_key=gemini_key, tier="tier2_reasoning",
                    preferred_provider=settings.SOURCE_EXTRACTION_PROVIDER, model_override=settings.SOURCE_EXTRACTION_MODEL, reasoning_effort=settings.SOURCE_EXTRACTION_REASONING_EFFORT, allow_fallback=False,
                    timeout_sec=180.0, slow_call_threshold_ms=180000.0
                )
                if not response:
                    continue
                try:
                    clean = response.strip()
                    fence = chr(96) * 3
                    if clean.startswith(fence):
                        clean = clean.split("\n", 1)[1].rsplit(fence, 1)[0].strip()
                    candidate = json.loads(clean)
                    if not isinstance(candidate, dict) or not isinstance(candidate.get("concepts"), list):
                        raise ValueError("concepts 배열이 없습니다.")
                    invalid = []
                    candidate["concepts"] = [self.resolve_quote_lines(value, lines) for value in candidate["concepts"]]
                    for value in candidate["concepts"]:
                        checked = self.validate_quotes(value, raw_text)
                        label = value.get("title") or value.get("id") or "개념"
                        if not value.get("summary") and not any(c.id == value.get("id") for c in catalog):
                            invalid.append(f"{label}/새 개념의 정의 필요. 원문에 정의가 없으면 관계 대상으로만 참조")
                        for case, checked_case in zip(value.get("perspectiveCases") or [], checked["perspectiveCases"]):
                            specs, checked_specs = case.get("specifications") or [], checked_case["specifications"]
                            if len(specs) != len(checked_specs) or any(
                                    original.get(key) is not None and validated.get(key) is None
                                    for original, validated in zip(specs, checked_specs)
                                    for key in ("value", "unit", "safetyMargin", "role", "tradeoff", "rationale")):
                                invalid.append(f"{label}/사례 파라미터")
                    if invalid and attempt == 0:
                        correction = "\n[형식 정정 요청]\n" + ", ".join(invalid) + "를 확인하고 원문에 있는 정의와 파라미터를 형식에 맞게 반환하라. 이전 응답:\n" + response
                        continue
                    payload = candidate
                    break
                except (ValueError, IndexError):
                    continue
            if payload is None:
                raise RuntimeError(f"원문 {number}/{len(parts)} 구간의 구조화 응답을 확인하지 못했습니다. 전체 문서를 완료 처리하지 않습니다.")
            subjects = {cid: {"id": cid, "title": value["title"], "perspectiveCases": value["perspectiveCases"]} for cid, value in extracted.items()}
            for value in payload["concepts"]:
                if value.get("id"):
                    previous = subjects.get(value["id"], {})
                    subjects[value["id"]] = {**value, "perspectiveCases": [*(previous.get("perspectiveCases") or []), *(value.get("perspectiveCases") or [])]}
            if subjects:
                supplements = await self.extract_perspective_parameters(doc, lines, list(subjects.values()), raw_text, openai_key, gemini_key)
                for supplement in supplements:
                    subject = next((c for c in payload["concepts"] if c.get("id") == supplement["id"]), None)
                    if subject is None:
                        subject = {**subjects[supplement["id"]], "perspectiveCases": []}
                        payload["concepts"].append(subject)
                    for case in supplement["perspectiveCases"]:
                        match = next((c for c in subject.setdefault("perspectiveCases", []) if c.get("perspectiveTitle") == case.get("perspectiveTitle")), None)
                        if match is None:
                            subject["perspectiveCases"].append(case)
                        else:
                            for spec in case["specifications"]:
                                if spec not in match.setdefault("specifications", []):
                                    match["specifications"].append(spec)
            for c in payload["concepts"]:
                if not isinstance(c, dict) or not (c.get("title") or "").strip():
                    raise ValueError(f"원문 {number} 구간에 개념명이 없는 추출 결과가 있습니다.")
                raw_id = (c.get("id") or "").strip().lower()
                cid = ID_ALIASES.get(raw_id, raw_id)
                if not cid:
                    cid = re.sub(r"[^a-zA-Z0-9]+", "-", (c.get("engName") or "").lower()).strip("-")
                if not cid:
                    cid = "concept-" + hashlib.sha256(c["title"].encode()).hexdigest()[:16]
                cid = concept_repo.resolve_reference_id(cid, c["title"], catalog)
                classification, classification_note = self.extraction_classification(c)
                item = self.normalize_concept(self.validate_quotes({
                    **c, "conceptId": cid, "engName": c.get("engName") or c["title"],
                    **classification, "classificationNote": classification_note, "summary": c.get("summary") or "",
                    "purpose": c.get("purpose") or "", "sourceDocumentTitle": doc.title, "sourceUrl": source_url
                }, raw_text), doc.doc_id)
                item["classificationProposals"] = [{**classification, "classificationNote": classification_note}]
                old = extracted.get(cid)
                if old is None:
                    extracted[cid] = item
                    catalog.append(SimpleNamespace(id=cid, title=item["title"], eng_name=item["engName"], aliases=[]))
                else:
                    old["validationWarnings"] = list(dict.fromkeys([*old.get("validationWarnings", []), *item.get("validationWarnings", [])]))
                    for field in ("summary", "purpose"):
                        if item.get(field) and item.get(f"{field}EvidenceVerified"):
                            if not old.get(f"{field}EvidenceVerified"):
                                old[field] = ""
                                old[f"{field}EvidenceQuotes"] = []
                            paragraphs = old[field].split("\n\n") if old[field] else []
                            if item[field] not in paragraphs:
                                paragraphs.append(item[field])
                            quotes = old.get(f"{field}EvidenceQuotes") or ([old.get(f"{field}EvidenceQuote")] if old.get(f"{field}EvidenceVerified") else [])
                            old[field] = "\n\n".join(paragraphs)
                            old[f"{field}EvidenceQuotes"] = list(dict.fromkeys(quote for quote in
                                [*quotes, item.get(f"{field}EvidenceQuote")] if isinstance(quote, str) and quote.strip()))
                            old[f"{field}EvidenceVerified"] = True
                    for field in ("principles", "limitations", "perspectiveCases", "previousSteps", "nextSteps", "alternatives", "partOf", "isA"):
                        for value in item[field]:
                            if field == "perspectiveCases":
                                prior = next((case for case in old[field] if case.get("perspectiveTitle") == value.get("perspectiveTitle") and case.get("narrative") == value.get("narrative") and case.get("caution") == value.get("caution")), None)
                                if prior:
                                    for spec in value["specifications"]:
                                        if spec not in prior["specifications"]:
                                            prior["specifications"].append(spec)
                                    continue
                            if value not in old[field]:
                                old[field].append(value)
                    for proposal in item["classificationProposals"]:
                        if not any(all(prior.get(key) == proposal.get(key) for key in ("domainFacet", "category", "scaleLevel"))
                                   for prior in old["classificationProposals"]):
                            old["classificationProposals"].append(proposal)
                    conflicts = old.setdefault("_classificationConflicts", set())
                    for field in ("domainFacet", "category", "scaleLevel"):
                        if field in conflicts:
                            continue
                        if not old.get(field) or old[field] == "미분류":
                            old[field] = item.get(field)
                        elif item.get(field) and item[field] != "미분류" and old[field] != item[field]:
                            conflicts.add(field)
                            old["classificationConflict"] = True
                            old[field] = "미분류" if field == "category" else None
                            old["classificationNote"] = "원문 구간별 분류안이 다릅니다. 관리자 확인이 필요합니다."
        if source_repo.compute_file_hash(file_path) != source_hash:
            raise RuntimeError("추출 중 원문이 변경되었습니다. 다시 추출해주세요.")
        if not extracted:
            raise RuntimeError("원문 전체를 처리했지만 위키에 반영할 개념을 추출하지 못했습니다.")
        await self.complete_classifications(doc, list(extracted.values()), openai_key, gemini_key)
        for item in extracted.values():
            proposal = {**ConceptClassificationDTO(**item).model_dump(by_alias=True), "classificationNote": item.get("classificationNote")}
            if not any(all(prior.get(key) == proposal.get(key) for key in ("domainFacet", "category", "scaleLevel")) for prior in item["classificationProposals"]):
                item["classificationProposals"].append(proposal)
        await self.review_relation_subjects(doc, list(extracted.values()), cleaned_text, openai_key, gemini_key, registered_concepts)
        await self.review_perspective_cases(doc, list(extracted.values()), cleaned_text, openai_key, gemini_key)
        extracted = {cid: self.normalize_concept(item, doc.doc_id) for cid, item in extracted.items()}
        coverage = {"complete": True, "totalParts": len(parts), "processedParts": len(parts),
                    "totalCharacters": len(cleaned_text), "processedCharacters": sum(end - start for start, end in parts),
                    "sourceHash": source_hash}
        return [ExtractedConceptDiffDTO(**{**item, "sourceCoverage": coverage}) for item in extracted.values()]

    async def stream_sequential_extraction(
        self, session: AsyncSession, doc_ids: List[str], force_reextract: bool = False,
        openai_key: Optional[str] = None, gemini_key: Optional[str] = None,
        preserved_doc_ids: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """Execute extraction sequentially one-by-one with SSE streaming events."""
        # 1. Acquire concurrency lock
        acquired = await self.lock_mgr.acquire(doc_ids)
        if not acquired:
            yield f"event: error\ndata: {json.dumps({'message': '이미 다른 추출 작업이 실행 중입니다. 완료 후 다시 시도하세요.'}, ensure_ascii=False)}\n\n"
            return

        total_docs = len(doc_ids)
        results: List[DocumentExtractionResultDTO] = []
        all_extracted_diffs: List[ExtractedConceptDiffDTO] = []

        try:
            yield f"event: start\ndata: {json.dumps({'total': total_docs, 'docIds': doc_ids}, ensure_ascii=False)}\n\n"

            # Check existing concepts in DB to mark isNew
            registered_concepts = await concept_repo.get_all_concepts(session)
            existing_by_id = {c.id: c for c in registered_concepts}
            existing_cids = set(existing_by_id)

            for idx, did in enumerate(doc_ids, start=1):
                doc = await source_repo.get_by_doc_id(session, did)
                if not doc:
                    results.append(DocumentExtractionResultDTO(
                        docId=did, filePath="", title=did, status="failed", succeeded=False,
                        errorMessage="문서를 찾을 수 없습니다."
                    ))
                    yield f"event: doc_error\ndata: {json.dumps({'current': idx, 'total': total_docs, 'docId': did, 'message': '문서를 찾을 수 없습니다.'}, ensure_ascii=False)}\n\n"
                    continue

                if did in (preserved_doc_ids or []):
                    preserved = [ExtractedConceptDiffDTO(**raw) for raw in doc.last_preview_payload or []]
                    all_extracted_diffs.extend(preserved)
                    for cd in preserved:
                        if not any(c.id == cd.concept_id for c in registered_concepts):
                            registered_concepts.append(SimpleNamespace(id=cd.concept_id, title=cd.title, eng_name=cd.eng_name, aliases=[]))
                    results.append(DocumentExtractionResultDTO(docId=did, filePath=doc.file_path, title=doc.title,
                        status="success", succeeded=True, extractedConcepts=preserved))
                    yield f"event: doc_success\ndata: {json.dumps({'current': idx, 'total': total_docs, 'docId': did, 'title': doc.title, 'conceptsCount': len(preserved), 'preserved': True}, ensure_ascii=False)}\n\n"
                    continue

                if doc.last_succeeded_at and not force_reextract:
                    results.append(DocumentExtractionResultDTO(
                        docId=did, filePath=doc.file_path, title=doc.title,
                        status="skipped", succeeded=False
                    ))
                    yield f"event: doc_skipped\ndata: {json.dumps({'current': idx, 'total': total_docs, 'docId': did, 'title': doc.title}, ensure_ascii=False)}\n\n"
                    continue

                # Mark attempt running
                await source_repo.update_attempt(session, did, status="running")

                yield f"event: progress\ndata: {json.dumps({'current': idx, 'total': total_docs, 'docId': did, 'title': doc.title, 'publisher': doc.publisher, 'step': '분석 중...'}, ensure_ascii=False)}\n\n"

                try:
                    history = {raw["conceptId"]: self.case_history(doc, raw) for raw in doc.last_preview_payload or []}
                    relation_history = {concept_repo.resolve_reference_id(raw["conceptId"], raw.get("title"), registered_concepts):
                        self.relation_history(doc, raw) for raw in doc.last_preview_payload or []}
                    # Run extraction
                    concepts_diff = await self.extract_single_document(doc, openai_key=openai_key, gemini_key=gemini_key,
                                                                      registered_concepts=registered_concepts)

                    # Mark isNew
                    for cd in concepts_diff:
                        cd.is_new = (cd.concept_id not in existing_cids)
                        existing = existing_by_id.get(cd.concept_id)
                        if existing:
                            cd.existing_classification = ConceptClassificationDTO(
                                domainFacet=existing.domain_facet, category=existing.process_category, scaleLevel=existing.scale_level)
                        if not any(c.id == cd.concept_id for c in registered_concepts):
                            registered_concepts.append(SimpleNamespace(id=cd.concept_id, title=cd.title, eng_name=cd.eng_name, aliases=[]))

                    all_extracted_diffs.extend(concepts_diff)

                    # Count relations
                    total_rels = sum(
                        len(c.previous_steps) + len(c.next_steps) + len(c.alternatives) + len(c.part_of) + len(c.is_a)
                        for c in concepts_diff
                    )

                    # Save preview payload and success status
                    preview_json = [{**c.model_dump(by_alias=True), "_appliedCases": history.get(c.concept_id, {}),
                                     "_appliedRelations": relation_history.get(c.concept_id, {})} for c in concepts_diff]
                    await source_repo.update_success(
                        session=session,
                        doc_id=did,
                        current_hash=doc.file_hash,
                        concepts_count=len(concepts_diff),
                        relations_count=total_rels,
                        preview_payload=preview_json
                    )

                    doc_res = DocumentExtractionResultDTO(
                        docId=did,
                        filePath=doc.file_path,
                        title=doc.title,
                        status="success",
                        succeeded=True,
                        extractedConcepts=concepts_diff
                    )
                    results.append(doc_res)

                    yield f"event: doc_success\ndata: {json.dumps({'current': idx, 'total': total_docs, 'docId': did, 'title': doc.title, 'conceptsCount': len(concepts_diff), 'relationsCount': total_rels}, ensure_ascii=False)}\n\n"

                except Exception as e:
                    err_msg = str(e)
                    logger.error(f"Extraction failed for {did}: {err_msg}", exc_info=True)
                    await source_repo.update_attempt(session, did, status="failed", error_message=err_msg)
                    doc_res = DocumentExtractionResultDTO(
                        docId=did,
                        filePath=doc.file_path,
                        title=doc.title,
                        status="failed",
                        succeeded=False,
                        errorMessage=err_msg
                    )
                    results.append(doc_res)
                    yield f"event: doc_error\ndata: {json.dumps({'current': idx, 'total': total_docs, 'docId': did, 'title': doc.title, 'errorMessage': err_msg}, ensure_ascii=False)}\n\n"

            # Final finished event with aggregated concepts for Preview Modal
            prepared = []
            states = {}
            for result in results:
                if result.succeeded:
                    doc = await source_repo.get_by_doc_id(session, result.doc_id)
                    prepared.extend(await self.prepare_preview(session, doc, doc.last_preview_payload, states))
            for item in prepared:
                self.check_completion(item)
            finished_payload = {
                "totalProcessed": total_docs,
                "totalSucceeded": sum(1 for r in results if r.succeeded),
                "totalFailed": sum(1 for r in results if r.status == "failed"),
                "totalSkipped": sum(1 for r in results if r.status == "skipped"),
                "aggregatedConcepts": [ExtractedConceptDiffDTO(**item).model_dump(by_alias=True) for item in prepared],
                "results": [r.dict(by_alias=True) for r in results]
            }
            yield f"event: finished\ndata: {json.dumps(finished_payload, ensure_ascii=False)}\n\n"

        finally:
            await self.lock_mgr.release(doc_ids)

    async def apply_extractions_to_wiki(
        self, session: AsyncSession, doc_ids: List[str],
        expected_versions: Optional[Dict[str, str]] = None,
        reviewed_by: Optional[str] = None,
        concept_metadata: Optional[Dict[str, ConceptClassificationDTO]] = None
    ) -> ApplyExtractionResponseDTO:
        """Approve classifications and supported links in the same transaction as the wiki content."""
        updated_cids: Set[str] = set()
        updated_evidence_ids: Set[str] = set()
        overrides = concept_metadata or {}
        applied_count = 0
        try:
            catalog = await concept_repo.get_all_concepts(session)
            pending = []
            states = {}
            classifications = {}
            requested_ids = set()
            for did in dict.fromkeys(doc_ids):
                doc = await source_repo.get_by_doc_id(session, did)
                if not doc:
                    raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
                if doc.is_applied:
                    continue
                if doc.attempt_status != "success" or not doc.last_preview_payload:
                    raise HTTPException(status_code=409, detail="적용 가능한 추출 결과가 없습니다. 미리보기를 다시 확인해주세요.")
                file_path = source_repo.resolve_safe_file_path(doc)
                if doc.last_succeeded_hash and source_repo.compute_file_hash(file_path) != doc.last_succeeded_hash:
                    raise HTTPException(status_code=409, detail="추출 이후 원문이 변경되었습니다. 다시 추출해주세요.")
                items = await self.prepare_preview(session, doc, doc.last_preview_payload, states)
                for raw, item in zip(doc.last_preview_payload, items):
                    original_id = raw["conceptId"]
                    cid = item["conceptId"]
                    requested_ids.update((original_id, cid))
                    candidates = [overrides[key] for key in dict.fromkeys((original_id, cid)) if key in overrides]
                    if len(candidates) > 1 and candidates[0] != candidates[1]:
                        raise HTTPException(status_code=409, detail=f"{item['title']}: 같은 개념의 분류 정정안이 다릅니다.")
                    if not candidates and item["isNew"] and item.get("classificationConflict"):
                        raise HTTPException(status_code=409, detail=f"{item['title']}: 원문 구간별 분류안을 미리보기에서 확정해주세요.")
                    classification = next(iter(candidates), None) or ConceptClassificationDTO(**item)
                    if not isinstance(classification, ConceptClassificationDTO):
                        classification = ConceptClassificationDTO(**classification)
                    if classification.domain_facet is None or classification.scale_level is None:
                        raise HTTPException(status_code=409, detail=f"{item['title']}: 분야와 규모를 미리보기에서 확인하거나 다시 추출해주세요.")
                    signature = (classification.domain_facet, classification.category, classification.scale_level)
                    if cid in classifications and classifications[cid] != signature:
                        raise HTTPException(status_code=409, detail=f"{item['title']}: 문서별 분류안이 다릅니다. 미리보기에서 분류를 통일해주세요.")
                    classifications[cid] = signature
                    item.update(classification.model_dump(by_alias=True))
                pending.append((doc, items))
            if set(overrides) - requested_ids and pending:
                raise HTTPException(status_code=400, detail="선택한 문서에 없는 개념의 분류를 변경할 수 없습니다.")
            for _, items in pending:
                for item in items:
                    self.check_completion(item)
                    if item["applyBlockers"]:
                        raise HTTPException(status_code=409, detail=f"{item['title']}: {' '.join(item['applyBlockers'])}")

            for doc, items in pending:
                did = doc.doc_id
                for item in items:
                    cid = item["conceptId"]
                    existing = await session.get(ConceptModel, cid)
                    if existing and expected_versions and cid in expected_versions and existing.version != expected_versions[cid]:
                        raise HTTPException(status_code=409, detail=f"{cid}의 내용이 변경되었습니다. 미리보기를 다시 확인해주세요.")
                    merged = item["mergedPreview"]
                    if existing:
                        existing.updated_at = datetime.utcnow()
                        concept = existing
                    else:
                        concept = ConceptModel(
                            id=cid, title=item["title"], eng_name=item["engName"], aliases=[item["title"]],
                            version="v2.1", status="adopted", last_reviewed_at=datetime.utcnow(), last_reviewed_by=reviewed_by,
                            summary=merged["summary"], purpose=merged["purpose"],
                            principles=merged["principles"], limitations=merged["limitations"], relations={})
                        session.add(concept)
                    concept.summary = merged["summary"]
                    concept.purpose = merged["purpose"]
                    concept.principles = deepcopy(merged["principles"])
                    concept.limitations = deepcopy(merged["limitations"])
                    concept.domain_facet = item["domainFacet"]
                    concept.process_category = item["category"]
                    concept.scale_level = item["scaleLevel"]
                    concept.scale_name = f"Scale {item['scaleLevel']}"

                    relations = deepcopy(concept.relations or {})
                    for key, field in [("previous_step", "previousSteps"), ("next_step", "nextSteps"),
                                       ("alternative_to", "alternatives"), ("part_of", "partOf"), ("is_a", "isA")]:
                        relations[key] = deepcopy(merged[field])
                    concept.relations = relations

                    quotes = set()
                    if item.get("evidenceVerified"):
                        quotes.add(item.get("evidenceQuote"))
                    for field in ("summary", "purpose"):
                        if item.get(f"{field}EvidenceVerified"):
                            quotes.update(item.get(f"{field}EvidenceQuotes") or [item.get(f"{field}EvidenceQuote")])
                    for field in ("principles", "limitations", "perspectiveCases", "previousSteps", "nextSteps", "alternatives", "partOf", "isA"):
                        quotes.update(value.get("evidenceQuote") for value in item[field] if value.get("evidenceVerified"))
                    for case in item["perspectiveCases"]:
                        if case.get("evidenceVerified"):
                            for spec in case["specifications"]:
                                quotes.add(spec["evidenceQuote"])
                                quotes.update(quote for quote in spec["fieldEvidenceQuotes"].values() if quote)
                    for quote in filter(None, quotes):
                        eid = self.evidence_id(did, cid, quote)
                        updated_evidence_ids.add(eid)
                        body_fields = {}
                        for field in ("summary", "purpose"):
                            field_quotes = item.get(f"{field}EvidenceQuotes") or [item.get(f"{field}EvidenceQuote")]
                            if item.get(f"{field}EvidenceVerified") and item.get(field, "").strip() and item[field].strip() == merged[field] and quote in field_quotes:
                                body_fields[field] = merged[field]
                        evidence = await session.get(EvidenceSourceModel, eid)
                        if evidence is None:
                            session.add(EvidenceSourceModel(
                                id=eid, source_name=f"{doc.publisher}: {doc.title}", source_type="source_document",
                                publisher=doc.publisher, quote=quote, section_context=doc.file_path,
                                external_url=item.get("sourceUrl") or "", url_label="원문 보기" if item.get("sourceUrl") else "로컬 원문", credibility_tier="원문 자료",
                                referenced_concepts=[{"conceptId": cid, "name": concept.title, "bodyFields": body_fields}]))
                        elif body_fields:
                            refs = deepcopy(evidence.referenced_concepts or [])
                            ref = next((ref for ref in refs if ref.get("conceptId") == cid), None)
                            if ref is None:
                                refs.append({"conceptId": cid, "name": concept.title, "bodyFields": body_fields})
                            else:
                                ref["bodyFields"] = {**ref.get("bodyFields", {}), **body_fields}
                            evidence.referenced_concepts = refs
                    await session.flush()
                    await source_repo.save_perspective_cases(session, cid, item["_caseUpdates"])
                    updated_cids.add(cid)
                    await session.flush()
                doc.last_preview_payload = [{**raw, "_appliedCases": item["_appliedCases"], "_appliedRelations": item["_appliedRelations"]}
                                            for raw, item in zip(doc.last_preview_payload, items)]
                await source_repo.mark_applied(session, did)
                applied_count += 1
            if pending:
                await concept_repo.reconcile_relation_edges(session,
                    [removed for _, items in pending for item in items for removed in item["_removedRelations"]])
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        for eid in updated_evidence_ids:
            await cache_manager.delete(f"evidence:detail:{eid}")
        if updated_cids:
            for prefix in ("concept:subgraph:", "concept:explainer:", "concept:tree:", "spotlight:", "chatbot:context:"):
                await cache_manager.delete_prefix(prefix)
        return ApplyExtractionResponseDTO(appliedCount=applied_count, updatedConcepts=sorted(updated_cids),
                                          message=f"{applied_count}개 문서의 지식이 위키에 적용되었습니다.")


source_service = SourceExtractionService(use_examples=False)
