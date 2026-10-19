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
    def __init__(self, timeout_sec: float = 3.0):
        self.timeout_sec = timeout_sec

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        session_id: str = "default",
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        preferred_provider: str = "gemini"
    ) -> Optional[str]:
        """Calls external LLM with DLP tokenization, circuit-breaker safety, and fallback.
        
        Returns None if circuit is open, timeout occurs, or no valid key is provided,
        prompting the caller agent to use its deterministic ontology fallback.
        """
        # 1. 서킷 브레이커 상태 확인
        if not circuit_breaker.can_execute():
            logger.info("Circuit breaker is OPEN/BLOCKED. Returning None for deterministic fallback.")
            return None

        # 2. API Key 확인
        active_gemini_key = gemini_key or settings.GEMINI_API_KEY
        active_openai_key = openai_key or settings.OPENAI_API_KEY

        if not active_gemini_key and not active_openai_key:
            # 키 미등록 시 즉시 정적 결정론적 폴백 유도
            return None

        # 3. 구간 인지형 가명화 (DLP Tokenization)
        tokenized_prompt, _ = dlp_tokenizer.tokenize(prompt, session_id=session_id)

        start_time = time.time()
        try:
            response_text = None
            if active_gemini_key and (preferred_provider == "gemini" or not active_openai_key):
                response_text = await self._call_gemini(tokenized_prompt, system_instruction, active_gemini_key)
            elif active_openai_key:
                response_text = await self._call_openai(tokenized_prompt, system_instruction, active_openai_key)

            duration_ms = (time.time() - start_time) * 1000

            if response_text:
                # 서킷 브레이커 성공 기록
                await circuit_breaker.record_call(success=True, duration_ms=duration_ms)
                # 4. 역치환 (Detokenization)
                detokenized = dlp_tokenizer.detokenize(response_text, session_id=session_id)
                return detokenized
            else:
                await circuit_breaker.record_call(success=False, duration_ms=duration_ms)
                return None

        except (httpx.TimeoutException, httpx.RequestError) as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.warning(f"LLM Gateway call timed out or network error ({duration_ms:.0f}ms): {e}")
            await circuit_breaker.record_call(success=False, duration_ms=duration_ms)
            return None
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"LLM Gateway unexpected error: {e}")
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
