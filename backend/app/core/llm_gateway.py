"""LLM Gateway for Semiconductor Ontology AI Agents.

Orchestrates:
1. Circuit Breaker protection (CLOSED / OPEN / HALF_OPEN)
2. Regime-Aware Tokenization & Detokenization (DLP)
3. Multi-Provider routing (Google Gemini / OpenAI)
4. Graceful Degradation to deterministic ontology inference when offline or circuit-open.
"""
import time
import json
import logging
from typing import Optional, Dict, Any
import httpx

from backend.app.core.config import settings
from backend.app.core.circuit_breaker import circuit_breaker, CircuitState
from backend.app.core.dlp_tokenizer import dlp_tokenizer

logger = logging.getLogger("llm_gateway")


class LLMGateway:
    def __init__(self, timeout_sec: float = 8.0):
        self.timeout_sec = timeout_sec

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        session_id: str = "default",
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        preferred_provider: Optional[str] = None
    ) -> Optional[str]:
        """Calls external LLM with DLP tokenization, active failover, circuit-breaker safety, and fallback.
        
        Failover Strategy:
        1. Both Alive: Executes preferred provider (default: OpenAI gpt-4o-mini).
        2. One Dead: Automatically cross-fails over to the surviving provider (e.g. Gemini or OpenAI).
        3. Both Dead: Returns None to trigger local deterministic ontology inference engine.
        """
        # 1. 서킷 브레이커 상태 확인
        if not circuit_breaker.can_execute():
            logger.info("Circuit breaker is OPEN/BLOCKED. Returning None for deterministic fallback.")
            return None

        # 2. API Key 확인
        active_gemini_key = gemini_key or settings.GEMINI_API_KEY
        active_openai_key = openai_key or settings.OPENAI_API_KEY

        if not active_gemini_key and not active_openai_key:
            return None

        # 3. 우선순위 결정 (Active Failover Chain 구성)
        pref = (preferred_provider or getattr(settings, "PREFERRED_LLM_PROVIDER", "openai")).lower()
        provider_chain = []
        if pref == "openai":
            if active_openai_key:
                provider_chain.append(("openai", active_openai_key))
            if active_gemini_key:
                provider_chain.append(("gemini", active_gemini_key))
        else:
            if active_gemini_key:
                provider_chain.append(("gemini", active_gemini_key))
            if active_openai_key:
                provider_chain.append(("openai", active_openai_key))

        if not provider_chain:
            return None

        # 4. 구간 인지형 가명화 (DLP Tokenization)
        tokenized_prompt, _ = dlp_tokenizer.tokenize(prompt, session_id=session_id)

        start_time = time.time()
        response_text = None
        used_provider = None

        # 🌟 Active Failover: 1순위 실패 시 2순위로 즉시 교차 재시도
        for prov_name, key in provider_chain:
            try:
                if prov_name == "openai":
                    response_text = await self._call_openai(tokenized_prompt, system_instruction, key)
                elif prov_name == "gemini":
                    response_text = await self._call_gemini(tokenized_prompt, system_instruction, key)

                if response_text and response_text.strip():
                    used_provider = prov_name
                    logger.info(f"[LLM Gateway] Successfully generated text using provider: {prov_name}")
                    break
                else:
                    logger.warning(f"[LLM Gateway] Provider '{prov_name}' failed or returned empty. Switching to next available provider in failover chain.")
            except (httpx.TimeoutException, httpx.RequestError) as e:
                logger.warning(f"[LLM Gateway] Provider '{prov_name}' network/timeout error: {e}. Switching to failover provider.")
            except Exception as e:
                logger.error(f"[LLM Gateway] Provider '{prov_name}' unexpected error: {e}. Switching to failover provider.")

        duration_ms = (time.time() - start_time) * 1000

        if response_text:
            await circuit_breaker.record_call(success=True, duration_ms=duration_ms)
            detokenized = dlp_tokenizer.detokenize(response_text, session_id=session_id)
            return detokenized
        else:
            logger.warning("[LLM Gateway] All available LLM providers failed. Triggering deterministic ontology fallback.")
            await circuit_breaker.record_call(success=False, duration_ms=duration_ms)
            return None

    async def _call_gemini(self, prompt: str, system_prompt: Optional[str], api_key: str) -> Optional[str]:
        """Calls Google Gemini REST API (gemini-2.5-flash / gemini-1.5-flash)."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
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

    async def _call_openai(self, prompt: str, system_prompt: Optional[str], api_key: str) -> Optional[str]:
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
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                logger.warning(f"OpenAI API returned status {resp.status_code}: {resp.text[:200]}")
                return None


# 전역 싱글톤 LLM 게이트웨이
llm_gateway = LLMGateway()
