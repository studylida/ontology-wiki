"""Bounded local CrossEncoder calls in a separately installed Python runtime."""
from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
from time import monotonic
from uuid import uuid4

from knowledge.core.errors import AppError


def _worker_environment() -> dict[str, str]:
    # Inference is offline and the child receives no provider or login secrets.
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
    env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", HF_HUB_OFFLINE="1",
               TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
               TOKENIZERS_PARALLELISM="false")
    return env


class LocalCrossEncoderReranker:
    def __init__(self, python_path: str, model: str, revision: str, *,
                 timeout_seconds: float = 120, device: str = "cpu", max_length: int = 1024,
                 batch_size: int = 4):
        self.python_path, self.model, self.revision = python_path, model, revision
        self.timeout_seconds, self.device = timeout_seconds, device
        self.max_length, self.batch_size = max_length, batch_size
        self._process = None
        self._lock = asyncio.Lock()
        self._ready = None
        if timeout_seconds <= 0 or max_length < 32 or batch_size < 1 or device not in ("cpu", "cuda"):
            raise ValueError("Invalid reranker execution settings")

    @property
    def profile(self) -> dict:
        return {"kind": "cross_encoder", "model": self.model, "revision": self.revision,
                "device": self.device, "dtype": "float16" if self.device == "cuda" else "float32",
                "maxLength": self.max_length, "batchSize": self.batch_size}

    async def _stop(self):
        process, self._process = self._process, None
        self._ready = None
        if process is not None:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            await process.wait()

    async def aclose(self):
        async with self._lock:
            await self._stop()

    async def _read(self):
        line = await self._process.stdout.readline()
        if not line:
            raise AppError(503, "RERANKER_UNAVAILABLE", "재정렬 프로세스가 종료됐습니다.")
        try:
            data = json.loads(line)
        except (ValueError, UnicodeDecodeError) as exc:
            raise AppError(502, "RERANKER_CONTRACT_ERROR", "재정렬 응답 형식이 올바르지 않습니다.") from exc
        if not isinstance(data, dict) or data.get("error"):
            raise AppError(503, "RERANKER_FAILED", "로컬 재정렬 모델을 실행하지 못했습니다.")
        return data

    async def _start(self):
        if self._process is not None and self._process.returncode is None:
            return False
        if not Path(self.python_path).is_file() or not Path(self.model).is_dir():
            raise AppError(503, "RERANKER_CONFIGURATION", "재정렬 실행 환경과 다운로드한 모델을 확인하세요.")
        worker = Path(__file__).with_name("rerank_worker.py")
        self._process = await asyncio.create_subprocess_exec(
            str(Path(self.python_path).resolve()), "-u", str(worker),
            "--model", str(Path(self.model).resolve()), "--device", self.device,
            "--max-length", str(self.max_length), "--batch-size", str(self.batch_size),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL, env=_worker_environment(), limit=1024 * 1024,
            **({"creationflags": 0x08000000} if os.name == "nt" else {}))
        self._ready = await self._read()
        if self._ready.get("ready") is not True or self._ready.get("device") != self.device:
            raise AppError(502, "RERANKER_CONTRACT_ERROR", "재정렬 모델 준비 상태가 올바르지 않습니다.")
        return True

    async def rerank(self, query: str, hits: list[dict]) -> dict:
        started = monotonic()
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Reranking requires a nonempty query")
        ids = [hit.get("passageId") for hit in hits]
        if any(not isinstance(pid, str) or not pid for pid in ids) or len(ids) != len(set(ids)):
            raise ValueError("Reranking requires unique passage IDs")
        if any(not isinstance(hit.get("text"), str) for hit in hits):
            raise ValueError("Reranking requires original passage text")
        if len(hits) > 200 or len(query) + sum(len(h["text"]) for h in hits) > 2_000_000:
            raise ValueError("Reranking input exceeds the bounded candidate budget")
        acquired = False
        try:
            async with asyncio.timeout(self.timeout_seconds):
                await self._lock.acquire()
                acquired = True
                cold_start = await self._start() if hits else False
                request_id = uuid4().hex
                data = {"scores": [], "inferenceMs": 0, "truncatedPairs": 0, "totalPairs": 0,
                        "inputTokens": 0, "processedTokens": 0}
                if hits:
                    payload = {"id": request_id, "query": query, "texts": [hit["text"] for hit in hits]}
                    self._process.stdin.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
                    await self._process.stdin.drain()
                    data = await self._read()
                    if data.get("id") != request_id:
                        raise AppError(502, "RERANKER_CONTRACT_ERROR", "재정렬 요청과 응답이 일치하지 않습니다.")
                scores = data.get("scores")
                if not isinstance(scores, list) or len(scores) != len(hits) or any(
                    isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score)
                    for score in scores):
                    raise AppError(502, "RERANKER_CONTRACT_ERROR", "재정렬 점수의 개수나 값이 올바르지 않습니다.")
                ranked = [{**hit, "rerankScore": float(score),
                           "methods": list(dict.fromkeys([*hit.get("methods", []), "cross_encoder"]))}
                          for hit, score in zip(hits, scores)]
                ranked.sort(key=lambda hit: -hit["rerankScore"])
                return {"hits": ranked, "profile": self.profile, "elapsedMs": round((monotonic() - started) * 1000, 2),
                        "inferenceMs": data["inferenceMs"], "coldStart": cold_start,
                        "runtime": self._ready.get("runtime", {}) if self._ready else {},
                        "gpuPeakMemoryMiB": data.get("gpuPeakMemoryMiB"),
                        "modelLoadMs": self._ready.get("modelLoadMs") if cold_start else 0,
                        "truncatedPairs": data["truncatedPairs"], "totalPairs": data["totalPairs"],
                        "inputTokens": data["inputTokens"], "processedTokens": data["processedTokens"],
                        "usage": {"source": "local", "providerCalls": 0, "providerCostUsd": 0,
                                  "localHardwareCostUsd": None}}
        except TimeoutError as exc:
            if acquired:
                await self._stop()
            raise AppError(504, "RERANKER_TIMEOUT", "재정렬 실행 시간 한도를 초과했습니다.") from exc
        except (Exception, asyncio.CancelledError):
            if acquired:
                await self._stop()
            raise
        finally:
            if acquired:
                self._lock.release()
