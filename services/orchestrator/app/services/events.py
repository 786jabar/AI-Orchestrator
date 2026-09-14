from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PlatformEvent:
    type: str
    project_id: int
    payload: dict[str, Any] = field(default_factory=dict)
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventBus:
    """In-process pub/sub for live pipeline / agent updates (SSE)."""

    def __init__(self) -> None:
        self._subs: dict[int, list[asyncio.Queue[PlatformEvent]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event: PlatformEvent) -> None:
        async with self._lock:
            queues = list(self._subs.get(event.project_id, []))
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, project_id: int) -> AsyncIterator[PlatformEvent]:
        q: asyncio.Queue[PlatformEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subs[project_id].append(q)
        try:
            yield PlatformEvent(
                type="subscribed",
                project_id=project_id,
                payload={"message": "live stream connected"},
            )
            while True:
                event = await q.get()
                yield event
        finally:
            async with self._lock:
                if q in self._subs[project_id]:
                    self._subs[project_id].remove(q)


event_bus = EventBus()
