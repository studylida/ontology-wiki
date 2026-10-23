"""Circuit Breaker Pattern for Semiconductor Ontology AI Gateway.

Strictly adheres to Section 5.5.2 of backend_architecture_specification.md:
- Sliding Window Size: 20 calls
- Failure Rate Threshold: 50%
- Slow Call Threshold: > 3,000ms (50% threshold)
- Wait Duration in OPEN State: 30 seconds (extends to 60 seconds on repeated probe failure)
- Permitted Calls in HALF_OPEN State: 5 trial probes
- States: CLOSED (🟢 Healthy) | OPEN (🟡 Degraded Fallback) | HALF_OPEN (Trial Probes)
"""
import time
import asyncio
from enum import Enum
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"         # 🟢 정상 가동 (Healthy)
    OPEN = "OPEN"             # 🟡 차단/성능 저하 폴백 (Degraded)
    HALF_OPEN = "HALF_OPEN"   # 복구 시험 가동 (5회 Trial Probes)


class CircuitBreaker:
    def __init__(
        self,
        sliding_window_size: int = 20,
        failure_rate_threshold: float = 0.5,
        slow_call_rate_threshold: float = 0.5,
        slow_call_threshold_ms: float = 3000.0,
        wait_duration_open_sec: float = 30.0,
        permitted_calls_half_open: int = 5
    ):
        self.sliding_window_size = sliding_window_size
        self.failure_rate_threshold = failure_rate_threshold
        self.slow_call_rate_threshold = slow_call_rate_threshold
        self.slow_call_threshold_ms = slow_call_threshold_ms
        self.wait_duration_open_sec = wait_duration_open_sec
        self.permitted_calls_half_open = permitted_calls_half_open

        self._state = CircuitState.CLOSED
        self._window: List[Tuple[bool, bool]] = []  # [(is_success, exceeded_caller_latency_budget)]
        self._state_changed_at = time.time()
        self._half_open_probes = 0
        self._half_open_successes = 0
        self._open_count = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        now = time.time()
        if self._state == CircuitState.OPEN:
            current_wait = self.wait_duration_open_sec * (2 if self._open_count > 1 else 1)
            if now - self._state_changed_at >= current_wait:
                self._state = CircuitState.HALF_OPEN
                self._state_changed_at = now
                self._half_open_probes = 0
                self._half_open_successes = 0
                logger.info(f"CircuitBreaker state transitioned to HALF_OPEN (Trial 5 probes).")
        return self._state

    def can_execute(self) -> bool:
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.HALF_OPEN:
            return self._half_open_probes < self.permitted_calls_half_open
        return False

    async def record_call(self, success: bool, duration_ms: float, slow_call_threshold_ms: Optional[float] = None):
        async with self._lock:
            now = time.time()
            current_state = self.state

            if current_state == CircuitState.HALF_OPEN:
                self._half_open_probes += 1
                if success:
                    self._half_open_successes += 1
                else:
                    # 5회 중 1회라도 실패 시 즉시 OPEN 재전이 (60초 연장)
                    self._state = CircuitState.OPEN
                    self._open_count += 1
                    self._state_changed_at = now
                    logger.warning("CircuitBreaker probe failed in HALF_OPEN -> Re-opened for 60s.")
                    return

                # 5회 전원 성공 시 CLOSED 복구
                if self._half_open_probes >= self.permitted_calls_half_open:
                    if self._half_open_successes == self.permitted_calls_half_open:
                        self._state = CircuitState.CLOSED
                        self._open_count = 0
                        self._window.clear()
                        self._state_changed_at = now
                        logger.info("CircuitBreaker 5 probes succeeded -> Recovered to CLOSED (🟢 Healthy).")
                    else:
                        self._state = CircuitState.OPEN
                        self._open_count += 1
                        self._state_changed_at = now
                return

            if current_state == CircuitState.CLOSED:
                threshold = self.slow_call_threshold_ms if slow_call_threshold_ms is None else slow_call_threshold_ms
                self._window.append((success, duration_ms > threshold))
                if len(self._window) > self.sliding_window_size:
                    self._window.pop(0)

                if len(self._window) >= min(10, self.sliding_window_size):
                    failures = sum(1 for s, _ in self._window if not s)
                    slow_calls = sum(1 for _, is_slow in self._window if is_slow)
                    total = len(self._window)

                    fail_rate = failures / total
                    slow_rate = slow_calls / total

                    if fail_rate >= self.failure_rate_threshold or slow_rate >= self.slow_call_rate_threshold:
                        self._state = CircuitState.OPEN
                        self._open_count = 1
                        self._state_changed_at = now
                        logger.warning(
                            f"CircuitBreaker OPENED: Fail rate={fail_rate:.1%}, Slow rate={slow_rate:.1%} "
                            f"(threshold={self.failure_rate_threshold:.1%}). Fallback active."
                        )

    def force_state(self, state: CircuitState):
        self._state = state
        self._state_changed_at = time.time()
        if state == CircuitState.CLOSED:
            self._window.clear()
            self._open_count = 0

    def get_metrics(self) -> dict:
        return {
            "state": self.state.value,
            "windowSize": len(self._window),
            "openCount": self._open_count,
            "stateAgeSec": round(time.time() - self._state_changed_at, 1)
        }


# 전역 싱글톤 서킷 브레이커
circuit_breaker = CircuitBreaker()
