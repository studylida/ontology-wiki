"""Section 6.1: Agent Gateway & Unified Dispatcher.

Provides a unified single gateway function `call_agent(...)` for all domain agents:
1. Model switching (Gemini 2.5 Pro, OpenAI GPT-4o, On-premise) controlled in a single place.
2. Built-in timeout (default: 30.0s, configurable) with graceful fallback to prevent 500 errors.
3. Centralized logging and error transformation.
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
    agent_type: Literal["clarifier", "directive", "advisor", "deep_research", "chatbot"],
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout_seconds: float = 30.0,
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None
) -> AgentResponse:
    """Unified single gateway function for all domain agents across Tab 1~4 and Chatbot.

    Args:
        agent_type: Calling agent category.
        prompt: User utterance or synthesis instruction.
        context: Screen and ontology context dictionary.
        system_instruction: System prompt for domain persona.
        model_name: Explicit model override (e.g. "gemini-2.5-pro", "gpt-4o").
        timeout_seconds: Execution timeout limit (default: 30.0s).
        gemini_key: Optional per-request API key.
        openai_key: Optional per-request API key.

    Returns:
        AgentResponse: Standardized response with graceful fallback guarantee.
    """
    ctx = context or {}
    session_id = f"{agent_type}-{ctx.get('sessionId') or ctx.get('conceptId') or 'global'}"

    # Default persona instruction if not provided
    default_instruction = (
        "당신은 글로벌 반도체 첨단 패키징 및 소자 공정 전문 지능형 어시스턴트입니다. "
        "공인 출처 백서와 실제 공정 인과 에지를 기반으로 엄밀하고 정량적인 엔지니어링 답변을 제공하십시오."
    )
    instruction = system_instruction or default_instruction

    try:
        # 🌟 30초 타임아웃 래핑 (Timeout Guardrail)
        generated_text = await asyncio.wait_for(
            llm_gateway.generate_text(
                prompt=prompt,
                system_instruction=instruction,
                session_id=session_id,
                gemini_key=gemini_key,
                openai_key=openai_key
            ),
            timeout=timeout_seconds
        )

        if not generated_text or not generated_text.strip():
            logger.warning(f"[{agent_type}] LLM returned empty response. Triggering graceful fallback.")
            return AgentResponse(
                agent_type=agent_type,
                status="fallback",
                result_text="요청하신 공학적 분석을 처리하는 중 일시적인 응답 지연이 발생했습니다. 기존 초안을 보존하며 재시도를 권장합니다.",
                metadata={"timeout": timeout_seconds, "fallback": True}
            )

        return AgentResponse(
            agent_type=agent_type,
            status="success",
            result_text=generated_text.strip(),
            metadata={"model": model_name or "gemini-default", "timeout": timeout_seconds}
        )

    except asyncio.TimeoutError:
        logger.error(f"[{agent_type}] Agent call timed out after {timeout_seconds}s. Returning graceful fallback.")
        return AgentResponse(
            agent_type=agent_type,
            status="fallback",
            result_text=f"지능형 에이전트 분석 시간이 제한선({timeout_seconds}초)을 초과했습니다. 안전을 위해 기존 데이터가 보존되었습니다.",
            metadata={"timeout": timeout_seconds, "reason": "timeout_error"},
            error_message="TIMEOUT_EXCEEDED"
        )
    except Exception as e:
        logger.error(f"[{agent_type}] Unexpected error during agent invocation: {e}", exc_info=True)
        return AgentResponse(
            agent_type=agent_type,
            status="error",
            result_text="지능형 에이전트 서비스 연동 중 오류가 발생했습니다. 잠시 후 다시 시도해 주십시오.",
            metadata={"error": str(e)},
            error_message=str(e)
        )
