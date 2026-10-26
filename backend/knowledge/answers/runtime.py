import asyncio
from dataclasses import dataclass, field
from time import monotonic

from ..core.ids import utcnow


@dataclass
class RunRuntime:
    run_id: str
    message_id: str
    conversation_id: str
    user_message_id: str
    principal: object
    started_clock: float = field(default_factory=monotonic)
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    changed: asyncio.Condition = field(default_factory=asyncio.Condition)
    finish_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cancel_kind: str = "cancelled"
    task: asyncio.Task | None = None
    seq: int = 0
    events: list[dict] = field(default_factory=list)
    pending: list[dict] = field(default_factory=list)
    content: str = ""
    citations: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    source_views: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    usage: dict | None = None
    metrics: dict = field(default_factory=lambda: {"retrievalMs": None, "generationMs": None,
                                                 "providerEventMs": None, "firstTextMs": None, "totalMs": None})
    generation_config: dict = field(default_factory=dict)
    retrieval_run_id: str | None = None
    status: str = "queued"
    finished: bool = False
    storage_error: bool = False
    pending_characters: int = 0
    last_flush: float = field(default_factory=monotonic)

    def make_event(self, kind, data):
        self.seq += 1
        return {"type": kind, "runId": self.run_id, "seq": self.seq,
                "at": utcnow().isoformat(), "data": data}

    async def emit(self, kind, data):
        if self.finished:
            return
        event = self.make_event(kind, data)
        self.pending.append(event)
        self.events.append(event)
        if kind == "text.delta":
            self.pending_characters += len(data["text"])
        await self.notify()

    async def notify(self):
        async with self.changed:
            self.changed.notify_all()

    def revision_ids(self):
        ids = {c["sourceRevisionId"] for c in self.citations if c.get("sourceRevisionId")}
        for card in self.relations + self.source_views:
            ids.update(c["sourceRevisionId"] for c in card.get("evidence", []) if c.get("sourceRevisionId"))
        return sorted(ids)

    def flushed(self):
        self.pending.clear()
        self.pending_characters = 0
        self.last_flush = monotonic()
