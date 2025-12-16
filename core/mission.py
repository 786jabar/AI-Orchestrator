from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import uuid


class MissionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    HALTED = "HALTED"


@dataclass
class MissionRecord:
    mission_id: str
    goal: str
    status: MissionStatus = MissionStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CoreMission:
    goal: str = ""
    mission_id: str = ""
    status: MissionStatus = MissionStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    _store: Dict[str, MissionRecord] = field(default_factory=dict, repr=False)

    def define_mission(self, goal: str) -> str:
        self.goal = goal
        if not self.mission_id:
            self.mission_id = f"m_{uuid.uuid4().hex[:8]}"
        self.status = MissionStatus.PENDING
        self._store[self.mission_id] = MissionRecord(mission_id=self.mission_id, goal=self.goal)
        return self.mission_id

    def get_mission(self, mission_id: str) -> Optional[MissionRecord]:
        return self._store.get(mission_id)
