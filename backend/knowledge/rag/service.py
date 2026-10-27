import asyncio
import hashlib
from time import monotonic

from ..core.errors import AppError
from ..core.ids import new_id
from ..core.usage import summarize_usage, unknown_usage
from ..documents.repository import DocumentRepository
from .context import group_matches, select_context
from .entities import RetrievalRun
from .planning import context_characters, coverage, plan_requirements
from .grounding import compose_grounding


class RetrievalService:
    def __init__(self, session_factory, embedding_client, settings):
        self.session_factory, self.embedding_client, self.settings = session_factory, embedding_client, settings

    async def search(self, principal, request, *, for_answer=False, progress=None,
                     cancel_event=None, history=None):
        principal.require("rag:answer" if for_answer else "rag:retrieve")
        start = monotonic()
        retrieval_id, groups = new_id("ret"), [g.public() for g in request.source_groups]
        usages, warnings, query_log = [], [], []
        plan = plan_requirements(request.message, request.aspect)

        async def report(stage, message):
            if cancel_event and cancel_event.is_set():
                raise asyncio.CancelledError()
            if progress:
                await progress({"stage": stage, "message": message, "retrievalRunId": retrieval_id})

        await report("snapshot", "현재 권한과 자료 판본을 확인합니다.")
        async with self.session_factory() as session:
            repo = DocumentRepository(session)
            snapshot = await repo.resolve_snapshot(principal, None, groups)
            if request.source_revision_ids:
                snapshot = sorted(set(snapshot).intersection(request.source_revision_ids))
            attachments = await repo.attachment_context(principal, request.attachment_ids, request.conversation_id)
            selected_documents = await repo.selected_context(principal, request.document_context_ids) if request.document_context_ids else []
        # Request-specific documents never broaden the shared index snapshot.
        private_context = attachments + selected_documents
        if groups:
            private_context = [h for h in private_context if any(group_matches(h, g) for g in groups)]
        snapshot_id = "idx-" + hashlib.sha256("|".join(sorted(snapshot)).encode()).hexdigest()[:24]
        if private_context:
            warnings.append("선택 문헌은 이 요청의 문맥으로만 사용하며 공용 검색 반영을 의미하지 않습니다.")
        query = request.message
        previous_questions = [m["content"] for m in (history or []) if m["role"] == "user"]
        if previous_questions:
            query += "\n대화의 앞선 질문: " + previous_questions[-1][:2000]

        async def execute_query(text, requirement_id=None):
            await report("searching", "보유 문헌에서 질문의 근거를 찾습니다.")
            call_start = monotonic()
            try:
                # There is no open SQL session or transaction during embedding I/O.
                batch = await self.embedding_client.embed([text])
            except (Exception, asyncio.CancelledError) as exc:
                if getattr(exc, "code", None) != "configuration_blocked":
                    usages.append(unknown_usage("query_embedding", self.settings.embedding_model,
                        source="fixture" if self.embedding_client.profile_id.startswith("fixture:") else "provider"))
                query_log.append({"query": text, "requirementId": requirement_id,
                    "elapsedMs": round((monotonic() - call_start) * 1000, 2), "hitCount": None,
                    "status": "interrupted" if isinstance(exc, asyncio.CancelledError) else "failed"})
                raise
            usages.append({**batch.usage, "operation": "query_embedding"})
            if not batch.vectors or len(batch.vectors) != 1:
                raise AppError(502, "EMBEDDING_CONTRACT_ERROR", "질문 임베딩 응답이 올바르지 않습니다.")
            async with self.session_factory() as session:
                result = await DocumentRepository(session).search(
                    principal, batch.vectors[0], self.embedding_client.profile_id, text,
                    source_revision_ids=snapshot, source_groups=groups,
                    limit=max(self.settings.retrieval_limit, len(groups)))
            query_log.append({"query": text, "elapsedMs": round((monotonic() - call_start) * 1000, 2),
                              "hitCount": len(result["hits"]), "requirementId": requirement_id, "status": "completed"})
            warnings.extend(result.get("warnings", []))
            return result

        try:
            initial = await execute_query(query) if snapshot else {"hits": [], "groupCoverage": []}
            direct_hits = initial["hits"]
            hits = private_context + direct_hits
            stop_reason = "basic_search_completed"
            extended_start, extra_count = None, 0
            if request.extended:
                await report("extended", "부족한 측면과 주변 구간을 추가 확인합니다.")
                extended_start = monotonic()
                stop_reason = "query_budget"

                async def within_budget(operation):
                    remaining = self.settings.extended_seconds - (monotonic() - extended_start)
                    if remaining <= 0:
                        raise TimeoutError()
                    async with asyncio.timeout(remaining):
                        return await operation()

                async def neighbors():
                    async with self.session_factory() as session:
                        return await DocumentRepository(session).get_neighbors(principal,
                            [h["passageId"] for h in hits], source_revision_ids=snapshot, source_groups=groups)

                try:
                    if context_characters(hits) < self.settings.context_max_characters:
                        hits += [{key: value for key, value in h.items() if key != "neighborOf"}
                                 for h in await within_budget(neighbors)]
                    # Literal mentions do not establish answerable conditions or
                    # numbers. Prioritize missing signals, but do not skip the
                    # remaining queries or claim sufficiency from word matches.
                    states = {state["id"]: state for state in coverage(plan, hits)}
                    search_plan = sorted(plan, key=lambda item: states[item["id"]]["status"] != "unknown")
                    for item in search_plan:
                        if context_characters(hits) >= self.settings.context_max_characters:
                            stop_reason = "context_budget"
                            break
                        if extra_count >= self.settings.extended_max_queries:
                            stop_reason = "query_budget"
                            break
                        if not snapshot:
                            stop_reason = "no_searchable_sources"
                            break
                        old_ids = {h["passageId"] for h in hits}
                        extra_count += 1
                        extra_result = await within_budget(lambda: execute_query(item["query"], item["id"]))
                        hits += extra_result["hits"]
                        if not any(h["passageId"] not in old_ids for h in extra_result["hits"]):
                            stop_reason = "no_new_evidence"
                            break
                    else:
                        stop_reason = "planned_queries_exhausted"
                except TimeoutError:
                    stop_reason = "time_budget"
                    warnings.append("추가 탐색 시간 예산이 끝나 이미 확보한 근거로 답변합니다.")
                    if query_log and query_log[-1]["status"] == "interrupted":
                        query_log[-1]["status"] = "time_budget"
            else:
                async with self.session_factory() as session:
                    neighbors = await DocumentRepository(session).get_neighbors(principal,
                        [h["passageId"] for h in direct_hits], source_revision_ids=snapshot, source_groups=groups)
                direct_order = {hit["passageId"]: i for i, hit in enumerate(direct_hits)}
                neighbors.sort(key=lambda h: min(direct_order[origin] for origin in h["neighborOf"]))
                # Preserve direct-result priority; nearby context uses the remaining budget.
                seen = {hit["passageId"] for hit in hits}
                hits += [{key: value for key, value in h.items() if key != "neighborOf"}
                         for h in neighbors if h["passageId"] not in seen]
            extended_elapsed = round((monotonic() - extended_start) * 1000, 2) if extended_start else None
            await report("context", "근거의 조건·출처와 문맥 범위를 구성합니다.")
            selected = select_context(hits, self.settings.context_max_characters)
            if context_characters(hits) > self.settings.context_max_characters:
                warnings.append("문맥 크기 한도로 일부 검색 구간만 답변에 사용합니다.")
            async with self.session_factory() as session:
                repo = DocumentRepository(session)
                if not await repo.ensure_readable(principal, [h["sourceRevisionId"] for h in selected]):
                    raise AppError(403, "SOURCE_ACCESS_CHANGED", "검색 도중 자료의 접근 권한이 변경되었습니다.")
                from ..ontology.repository import OntologyRepository
                ontology = OntologyRepository(session)
                concept_ids = list(request.concept_ids)
                if not concept_ids:
                    concept_ids = await ontology.resolve_mentions(request.message)
                context = await ontology.context(principal, concept_ids, snapshot)
            source_views = context.get("sourceViews", [])
            if groups:
                source_views = [view for view in source_views if any(group_matches(view, group) for group in groups)]
                context["relations"] = [relation for relation in context.get("relations", []) if relation.get("evidence")
                    and all(any(group_matches(evidence, group) for group in groups) for evidence in relation["evidence"])]
            if request.aspect:
                source_views = [v for v in source_views if v.get("aspect") == request.aspect]
            selected, grounding, grounding_stats = compose_grounding(hits, context.get("relations", []), source_views,
                                                                     self.settings.context_max_characters, groups=groups)
            async with self.session_factory() as session:
                if not await DocumentRepository(session).ensure_readable(principal, [h["sourceRevisionId"] for h in selected]):
                    raise AppError(403, "SOURCE_ACCESS_CHANGED", "문맥 구성 중 자료의 접근 권한이 변경되었습니다.")
            if grounding_stats["relations"] or grounding_stats["sourceViews"]:
                warnings.append("일부 관계·관점 카드는 전체 근거가 문맥 예산에 들어오지 않아 생성 프롬프트에서 제외했습니다.")
            group_coverage = [{"groupId": group["groupId"], "hitCount": sum(group_matches(h, group) for h in selected),
                               "status": "available" if any(group_matches(h, group) for h in selected) else "missing",
                               "missingAspects": [request.aspect] if request.aspect and not any(group_matches(v, group) for v in source_views) else []}
                              for group in groups]
            if not selected:
                warnings.append("현재 허용된 자료에서 사용할 근거를 확보하지 못했습니다.")
            if any(u.get("source") == "fixture" for u in usages):
                warnings.append("명시적 fixture 임베딩으로 실행한 검증 결과입니다. 실제 모델 검색 품질을 뜻하지 않습니다.")
            result = {"retrievalRunId": retrieval_id, "indexSnapshotId": snapshot_id,
                      "hits": selected, "relatedConcepts": context.get("relatedConcepts", []),
                      "relations": context.get("relations", []), "sourceViews": source_views,
                      "grounding": grounding,
                      "groupCoverage": group_coverage, "warnings": list(dict.fromkeys(warnings)),
                      "appliedFilters": {"sourceRevisionIds": snapshot, "sourceGroups": groups, "aspect": request.aspect,
                                         "documentContextIds": request.document_context_ids, "attachmentIds": request.attachment_ids},
                      "usage": summarize_usage(usages), "stopReason": stop_reason,
                      "requirementCoverage": coverage(plan, selected), "semanticSufficiency": "not_evaluated",
                      "exploration": {"planner": "bounded_parameter_aspect_rules_v2", "extraQueries": extra_count,
                          "queryBudget": self.settings.extended_max_queries, "secondsBudget": self.settings.extended_seconds,
                          "contextCharacters": sum(len(h["text"]) for h in selected),
                          "contextCharacterBudget": self.settings.context_max_characters,
                          "grounding": grounding_stats},
                      "timings": {"totalMs": round((monotonic() - start) * 1000, 2),
                          "extendedMs": extended_elapsed},
                      "queries": query_log}
            async with self.session_factory() as session, session.begin():
                session.add(RetrievalRun(id=retrieval_id, owner_id=principal.id, request=request.public(),
                                         snapshot_id=snapshot_id, revision_ids=snapshot, result=result))
            return result
        except (Exception, asyncio.CancelledError) as exc:
            exc.usage = summarize_usage(usages)
            async with self.session_factory() as session, session.begin():
                session.add(RetrievalRun(id=retrieval_id, owner_id=principal.id, request=request.public(),
                    snapshot_id=snapshot_id, revision_ids=snapshot,
                    result={"status": "cancelled" if isinstance(exc, asyncio.CancelledError) else "failed", "code": getattr(exc, "code", "RETRIEVAL_FAILED"),
                            "usage": summarize_usage(usages), "queries": query_log}))
            raise
