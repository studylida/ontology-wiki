"""Milestone 5 Comprehensive Verification Test Suite.

Verifies:
1. Extended Seeds Coverage: 38+ frontend concepts, causal edges, perspective cases.
2. DLP RegimeAwareTokenizer: Normalization (Temp/Force/Yield/Time) and 100% reversible detokenization.
3. CircuitBreaker: Sliding window state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED).
4. Section 3.1 ClarifierAgent: 3 modes (Comparison Quick-Presets, Research Scope, Chatbot 3-Way Intent).
5. Section 3.2 ComparisonAgent: Multi-dimensional matrix with Zero-Hallucination Gap Isolation & 3-hop Tail Question.
6. Section 3.3 AdvisorAgent: Process Safety Margins (422 blocking on >300°C / >200N) & Plan A/B Compensation.
7. Section 3.4 DirectiveAgent: Expert reason preservation ("전문가 사유" allowed without 400 error) & integrity metrics.
8. Section 3.5 DeepResearchAgent: Whitelist domain evidence synthesis & KnowledgeCandidates generation.
9. Section 3.6 ExplainerAgent: Strict prompt guardrail "현재 공정 맥락({parentName}):" & pre-compilation.
10. Section 5.4 RBAC & Masking: Tier 3 sensitive metrics masking for line_engineer, unmasked for chief_reviewer, and access requests.
11. WORM Audit Merkle Chain: SHA-256 integrity verification.
12. SSE Streaming: Chatbot real-time token streaming endpoint.
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func

from backend.app.main import app
from backend.app.core.cache import cache_manager
from backend.app.core.database import async_session_factory
from backend.app.core.circuit_breaker import CircuitBreaker, CircuitState
from backend.app.core.dlp_tokenizer import dlp_tokenizer
from backend.app.core.security import mask_tier3_perspective, get_current_user_role
from backend.app.models.entities import (
    ConceptModel,
    PerspectiveCaseModel,
    CausalEdgeModel,
    EvidenceSourceModel,
    ComparisonSessionModel,
    ReviewTicketModel,
    ResearchSessionModel
)
from backend.app.agents import (
    clarifier_agent,
    comparison_agent,
    advisor_agent,
    directive_agent,
    deep_research_agent,
    explainer_agent
)


@pytest.fixture(autouse=True)
async def setup_test_cache():
    """Ensure in-memory/redis cache manager is initialized for testing."""
    await cache_manager.init()
    yield
    await cache_manager.close()


# ==============================================================================
# 1. Seeds Coverage: 38+ frontend concepts & Causal Edges
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_seeds_coverage():
    """Verify that all 38 frontend concepts are loaded in DB and causal queries work."""
    async with async_session_factory() as session:
        # 1. Total Concepts count >= 38
        count_stmt = select(func.count(ConceptModel.id))
        total_concepts = (await session.execute(count_stmt)).scalar()
        assert total_concepts >= 38, f"Expected at least 38 concepts, got {total_concepts}"

        # 2. Check representative frontend concepts
        target_ids = [
            "concept-tcb",
            "concept-mrmuf",
            "hybrid-bonding",
            "dry-etch",
            "concept-dry-etch",
            "concept-cryo-etch",
            "euv-lithography",
            "high-na-euv",
            "concept-high-na-euv",
            "concept-gaa-nanosheet"
        ]
        stmt = select(ConceptModel).where(ConceptModel.id.in_(target_ids))
        found = (await session.execute(stmt)).scalars().all()
        found_ids = {c.id for c in found}
        for tid in target_ids:
            assert tid in found_ids, f"Required concept '{tid}' not found in DB."

        # 3. Causal Edges count >= 20
        edge_count = (await session.execute(select(func.count(CausalEdgeModel.id)))).scalar()
        assert edge_count >= 20, f"Expected at least 20 causal edges, got {edge_count}"


# ==============================================================================
# 2. DLP Regime-Aware Tokenizer: Normalization & Detokenization
# ==============================================================================
def test_milestone5_dlp_tokenizer():
    """Verify that sensitive regimes are anonymized and accurately restored."""
    session_id = "test-session-dlp-001"
    raw_prompt = "본딩 피크 온도를 285°C로 설정하고 가압력 150N 및 N2 챔버 압력 0.5Torr에서 수율 98.5%를 달성하기 위한 방안은?"

    # Tokenize
    anonymized, token_map = dlp_tokenizer.tokenize(raw_prompt, session_id)
    assert "[TEMP_REGIME_PEAK:" in anonymized
    assert "[FORCE_REGIME_LOAD:" in anonymized
    assert "[RATIO_REGIME_METRIC:" in anonymized
    assert "285°C" not in anonymized
    assert "150N" not in anonymized

    # Detokenize
    restored = dlp_tokenizer.detokenize(anonymized, session_id)
    assert "285°C" in restored
    assert "150N" in restored
    assert "98.5%" in restored


# ==============================================================================
# 3. Circuit Breaker: State Machine Transitions
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_circuit_breaker_transitions():
    """Verify CLOSED -> OPEN -> HALF_OPEN -> CLOSED transition lifecycle."""
    cb = CircuitBreaker(
        sliding_window_size=4,
        failure_rate_threshold=0.5,
        wait_duration_open_sec=0.1,  # Fast for test
        permitted_calls_half_open=2
    )
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 4 failures out of 4 calls -> 100% failure rate -> OPEN
    await cb.record_call(False, 100.0)
    await cb.record_call(False, 100.0)
    await cb.record_call(False, 100.0)
    await cb.record_call(False, 100.0)
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    # Sleep to exceed wait_duration_open_sec
    await asyncio.sleep(0.15)

    # In HALF_OPEN state
    assert cb.state == CircuitState.HALF_OPEN
    assert cb.can_execute() is True

    # 2 successful probes -> CLOSED
    await cb.record_call(True, 100.0)
    await cb.record_call(True, 100.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


# ==============================================================================
# 4. Clarifier Agent: 3 Screen-Specific Modes
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_clarifier_agent_modes():
    """Verify Clarifier Agent Mode A, Mode B, and Mode C routing."""
    async with async_session_factory() as session:
        # Mode A: Comparison Clarifier
        comp_clarify = await clarifier_agent.clarify_comparison(
            query="TCB와 MR-MUF 16단 적층 열저항 및 휨 비교",
            base_concept_id="concept-tcb",
            custom_axes=["CAPEX 비용"],
            db=session
        )
        assert len(comp_clarify.branches) == 3
        assert any("Warpage" in b.title or "휨" in b.title for b in comp_clarify.branches)
        assert len(comp_clarify.dynamicAxesPool) >= 3
        assert len(comp_clarify.clarificationQuestions) >= 3

        # Mode B: Research Clarifier
        res_clarify = await clarifier_agent.clarify_research(
            search_topic="차세대 유리기판 TGV 공정 및 신뢰성",
            preferred_tier=["Tier 1"],
            db=session
        )
        assert res_clarify.searchTopic == "차세대 유리기판 TGV 공정 및 신뢰성"
        assert len(res_clarify.scopeFilters) >= 2
        assert any("IEEE" in inst or "SEMI" in inst for inst in res_clarify.targetInstitutions)

        # Mode C: Chatbot Intent Routing
        # (1) Action Trigger
        resp_act = await clarifier_agent.route_chatbot_intent(
            utterance="TCB랑 MR-MUF 비교 스튜디오 열어줘",
            concept_id="concept-tcb",
            db=session
        )
        assert resp_act.pathType == "action_trigger"
        assert resp_act.actionCard is not None
        assert "comparison" in resp_act.actionCard.targetUrl

        # (2) Factoid / Causal
        resp_fact = await clarifier_agent.route_chatbot_intent(
            utterance="TCB의 정의와 기본 원리를 알려줘",
            concept_id="concept-tcb",
            db=session
        )
        assert resp_fact.pathType in ["factoid_query", "causal_clarification"]
        assert len(resp_fact.suggestedChips) >= 2


# ==============================================================================
# 5. Comparison Agent: Matrix & Zero-Hallucination Gap Isolation & Tail Question
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_comparison_agent_matrix_and_tail_question():
    """Verify matrix synthesis, gap isolation (isGap: true), and 3-hop tail question traversal."""
    async with async_session_factory() as session:
        # 1. Generate Matrix
        rows = await comparison_agent.generate_matrix(
            concept_a_id="concept-tcb",
            concept_b_id="concept-mrmuf",
            selected_axes=["thermal", "defects"],
            custom_axes=["초미세 피치 접합 수율"],
            constraints=None,
            db=session
        )
        assert len(rows) >= 3
        # Zero-Hallucination Gap Isolation Check
        has_gap = any(r.isGap is True for r in rows)
        assert has_gap is True, "Must isolate unverified metrics with isGap: True"

        # 2. Answer Tail Question
        mock_sess = ComparisonSessionModel(
            id="test-comp-session-001",
            title="TCB vs MR-MUF",
            user_id="EMP-TEST",
            query="TCB vs MR-MUF",
            snapshots=[]
        )
        tail_resp = await comparison_agent.answer_tail_question(
            session=mock_sess,
            query="16단 적층 시 다이 휨이 발생하는 구체적 원인은?",
            step_index=2,
            db=session
        )
        assert len(tail_resp.causalPath) >= 3
        assert len(tail_resp.chainSteps) == 3
        assert tail_resp.compensatingProposal is not None
        assert "보상 파라미터" in tail_resp.compensatingProposal or "진동" in tail_resp.compensatingProposal


# ==============================================================================
# 6. Advisor Agent: Safety Margin (422) & Compensating Parameters
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_advisor_agent_safety_margins():
    """Verify process safety margins (422 on >300°C, >200N) and compensating recommendations."""
    from fastapi import HTTPException

    async with async_session_factory() as session:
        # 1. Out of Bounds Force (250N > 200N limit) -> 422
        with pytest.raises(HTTPException) as excinfo:
            await advisor_agent.run_tuning_advisor(
                session_id="sess-20261016-001",
                user_prompt="본딩 압력을 250N으로 올려서 접합 시간을 줄이고 싶습니다.",
                apply_compensation=None,
                manual_conditions={"bonding_force": 250},
                db=session
            )
        assert excinfo.value.status_code == 422
        assert excinfo.value.detail["code"] == "SAFETY_MARGIN_VIOLATION"

        # 2. Normal Tuning Request -> Plan A & Plan B
        advisor_resp = await advisor_agent.run_tuning_advisor(
            session_id="sess-20261016-001",
            user_prompt="저가압 145N 장비 한계에서 보이드 발생을 막으려면?",
            apply_compensation=None,
            manual_conditions=None,
            db=session
        )
        assert advisor_resp.userPrompt == "저가압 145N 장비 한계에서 보이드 발생을 막으려면?"
        rec = advisor_resp.advisorRecommendation
        assert "compensationA" in rec
        assert "compensationB" in rec
        assert "보상 파라미터" in rec["compensationA"]["name"]


# ==============================================================================
# 7. Directive Agent: "전문가 사유" Preservation & Integrity Metrics
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_directive_agent_expert_reason_preservation():
    """⚠️ CRITICAL: Verify that '전문가 사유' is NOT blocked and properly preserved."""
    async with async_session_factory() as session:
        ticket = await session.get(ReviewTicketModel, "ticket-20261016-001")
        if not ticket:
            ticket = ReviewTicketModel(
                id="ticket-20261016-001",
                concept_id="concept-tcb",
                concept_title="열압착 본딩 (TCB)",
                title="TCB 가압 조건 개정안",
                review_type="파라미터 수정",
                author="수석엔지니어",
                current_content="초기 TCB 규격 초안",
                ai_merged_draft="초기 TCB 규격 초안",
                integrity_report={}
            )
            session.add(ticket)
            await session.commit()

        # Directive containing "전문가 사유"
        directive_text = "전문가 사유에 따라 다단 칩 적층 시 계면 전단응력 완화 규격 보강"
        override_reason = "현장 전문가 사유 및 파일럿 실측치 기반"

        directive_resp = await directive_agent.apply_directive(
            ticket=ticket,
            directive_text=directive_text,
            override_reason=override_reason,
            target_layer="hybrid",
            db=session
        )

        assert directive_resp.ticketId == ticket.id
        assert "<mark class=\"diff-added\">" in directive_resp.revisedDraft
        assert "[E-01]" in directive_resp.revisedDraft
        # Integrity Metrics
        assert directive_resp.integrityReport["evidenceMatchRate"] == 1.0
        assert directive_resp.integrityReport["hasOntologyConflict"] is False
        assert ticket.override_reason == override_reason


# ==============================================================================
# 8. Deep Research Agent: Whitelist Synthesis & KnowledgeCandidates
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_deep_research_synthesis():
    """Verify Deep Research synthesis, consensus/tension report, and candidates."""
    async with async_session_factory() as session:
        mock_res_sess = ResearchSessionModel(
            id="res-test-m5-001",
            search_topic="차세대 유리기판 TGV 공정 및 물성 표준 규격"
        )
        synth_res = await deep_research_agent.synthesize(
            session=mock_res_sess,
            selected_evidence_ids=["E-RES-01", "E-RES-02"],
            db=session
        )
        assert "report" in synth_res
        assert "candidates" in synth_res
        assert len(synth_res["candidates"]) == 3
        assert any(c["candidateType"] == "new_concept" for c in synth_res["candidates"])


# ==============================================================================
# 9. Explainer Agent: Guardrail & 1-Hop Connected Concepts
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_explainer_agent_guardrail():
    """Verify that explanation strictly begins with '현재 공정 맥락({parentName}):'."""
    async with async_session_factory() as session:
        resp = await explainer_agent.get_explanation(
            child_id="concept-mrmuf",
            parent_id="concept-tcb",
            perspective_id="default",
            db=session
        )
        assert resp.childConceptId == "concept-mrmuf"
        assert resp.parentConceptId == "concept-tcb"
        # Strict Guardrail Check
        guardrail_prefix = f"현재 공정 맥락({resp.parentConceptName}):"
        assert resp.contextualExplanation.startswith(guardrail_prefix), (
            f"Explanation must start with '{guardrail_prefix}', got: '{resp.contextualExplanation}'"
        )


# ==============================================================================
# 10. Security & RBAC: Tier 3 Data Masking & Access Requests
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_rbac_and_masking():
    """Verify Tier 3 data masking for line_engineer, clear view for chief_reviewer, and access requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. line_engineer role -> isMasked: True
        res_le = await ac.get("/api/v1/concepts/concept-tcb", headers={"X-User-Role": "line_engineer"})
        assert res_le.status_code == 200
        data_le = res_le.json()
        perspectives_le = data_le.get("perspectives", [])
        if perspectives_le:
            p = perspectives_le[0]
            assert p["isMasked"] is True
            assert p["relativeTrend"] is not None
            assert any(s["value"] == "[🔒 대외비 마스킹]" for s in p["specifications"])

        # 2. chief_reviewer role -> isMasked: False
        res_cr = await ac.get("/api/v1/concepts/concept-tcb", headers={"X-User-Role": "chief_reviewer"})
        assert res_cr.status_code == 200
        data_cr = res_cr.json()
        perspectives_cr = data_cr.get("perspectives", [])
        if perspectives_cr:
            p = perspectives_cr[0]
            assert p["isMasked"] is False

        # 3. Access Request Endpoint
        req_body = {
            "conceptId": "concept-tcb",
            "perspectiveId": "persp-tcb-01",
            "reason": "16단 HBM 라인 긴급 불량 분석을 위한 수율 및 압력 절대치 열람 신청"
        }
        res_req = await ac.post("/api/v1/security/access-requests", json=req_body, headers={"X-User-Role": "line_engineer"})
        assert res_req.status_code == 200
        assert res_req.json()["status"] in ["submitted", "pending_approval"]


# ==============================================================================
# 11. WORM Audit Log: Merkle Chain Verification
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_audit_merkle_chain_integrity():
    """Verify SHA-256 Merkle chain integrity on WORM Audit Logs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/system/audit/verify-integrity")
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["totalVerifiedLogs"] >= 0
        assert "merkleRootHash" in data


# ==============================================================================
# 12. Chatbot SSE Streaming Endpoint
# ==============================================================================
@pytest.mark.asyncio
async def test_milestone5_chatbot_sse_streaming():
    """Verify POST /api/v1/chatbot/messages/stream SSE streaming responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "message": "TCB와 MR-MUF의 핵심 차이점을 한 문장으로 요약해줘",
            "conceptId": "concept-tcb"
        }
        res = await ac.post("/api/v1/chatbot/messages/stream", json=payload)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        text_content = res.text
        assert "data: " in text_content
        assert "event: done" in text_content
