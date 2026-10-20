"""4-Tier LLM Gateway for Semiconductor Ontology AI Agents.

Orchestrates:
1. Tier 1: Fast Cloud LLM (gpt-4o-mini / gemini-flash) for latency-critical 0ms inline popovers.
2. Tier 2: Deep Reasoning Cloud LLM (gpt-4o / gemini-pro) for comparison matrices, tuning, & governance patch.
3. Tier 3: On-Premise Air-Gapped Local LLM (vLLM / Ollama) with DLP Tokenization for top-secret fab recipes.
4. Tier 4: Deterministic Ontology Inference Engine (SQLite CTE & math formulas) for zero-AI fallback.
"""
import time
import json
import logging
from typing import Optional, Dict, Any, Literal, List
import httpx

from backend.app.core.config import settings
from backend.app.core.circuit_breaker import circuit_breaker
from backend.app.core.dlp_tokenizer import dlp_tokenizer

logger = logging.getLogger("llm_gateway")


class LLMGateway:
    def __init__(self, default_timeout_sec: float = 8.0):
        self.default_timeout_sec = default_timeout_sec

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        session_id: str = "default",
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        tier: Literal["tier1_fast", "tier2_reasoning", "tier3_local"] = "tier1_fast",
        model_override: Optional[str] = None,
        timeout_sec: Optional[float] = None
    ) -> Optional[str]:
        """Calls 4-Tier AI models with DLP tokenization, active failover, and zero-AI fallback.
        
        Returns None if all AI providers fail or circuit is open, triggering Tier 4 Deterministic Fallback.
        """
        # 1. 서킷 브레이커 상태 확인 (Tier 1 & Tier 2 클라우드 호출 시)
        if tier != "tier3_local" and not circuit_breaker.can_execute():
            logger.info("Circuit breaker is OPEN/BLOCKED. Falling back to Tier 4 Deterministic Engine.")
            return None

        # 2. 구간 인지형 가명화 (DLP Tokenization)
        tokenized_prompt, _ = dlp_tokenizer.tokenize(prompt, session_id=session_id)

        # 3. Tier 3: 사내 에어갭 폐쇄망 로컬 LLM 분기
        if tier == "tier3_local":
            if getattr(settings, "ENABLE_LOCAL_LLM", False):
                local_res = await self._call_local_llm(
                    prompt=tokenized_prompt,
                    system_prompt=system_instruction,
                    base_url=settings.TIER3_LOCAL_URL,
                    model=settings.TIER3_LOCAL_MODEL,
                    timeout=timeout_sec or 20.0
                )
                if local_res:
                    return dlp_tokenizer.detokenize(local_res, session_id=session_id)
            logger.info("[Tier 3 Air-Gapped] Local LLM disabled or unreachable. Transitioning to Tier 4 Deterministic Engine.")
            return None

        # 4. Tier 1 & Tier 2: API Key 확인
        active_gemini_key = gemini_key or settings.GEMINI_API_KEY
        active_openai_key = openai_key or settings.OPENAI_API_KEY

        if not active_gemini_key and not active_openai_key:
            return None

        # 5. 티어별 모델 및 페일오버 체인 구성
        # Tier 1 (Fast): gpt-4o-mini (5s) -> gemini-flash (5s)
        # Tier 2 (Reasoning): gpt-4o (30s) -> gpt-4o-mini (10s) -> gemini-pro (20s)
        provider_chain: List[Dict[str, Any]] = []

        if tier == "tier1_fast":
            timeout_1 = timeout_sec or 5.0
            primary_model = model_override or settings.TIER1_MODEL
            if active_openai_key:
                provider_chain.append({"provider": "openai", "key": active_openai_key, "model": primary_model, "timeout": timeout_1})
            if active_gemini_key:
                provider_chain.append({"provider": "gemini", "key": active_gemini_key, "model": "gemini-2.5-flash", "timeout": timeout_1})
        else:  # tier2_reasoning
            timeout_2 = timeout_sec or 30.0
            primary_model = model_override or settings.TIER2_MODEL
            if active_openai_key:
                provider_chain.append({"provider": "openai", "key": active_openai_key, "model": primary_model, "timeout": timeout_2})
                # OpenAI Tier 2 모델 실패 시 경량 모델로 1차 완화 재시도
                if primary_model != settings.TIER1_MODEL:
                    provider_chain.append({"provider": "openai", "key": active_openai_key, "model": settings.TIER1_MODEL, "timeout": 10.0})
            if active_gemini_key:
                provider_chain.append({"provider": "gemini", "key": active_gemini_key, "model": "gemini-2.5-pro", "timeout": 20.0})

        start_time = time.time()
        response_text = None
        used_meta = None

        # 🌟 Active Failover: 체인 순차 실행
        for candidate in provider_chain:
            prov = candidate["provider"]
            key = candidate["key"]
            m_name = candidate["model"]
            t_limit = candidate["timeout"]

            try:
                if prov == "openai":
                    response_text = await self._call_openai(tokenized_prompt, system_instruction, key, model=m_name, timeout=t_limit)
                elif prov == "gemini":
                    response_text = await self._call_gemini(tokenized_prompt, system_instruction, key, model=m_name, timeout=t_limit)

                if response_text and response_text.strip():
                    used_meta = f"{prov}:{m_name}"
                    logger.info(f"[LLM Gateway] Success with {tier} -> {used_meta}")
                    break
                else:
                    logger.warning(f"[LLM Gateway] Candidate {prov}:{m_name} failed. Attempting failover...")
            except (httpx.TimeoutException, httpx.RequestError) as e:
                logger.warning(f"[LLM Gateway] Candidate {prov}:{m_name} network error: {e}. Attempting failover...")
            except Exception as e:
                logger.error(f"[LLM Gateway] Candidate {prov}:{m_name} unexpected error: {e}. Attempting failover...")

        duration_ms = (time.time() - start_time) * 1000

        if response_text:
            await circuit_breaker.record_call(success=True, duration_ms=duration_ms)
            detokenized = dlp_tokenizer.detokenize(response_text, session_id=session_id)
            return detokenized
        else:
            logger.warning(f"[LLM Gateway] All AI candidates failed for {tier}. Activating Tier 4 Deterministic Fallback.")
            await circuit_breaker.record_call(success=False, duration_ms=duration_ms)
            return None

    async def _call_gemini(self, prompt: str, system_prompt: Optional[str], api_key: str, model: str = "gemini-2.5-flash", timeout: float = 8.0) -> Optional[str]:
        """Calls Google Gemini REST API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text[:200]}")
                return None

    async def _call_openai(self, prompt: str, system_prompt: Optional[str], api_key: str, model: str = "gpt-4o-mini", timeout: float = 8.0) -> Optional[str]:
        """Calls OpenAI Chat Completion REST API."""
        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                logger.warning(f"OpenAI API ({model}) returned status {resp.status_code}: {resp.text[:200]}")
                return None

    async def _call_local_llm(self, prompt: str, system_prompt: Optional[str], base_url: str, model: str = "qwen2.5:7b", timeout: float = 15.0) -> Optional[str]:
        """Calls On-Premise Air-Gapped vLLM / Ollama REST API (OpenAI Compatible)."""
        url = f"{base_url.rstrip('/')}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"Tier 3 Local LLM call failed ({url}): {e}")
        return None


# 전역 싱글톤 LLM 게이트웨이
llm_gateway = LLMGateway()
