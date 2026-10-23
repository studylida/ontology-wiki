"""Isolated discovery contract checks and optional browser fixture server.

No operational DB, source writes, credentials, or model network calls are used.
Run with --serve for the actual frontend against deterministic external fixtures.
"""
import asyncio
from contextlib import ExitStack
import json
import os
import runpy
from pathlib import Path
import sys
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

os.environ["DB_ENGINE"] = "sqlite"
os.environ["SQLITE_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["USE_IN_MEMORY_REDIS"] = "true"
os.environ["DEBUG"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from backend.app.api import research
from backend.app.core.database import Base, engine, async_session_factory
from backend.app.core.llm_gateway import llm_gateway
from backend.app.agents.research_discovery_agent import research_discovery_agent
from backend.app.schemas.research import ResearchSearchPlan, ResearchAssessmentDraft
from backend.app.models.entities import ResearchSessionModel, ConceptModel, ComparisonSessionModel, EvidenceSourceModel
from backend.app.core.security import get_current_user_optional
from backend.app.repositories.research_repo import research_repo
from backend.app.main import app

QUESTION = "HBM 하이브리드 본딩에서 수율을 떨어뜨리는 요인"
RECORDS = [
    dict(title=["[격리 fixture] Hybrid bonding particle defects"], publisher="Fixture Institute",
         DOI="10.fixture/particles", abstract="Particles on die surfaces cause local non-bonded areas in die-to-wafer hybrid bonding."),
    dict(title=["[격리 fixture] Copper surface planarity"], publisher="Fixture Institute",
         DOI="10.fixture/planarity", abstract="Copper dishing and surface planarity influence incomplete Cu bonding. Test structures are not HBM products."),
    dict(title=["[격리 fixture] HBM hybrid bonding metadata only"], publisher="Fixture Institute", DOI="10.fixture/metadata"),
    dict(title=["[격리 fixture] Hybrid bonding in unrelated materials"], publisher="Fixture Institute",
         DOI="10.fixture/unrelated", abstract="This paper studies adhesive joints of polymer pipes, not semiconductor interconnects."),
]


async def fixture_gateway(**kwargs):
    assert kwargs["model_override"] == "gpt-6.1-sol"
    assert kwargs["reasoning_effort"] == "medium" and kwargs["allow_fallback"] is False
    payload = json.loads(kwargs["prompt"])
    if "question" in payload:
        unclear = payload["question"] == "본딩 문제" and not payload["clarificationAnswer"]
        return json.dumps(dict(originalQuestion=payload["question"], interpretedQuestion=(
            "HBM 하이브리드 본딩 공정의 결함 발생 요인을 조사합니다." if not unclear else "본딩 문제의 조사 대상을 확인합니다."),
            assumptions=["HBM 세대와 적층 수는 미지정이며 일반 공정 자료도 한계를 표시해 조사합니다."],
            searchQueries=["HBM hybrid bonding yield defects"],
            clarificationQuestion="반도체 접합 공정의 수율 문제인가요?" if unclear else None,
            status="needs_clarification" if unclear else "ready"), ensure_ascii=False)
    if "candidates" in payload:
        return json.dumps({"candidates": [dict(id=e["id"], priority="normal", reason="격리 후보 선별") for e in payload["candidates"]]})
    if "plan" in payload:
        assessments = []
        for item in payload["evidence"]:
            quote = " ".join(segment["text"] for segment in item["readSegments"])
            unrelated = "polymer pipes" in quote
            assessments.append(dict(id=item["id"], assessment=dict(
                decision="excluded" if unrelated else "included",
                documentSummary="고분자 배관의 접착 연구입니다." if unrelated else (
                    "다이 표면 입자와 미접합 영역의 관계를 다룬 공정 연구입니다." if "Particles" in quote
                    else "구리 표면의 디싱과 불완전 접합을 다룬 실험 구조 연구입니다."),
                inclusionReason="반도체 접합과 대상이 달라 제외했습니다." if unrelated else (
                    "질문의 수율 저하 요인 중 접합 전 표면 오염을 조사하는 데 도움이 됩니다." if "Particles" in quote
                    else "질문의 수율 저하 요인 중 접합면 평탄도와 연마 공정을 살펴볼 근거입니다."),
                usefulness="" if unrelated else "결함의 발생 단계와 확인할 공정 조건을 파악할 수 있습니다.",
                limitations=["격리 검증용 fixture이며 실제 연구 결과가 아닙니다.", "초록만 확인했으며 HBM 양산 수율을 직접 검증하지 않았습니다."],
                evidenceReferences=[item["readSegments"][0]["id"]])))
        return json.dumps(dict(assessments=assessments, followUpQueries=[], remainingQuestions=["HBM 실제품의 동일 조건 검증이 필요합니다."]), ensure_ascii=False)
    if "topic" in payload:
        assert all("assessment" not in item for item in payload["evidence"])
        eid = payload["evidence"][0]["id"]
        return json.dumps(dict(report=dict(title="HBM 격리 검증 종합 분석", narrativeMarkdown=f"표면 상태와 접합 결함을 조사했습니다. [{eid}]",
            consensusFacts=[], tensionGaps=["HBM 실제품 적용은 추가 확인이 필요합니다."]), candidates=[]), ensure_ascii=False)
    return None


def fixtures():
    stack = ExitStack()
    stack.enter_context(patch.object(llm_gateway, "generate_text", new=fixture_gateway))
    stack.enter_context(patch.object(research_repo, "crossref", new=AsyncMock(return_value=RECORDS)))
    stack.enter_context(patch.object(research_repo, "source_documents", side_effect=lambda: iter([])))
    stack.enter_context(patch.object(research_repo, "fetch_public", new=AsyncMock(side_effect=ValueError("fixture_unavailable"))))
    return stack


async def candidate_selection_checks():
    from backend.app.services.research_service import research_service
    from backend.app.services.research_evidence import usable_research_evidence
    rows = [EvidenceSourceModel(id=f"candidate-glossary-{i:02}", source_name=f"Hybrid glossary {i}",
        source_type="academic_peer_reviewed", publisher="fixture", quote="generic glossary: hybrid means a mixture.",
        external_url="https://example.org/shared", url_label="원문", credibility_tier="공개", referenced_concepts=[]) for i in range(40)]
    rows += [EvidenceSourceModel(id=eid, source_name="HBM hybrid bonding yield defects", source_type="academic_peer_reviewed",
        publisher="fixture", quote=quote, external_url=url, url_label="원문", credibility_tier="공개", referenced_concepts=[])
        for eid, quote, url in [
            ("candidate-relevant", "Particles cause hybrid bonding yield defects.", "https://example.org/shared"),
            ("candidate-distinct", "Copper planarity affects hybrid bonding yield defects.", "https://example.org/shared"),
            ("candidate-doi", RECORDS[0]["abstract"], "https://doi.org/10.fixture/particles")]]
    documents = [(f"candidate/{i:02}.md", "# HBM hybrid bonding yield defects\n\n" + (
        "fixture insufficient: HBM hybrid bonding topic only." if i == 0 else "Particles cause hybrid bonding yield defects.")) for i in range(40)]
    async with async_session_factory() as db:
        db.add_all(rows); await db.commit()
        stored = await research_repo.evidences(db)
        with patch.object(research_repo, "source_documents", side_effect=lambda: iter(documents)):
            selected, ok = await research_service.gather(db, "HBM hybrid bonding yield defects", [], [])
            assert ok and len(selected) == 30
            counts = {kind: sum(e["retrievalStatus"] == kind for e in selected) for kind in ("registered_excerpt", "source_excerpt", "abstract", "metadata")}
            assert counts == dict(registered_excerpt=13, source_excerpt=13, abstract=3, metadata=1), counts
            assert {"candidate-relevant", "candidate-distinct", "candidate-doi"} <= {e["id"] for e in selected}
            with patch.object(research_repo, "evidences", new=AsyncMock(return_value=list(reversed(stored)))):
                reversed_selection, _ = await research_service.gather(db, "HBM hybrid bonding yield defects", [], [])
            assert [e["id"] for e in selected] == [e["id"] for e in reversed_selection]
            for external in (AsyncMock(return_value=[]), AsyncMock(side_effect=httpx.ConnectError("fixture"))):
                with patch.object(research_repo, "crossref", new=external):
                    warnings = []; kept, search_ok = await research_service.gather(db, "HBM hybrid bonding yield defects", [], warnings)
                    assert len(kept) == 30 and sum(e["retrievalStatus"] == "registered_excerpt" for e in kept) == 15
                    assert sum(e["retrievalStatus"] == "source_excerpt" for e in kept) == 15
                    assert search_ok == (not warnings)
            with patch.object(research_repo, "evidences", new=AsyncMock(return_value=[])):
                kept, _ = await research_service.gather(db, "HBM hybrid bonding yield defects", [], [])
                assert len(kept) == 30 and sum(e["retrievalStatus"] == "source_excerpt" for e in kept) == 26
            with patch.object(research_repo, "source_documents", side_effect=lambda: iter([])):
                kept, _ = await research_service.gather(db, "HBM hybrid bonding yield defects", [], [])
                assert len(kept) == 30 and sum(e["retrievalStatus"] == "registered_excerpt" for e in kept) == 26
    assessed = set()
    original_assess = research_discovery_agent.assess
    async def observe_assess(*args, **kwargs):
        result = await original_assess(*args, **kwargs)
        inputs = {e["id"]: " ".join(s["text"] for s in e["readSegments"]) for e in args[1]}
        assessed.update(inputs)
        for entry in result.assessments:
            if "generic glossary" in inputs[entry.id]:
                entry.assessment.decision = "excluded"
            if "fixture insufficient" in inputs[entry.id]:
                entry.assessment.decision = "deferred"
        return result
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
        with patch.object(research_repo, "source_documents", side_effect=lambda: iter(documents)), patch.object(research_discovery_agent, "assess", new=observe_assess):
            response = await client.post("/api/v1/research/discover", json=dict(searchTopic=QUESTION))
            assert response.status_code == 200, response.text
            result = response.json(); feed = result["evidenceFeed"]
            by_id = {e["id"]: e for e in feed}
            assert "candidate-relevant" in assessed and any(eid.startswith("src-") for eid in assessed)
            assert any(eid.startswith("doi-") for eid in assessed)
            assert by_id["candidate-doi"]["quote"] == RECORDS[0]["abstract"]
            assert sum(e["externalUrl"].endswith("10.fixture/particles") for e in feed) == 1
            assert "candidate-relevant" in by_id and "candidate-distinct" in by_id
            assert all(not usable_research_evidence(e) for e in feed if e["id"].startswith("candidate-glossary") or e["retrievalStatus"] == "metadata" or e.get("deferReason") == "insufficient_content")
            blocked = next(e["id"] for e in feed if e["assessment"]["decision"] == "deferred")
            assert (await client.post(f"/api/v1/research/sessions/{result['sessionId']}/synthesize", json=dict(selectedEvidenceIds=[blocked]))).status_code == 422
            restored = (await client.get(f"/api/v1/research/sessions/{result['sessionId']}")).json()
            continuation = await client.post(f"/api/v1/research/sessions/{result['sessionId']}/continue", json=dict(expectedUpdatedAt=restored["updatedAt"]))
            assert continuation.status_code == 200, continuation.text
            assert {e["id"] for e in continuation.json()["evidenceFeed"]} == set(by_id)
    async with async_session_factory() as db:
        for row in await research_repo.evidences(db):
            await db.delete(row)
        await db.commit()
    print("PASS ranked/interleaved routes under registered flood, query-order independence, empty/failing routes, original IDs/quotes, same-URL separation, DOI merge and continuation guards")


async def checks():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await candidate_selection_checks()
    async with async_session_factory() as db:
        db.add(ResearchSessionModel(id="legacy-fixture", search_topic="과거 조사", evidence_feed=[dict(
            id="legacy-e", sourceName="과거 자료", sourceType="academic_paper", publisher="fixture", quote="과거에 확보한 본딩 발췌",
            externalUrl="", urlLabel="", credibilityTier="등록 발췌", retrievalStatus="source_excerpt")],
            candidates=[], synthesis_report={}))
        db.add(ConceptModel(id="fixture-concept", title="격리 본딩", eng_name="Fixture Bonding", domain_facet="unit_process", process_category="본딩", scale_level=3, summary="격리 정의", purpose="검증"))
        db.add(ComparisonSessionModel(id="fixture-comparison", user_id="fixture", title="격리 비교", query="원래 비교 질문",
            context_params=dict(targetA="fixture-concept", targetB="fixture-concept", conditions=["원래 조건"]),
            snapshots=[{}, {}, {"deepDiveHistory": []}]))
        await db.commit()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://fixture") as client:
        async def post(path, payload):
            response = await client.post("/api/v1/" + path, json=payload)
            response.raise_for_status()
            return response.json()
        clarified = await post("research/clarify", dict(searchTopic=QUESTION))
        plan = clarified["searchPlan"]
        assert plan["status"] == "ready" and "hybrid bonding" in plan["searchQueries"][0]
        # A real multi-document assessment may exceed 45s; respect the overall deadline.
        original_assess = research_discovery_agent.assess
        assessment_budgets = []
        async def capture_budget(*args, **kwargs):
            assessment_budgets.append(kwargs["timeout_sec"])
            return await original_assess(*args, **kwargs)
        clock = iter([0])
        with patch("backend.app.services.research_service.monotonic", side_effect=lambda: next(clock, 90)), patch.object(
                research_discovery_agent, "assess", new=capture_budget):
            result = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
        assert assessment_budgets and all(0 < budget <= 60 for budget in assessment_budgets)
        cancelled = []
        async def stalled_assessment(*args, **kwargs):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.append(True)
        clock = iter([0])
        with patch("backend.app.services.research_service.monotonic", side_effect=lambda: next(clock, 149.99)), patch.object(
                research_discovery_agent, "assess", new=stalled_assessment):
            timed_out = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
        assert cancelled == [True] and len(timed_out["evidenceFeed"]) == 4
        assert all(e["assessment"]["decision"] == "deferred" for e in timed_out["evidenceFeed"])
        assert not timed_out["synthesisReady"] and "시간 예산" in timed_out["discoveryContext"]["stopReason"]
        saved_timeout = (await client.get("/api/v1/research/sessions/" + timed_out["sessionId"])).json()
        assert saved_timeout["evidenceFeed"] == timed_out["evidenceFeed"]
        sid = result["sessionId"]
        feed = result["evidenceFeed"]
        included = [e for e in feed if e["assessment"]["decision"] == "included"]
        assert len(feed) == 4 and len(included) == 2 and result["synthesisReady"]
        assert result["discoveryContext"]["queriesExecuted"] == plan["searchQueries"]
        for item in included:
            assert set(item["assessment"]["evidenceReferences"]) <= {s["id"] for s in item["readSegments"]}
            assert item["relevanceScore"] is None
        for item in feed:
            if item not in included:
                response = await client.post(f"/api/v1/research/sessions/{sid}/synthesize", json=dict(selectedEvidenceIds=[item["id"]]))
                assert response.status_code == 422
        selected = [e["id"] for e in included]
        synthesis = await post(f"research/sessions/{sid}/synthesize", dict(selectedEvidenceIds=selected))
        assert synthesis["synthesisReport"]["generationStatus"] == "ai_generated"
        restored = (await client.get(f"/api/v1/research/sessions/{sid}")).json()
        assert restored["discoveryContext"] == result["discoveryContext"]
        assert restored["evidenceFeed"] == feed
        with patch.object(research_repo, "source_documents", return_value=[
                (f"flood/{i}.md", "# HBM hybrid bonding\n\nHBM hybrid bonding yield defects.") for i in range(40)]):
            crowded = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
        assert len(crowded["evidenceFeed"]) == 30
        external_ids = {e["id"] for e in feed if e["externalUrl"].startswith("https://doi.org/")}
        assert external_ids <= {e["id"] for e in crowded["evidenceFeed"]}
        # External-first retrieval must preserve a more useful local excerpt for the same DOI.
        with patch.object(research_repo, "source_documents", return_value=[("fixture/same-doi.md",
                "---\nurl: https://doi.org/10.fixture/particles\n---\n# HBM study\n\nHBM hybrid bonding surface damage.")]):
            combined = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
        same_doi = [e for e in combined["evidenceFeed"] if e["externalUrl"].lower().endswith("10.fixture/particles")]
        assert len(same_doi) == 1 and same_doi[0]["retrievalStatus"] == "source_excerpt"
        assert "surface damage" in same_doi[0]["quote"] and RECORDS[0]["abstract"] in same_doi[0]["quote"]
        assert "Crossref 초록" in same_doi[0]["sectionContext"] and "same-doi.md" in same_doi[0]["sectionContext"]
        unclear = await post("research/clarify", dict(searchTopic="본딩 문제"))
        assert unclear["searchPlan"]["status"] == "needs_clarification"
        clear = await post("research/clarify", dict(searchTopic="본딩 문제", clarificationAnswer="네, 반도체 접합 수율입니다."))
        assert clear["searchPlan"]["status"] == "ready"
        legacy = (await client.get("/api/v1/research/sessions/legacy-fixture")).json()
        assert legacy["discoveryContext"] is None and legacy["evidenceFeed"][0]["assessment"] is None
        await post("research/sessions/legacy-fixture/synthesize", dict(selectedEvidenceIds=["legacy-e"]))
        # The server restores authoritative comparison context, ignoring the browser claim.
        linked = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan,
            comparisonContext=dict(comparisonSessionId="fixture-comparison", originalQuestion="잘못된 브라우저 값")))
        assert linked["comparisonContext"]["originalQuestion"] == "원래 비교 질문"
        rejected = next(e["id"] for e in linked["evidenceFeed"] if e["assessment"]["decision"] == "excluded")
        response = await client.post("/api/v1/comparison-sessions/fixture-comparison/research-evidence", json=dict(
            researchSessionId=linked["sessionId"], selectedEvidenceIds=[rejected, linked["evidenceFeed"][0]["id"]]))
        assert response.status_code == 422
        # Invalid references cannot be promoted into included assessments.
        async def invalid(**kwargs):
            raw = json.loads(await fixture_gateway(**kwargs))
            if "assessments" in raw:
                for entry in raw["assessments"]:
                    entry["assessment"]["evidenceReferences"] = ["invented-segment"]
            return json.dumps(raw, ensure_ascii=False)
        with patch.object(llm_gateway, "generate_text", new=invalid):
            bad = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
            assert not bad["synthesisReady"] and all(e["assessment"]["decision"] == "deferred" for e in bad["evidenceFeed"])
        with patch.object(llm_gateway, "generate_text", new=AsyncMock(return_value=None)):
            failed = await post("research/discover", dict(searchTopic=QUESTION))
            assert failed["discoveryContext"]["generationStatus"] == "source_only" and not failed["synthesisReady"]
        with patch.object(research_repo, "crossref", new=AsyncMock(side_effect=httpx.ConnectError("fixture"))):
            failed = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
            assert failed["evidenceFeed"] == [] and failed["discoveryContext"]["generationStatus"] == "partial"
        # Duplicate queries stop; a new query can expand discovery but never repeats indefinitely.
        async def followups(**kwargs):
            raw = json.loads(await fixture_gateway(**kwargs))
            if "assessments" in raw:
                raw["followUpQueries"] = ["HBM hybrid bonding yield defects", "HBM Cu dishing defects"]
            return json.dumps(raw, ensure_ascii=False)
        with patch.object(llm_gateway, "generate_text", new=followups):
            expanded = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
            assert len(expanded["evidenceFeed"]) == 4 and len(expanded["discoveryContext"]["queriesExecuted"]) == 2
        # A later query must read a newly relevant paragraph in an already known document.
        async def new_segment(**kwargs):
            raw = json.loads(await fixture_gateway(**kwargs))
            if "assessments" in raw:
                supplied = json.loads(kwargs["prompt"])["evidence"]
                for entry, item in zip(raw["assessments"], supplied):
                    entry["assessment"]["decision"] = "included" if any("damage" in seg["text"] for seg in item["readSegments"]) else "deferred"
                raw["followUpQueries"] = ["surface damage"]
            return json.dumps(raw, ensure_ascii=False)
        source = "# HBM reference\n\nHBM background overview.\n\nSurface damage causes non-bonded regions."
        with patch.object(llm_gateway, "generate_text", new=new_segment), patch.object(research_repo, "crossref", new=AsyncMock(return_value=[])), patch.object(research_repo, "source_documents", side_effect=lambda: iter([("fixture/local.md", source)])):
            local = await post("research/discover", dict(searchTopic=QUESTION, searchPlan={**plan, "searchQueries": ["HBM background overview"]}))
            assert len(local["evidenceFeed"]) == 1 and local["evidenceFeed"][0]["assessment"]["decision"] == "included"
            assert "Surface damage" in local["evidenceFeed"][0]["quote"]
        # URL query parameters identify different documents unless this is a DOI resolver.
        async with async_session_factory() as db:
            for suffix in ["A", "B"]:
                db.add(EvidenceSourceModel(id="query-" + suffix, source_name="HBM hybrid bonding query " + suffix,
                    source_type="academic_paper", publisher="Fixture Institute", quote="Particles affect HBM bonding yield.",
                    external_url="https://fixture.example/article?id=" + suffix, url_label="fixture", credibility_tier="공인 학술"))
            await db.commit()
        distinct = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
        assert {"query-A", "query-B"} <= {e["id"] for e in distinct["evidenceFeed"]}
        # Two local files referring to the same DOI remain one document, with combined excerpts.
        files = [("fixture/a.md", "---\nurl: https://doi.org/10.fixture/shared\n---\n# HBM study\n\nHBM hybrid bonding particles."),
                 ("fixture/b.md", "---\nurl: https://dx.doi.org/10.fixture/SHARED\n---\n# HBM study\n\nHBM hybrid bonding surface damage.")]
        with patch.object(research_repo, "evidences", new=AsyncMock(return_value=[])), patch.object(research_repo, "crossref", new=AsyncMock(return_value=[])), patch.object(research_repo, "source_documents", side_effect=lambda: iter(files)):
            duplicate = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
            assert len(duplicate["evidenceFeed"]) == 1
            assert "particles" in duplicate["evidenceFeed"][0]["quote"] and "surface damage" in duplicate["evidenceFeed"][0]["quote"]
        # One DOI is one document; preserve the registered ID and the entire original quote.
        long_quote = "Particles affect HBM hybrid bonding yield. " + "original excerpt " * 450
        async with async_session_factory() as db:
            db.add(EvidenceSourceModel(id="registered-long", source_name="HBM hybrid bonding yield", source_type="academic_paper",
                publisher="Fixture Institute", quote=long_quote, external_url="https://doi.org/10.fixture/PARTICLES",
                url_label="fixture", credibility_tier="공인 학술", referenced_concepts=[]))
            await db.commit()
        long_result = await post("research/discover", dict(searchTopic=QUESTION, searchPlan=plan))
        long_item = next(e for e in long_result["evidenceFeed"] if e["id"] == "registered-long")
        assert len(long_result["evidenceFeed"]) == 6 and long_item["quote"] == long_quote
        from backend.app.services.research_evidence import assessment_segments
        assert sum(len(seg["text"]) for seg in assessment_segments(long_item)) <= 6000
        async with async_session_factory() as db:
            session = await db.get(ResearchSessionModel, long_result["sessionId"])
            session.candidates = [dict(candidateId="long-candidate", candidateType="concept_enrichment", title="격리 검토",
                summary="발췌 보존 검증", draftPayload=dict(conceptId="fixture-concept", content="검토용 제안"), evidenceIds=["registered-long"])]
            await db.commit()
        async def fixture_user():
            return SimpleNamespace(id="fixture", level=3, name="격리 검토자", department="검증")
        app.dependency_overrides[get_current_user_optional] = fixture_user
        try:
            await post("research/candidates/long-candidate/export-ticket", dict(sessionId=long_result["sessionId"], userNote="격리 검증"))
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)
    print("PASS HBM interpretation, evidence explanations, inclusion/defer/exclusion, reference validation, follow-up deduplication, legacy restore, synthesis context preservation, comparison guards and source-only failure; isolated in-memory DB")
    await engine.dispose()


if __name__ == "__main__":
    if "--regression" in sys.argv:
        async def regression_plan(question, *args, **kwargs):
            return ResearchSearchPlan(originalQuestion=question, interpretedQuestion=question, searchQueries=[question])
        async def regression_assess(plan, evidence, *args, **kwargs):
            return ResearchAssessmentDraft.model_validate({"assessments": [{"id": e["id"], "assessment": dict(
                decision="included", documentSummary="격리 검증 자료", inclusionReason="fixture 본딩 질문 근거",
                usefulness="검증", limitations=["격리 fixture"], evidenceReferences=[e["readSegments"][0]["id"]])} for e in evidence]})
        with patch.object(research_discovery_agent, "plan", new=regression_plan), patch.object(research_discovery_agent, "assess", new=regression_assess):
            runpy.run_path(str(Path(__file__).with_name("verify_research_flow.py")), run_name="__main__")
    else:
        with fixtures():
            if "--serve" in sys.argv:
                import uvicorn
                print("ISOLATED FIXTURE SERVER: in-memory DB; deterministic model and search; no real model calls", flush=True)
                uvicorn.run(app, host="127.0.0.1", port=18004, log_level="warning")
            else:
                asyncio.run(checks())
