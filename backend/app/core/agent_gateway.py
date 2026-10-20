"""Section 6.1: 4-Tier Agent Gateway & Unified Dispatcher.

Provides a unified single gateway function `call_agent(...)` for all domain agents:
1. Tier 1 (Fast Cloud): gpt-4o-mini (5s) for latency-critical inline popovers & chat.
2. Tier 2 (Deep Reasoning): gpt-4o (30s) for comparative tuning, governance patches, & deep research.
3. Tier 3 (Air-Gapped Local): On-premise vLLM / Ollama for top-secret fab recipes.
4. Tier 4 (Deterministic): Local SQLite CTE graph & math formulas for zero-AI fallback.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel

from backend.app.core.llm_gateway import llm_gateway

logger = logging.getLogger("agent_gateway")


class AgentResponse(BaseModel):
    agent_type: str
    status: Literal["success", "fallback", "error"]
    result_text: str
    metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None


async def call_agent(
    agent_type: Literal["explainer", "chatbot", "clarifier", "directive", "advisor", "deep_research", "comparison"],
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None,
    tier: Optional[Literal["tier1_fast", "tier2_reasoning", "tier3_local"]] = None,
    timeout_seconds: Optional[float] = None,
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None
) -> AgentResponse:
    """Unified single 4-Tier gateway function for all domain agents across Tab 1~4 and Chatbot.

    Automatic Tier Classification:
    - explainer, chatbot -> Tier 1 (Fast Cloud LLM, default 5s)
    - comparison, advisor, directive, deep_research, clarifier -> Tier 2 (Deep Reasoning Cloud LLM, default 30s)
    - isSecretRecipe / isTier3 in context -> Tier 3 (Air-Gapped On-Premise Local LLM)
    - AI failure / offline -> Tier 4 (Deterministic Zero-AI Ontology Fallback)
    """
    ctx = context or {}
    session_id = f"{agent_type}-{ctx.get('sessionId') or ctx.get('conceptId') or 'global'}"

    # 1. 4-Tier 계층 자동 판별
    if tier:
        assigned_tier = tier
    elif ctx.get("isSecretRecipe") or ctx.get("isTier3"):
        assigned_tier = "tier3_local"
    elif agent_type in ["explainer", "chatbot"]:
        assigned_tier = "tier1_fast"
    else:
        assigned_tier = "tier2_reasoning"

    # 타임아웃 기본값
    if timeout_seconds is not None:
        effective_timeout = timeout_seconds
    elif assigned_tier == "tier1_fast":
        effective_timeout = 5.0
    else:
        effective_timeout = 30.0

    # Default persona instruction if not provided
    default_instruction = (
        "당신은 글로벌 반도체 첨단 패키징 및 소자 공정 전문 지능형 어시스턴트입니다. "
        "공인 출처 백서와 실제 공정 인과 에지를 기반으로 엄밀하고 정량적인 엔지니어링 답변을 제공하십시오."
    )
    instruction = system_instruction or default_instruction

    try:
        # 🌟 4-Tier LLMGateway 호출
        generated_text = await llm_gateway.generate_text(
            prompt=prompt,
            system_instruction=instruction,
            session_id=session_id,
            gemini_key=gemini_key,
            openai_key=openai_key,
            tier=assigned_tier,
            model_override=model_name,
            timeout_sec=effective_timeout
        )

        if not generated_text or not generated_text.strip():
            logger.warning(f"[{agent_type}] AI returned empty. Triggering Tier 4 Deterministic Fallback.")
            return AgentResponse(
                agent_type=agent_type,
                status="fallback",
                result_text="요청하신 공학적 분석에 대해 Tier 4 온톨로지 결정론적 추론 엔진으로 안전하게 전환되었습니다.",
                metadata={"tier": "tier4_deterministic", "timeout": effective_timeout, "fallback": True}
            )

        return AgentResponse(
            agent_type=agent_type,
            status="success",
            result_text=generated_text.strip(),
            metadata={"tier": assigned_tier, "model": model_name or "auto-tiered", "timeout": effective_timeout}
        )

    except asyncio.TimeoutError:
        logger.error(f"[{agent_type}] Agent call timed out after {effective_timeout}s. Transitioning to Tier 4.")
        return AgentResponse(
            agent_type=agent_type,
            status="fallback",
            result_text=f"지능형 에이전트 분석 시간이 제한선({effective_timeout}초)을 초과하여 Tier 4 온톨로지 규칙으로 보존되었습니다.",
            metadata={"tier": "tier4_deterministic", "timeout": effective_timeout, "reason": "timeout_error"},
            error_message="TIMEOUT_EXCEEDED"
        )
    except Exception as e:
        logger.error(f"[{agent_type}] Unexpected error during agent invocation: {e}", exc_info=True)
        return AgentResponse(
            agent_type=agent_type,
            status="fallback",
            result_text="지능형 에이전트 연동 중 오류로 인해 Tier 4 온톨로지 규칙으로 안전 착륙했습니다.",
            metadata={"tier": "tier4_deterministic", "error": str(e)},
            error_message=str(e)
        )
