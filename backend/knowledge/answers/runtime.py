"""Only live cancellation/notification state is local. Replay comes from PostgreSQL."""
import asyncio
from dataclasses import dataclass, field
from time import monotonic
from uuid import uuid4
from .states import TERMINAL


@dataclass
class RunRuntime:
    run_id: str
    epoch: str
    status: str = 'accepted'
    task: asyncio.Task | None = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    changed: asyncio.Event = field(default_factory=asyncio.Event)
    write_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    text: str = ''
    citations: list = field(default_factory=list)
    source_ids: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    pending: list = field(default_factory=list)
    pending_chars: int = 0
    last_flush: float = field(default_factory=monotonic)
    storage_failed: bool = False
    shutdown: bool = False


class RunRegistry:
    def __init__(self):
        self.epoch = uuid4().hex
        self.runs = {}

    def get(self, run_id):
        return self.runs.get(run_id)

    def add(self, run_id):
        for key, value in list(self.runs.items()):
            if len(self.runs) < 256:
                break
            if value.task is not None and value.task.done():
                self.runs.pop(key)
        if len(self.runs) >= 256:
            from knowledge.core.errors import AppError
            raise AppError(503, 'answer_capacity', '진행 중인 답변이 많습니다. 잠시 후 다시 시도해 주세요.', retryable=True)
        runtime = RunRuntime(run_id, self.epoch)
        self.runs[run_id] = runtime
        return runtime

    async def close(self):
        active = [r for r in self.runs.values() if r.task is not None and not r.task.done()]
        for runtime in active:
            runtime.shutdown = True
            runtime.cancel_event.set()
            runtime.task.cancel()
        if active:
            await asyncio.gather(*(r.task for r in active), return_exceptions=True)
