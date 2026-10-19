"""Regime-Aware Tokenization and Detokenization (DLP) Pipeline.

Strictly adheres to Section 5.4.3 of backend_architecture_specification.md:
- Preserves physical non-linear regimes while obfuscating proprietary trade secrets.
- Replaces raw values with structured tokens: e.g. [TEMP_REGIME_SOLDER_PEAK: 0.60]
- Session-based ephemeral dictionary (TTL 10 minutes) for bidirectional detokenization.
"""
import re
import time
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger("dlp_tokenizer")


class RegimeAwareTokenizer:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        # session_id -> { token: original_text, "expire_at": float }
        self._ephemeral_sessions: Dict[str, Dict[str, str]] = {}

    def _cleanup_expired(self):
        now = time.time()
        expired = [sid for sid, s in self._ephemeral_sessions.items() if s.get("_expire_at", 0) < now]
        for sid in expired:
            del self._ephemeral_sessions[sid]

    def tokenize(self, text: str, session_id: str = "default") -> Tuple[str, Dict[str, str]]:
        """Tokenizes sensitive physical engineering numbers into regime tokens."""
        if not text:
            return text, {}

        self._cleanup_expired()
        token_map: Dict[str, str] = {}
        processed = text

        # 1. 온도 (Temperature): e.g. 280°C, 285℃, -60℃, 85°C
        def replace_temp(match):
            val_str = match.group(1)
            unit = match.group(2)
            try:
                val = float(val_str)
                # 정규화 계수 (0~500도 스케일)
                normalized = round(max(0.0, min(1.0, (val + 100) / 600)), 2)
            except ValueError:
                normalized = 0.50
            token = f"[TEMP_REGIME_PEAK: {normalized:.2f}]"
            token_map[token] = f"{val_str}{unit}"
            return token

        processed = re.sub(r'(-?\d+(?:\.\d+)?)\s*(°C|℃)', replace_temp, processed)

        # 2. 하중/압력 (Force / Load): e.g. 150N, 145N, 180N
        def replace_force(match):
            val_str = match.group(1)
            unit = match.group(2)
            try:
                val = float(val_str)
                normalized = round(max(0.0, min(1.0, val / 300)), 2)
            except ValueError:
                normalized = 0.50
            token = f"[FORCE_REGIME_LOAD: {normalized:.2f}]"
            token_map[token] = f"{val_str}{unit}"
            return token

        processed = re.sub(r'(\d+(?:\.\d+)?)\s*(N)', replace_force, processed)

        # 3. 압력 (Pressure): e.g. 0.45MPa, 1.5 Torr, 2.4kPa
        def replace_pressure(match):
            val_str = match.group(1)
            unit = match.group(2)
            token = f"[PRESSURE_REGIME_LEVEL: {val_str}]"
            token_map[token] = f"{val_str}{unit}"
            return token

        processed = re.sub(r'(\d+(?:\.\d+)?)\s*(MPa|Torr|kPa|Pa)', replace_pressure, processed)

        # 4. 수율 / 결함률 (Yield / Defect %): e.g. 94.2%, 0.1%, 4.2%
        def replace_pct(match):
            val_str = match.group(1)
            try:
                val = float(val_str)
                normalized = round(val / 100.0, 3)
            except ValueError:
                normalized = 0.50
            token = f"[RATIO_REGIME_METRIC: {normalized:.3f}]"
            token_map[token] = f"{val_str}%"
            return token

        processed = re.sub(r'(\d+(?:\.\d+)?)\s*%', replace_pct, processed)

        # 5. 시간 (Duration): e.g. 2.2s, 350ms, 12s
        def replace_time(match):
            val_str = match.group(1)
            unit = match.group(2)
            token = f"[TIME_REGIME_DURATION: {val_str}_{unit}]"
            token_map[token] = f"{val_str}{unit}"
            return token

        processed = re.sub(r'(\d+(?:\.\d+)?)\s*(ms|s|sec)', replace_time, processed)

        # 6. 미세 치수 (Dimensions): e.g. 30㎛, 25㎛, 10μm, 8nm
        def replace_dim(match):
            val_str = match.group(1)
            unit = match.group(2)
            token = f"[DIM_REGIME_SCALE: {val_str}_{unit}]"
            token_map[token] = f"{val_str}{unit}"
            return token

        processed = re.sub(r'(\d+(?:\.\d+)?)\s*(㎛|μm|nm|mm)', replace_dim, processed)

        # 세션 임시 사전에 저장
        now = time.time()
        if session_id not in self._ephemeral_sessions:
            self._ephemeral_sessions[session_id] = {}
        self._ephemeral_sessions[session_id].update(token_map)
        self._ephemeral_sessions[session_id]["_expire_at"] = now + self.ttl_seconds

        return processed, token_map

    def detokenize(self, text: str, session_id: str = "default") -> str:
        """Restores regime tokens back to original engineering numbers."""
        if not text:
            return text

        session_map = self._ephemeral_sessions.get(session_id, {})
        result = text
        for token, orig in session_map.items():
            if token.startswith("_"):
                continue
            result = result.replace(token, orig)
        return result


# 전역 싱글톤 가명화 엔진
dlp_tokenizer = RegimeAwareTokenizer()
