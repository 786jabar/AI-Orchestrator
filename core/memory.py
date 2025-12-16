from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class OutcomeType(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    HALT = "HALT"


@dataclass
class MemoryEntry:
    text: str
    meta: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def content(self) -> str:
        return self.text


@dataclass
class ProjectState:
    mission_id: str
    goal: str


class MemorySystem:
    def __init__(self) -> None:
        self.working: Dict[str, Any] = {}
        self.projects: Dict[str, ProjectState] = {}
        self.episodic: List[MemoryEntry] = []
        self.reflections: List[MemoryEntry] = []
        self.semantic: List[MemoryEntry] = []

    def initialize_project(self, project_id: str, goal: str) -> ProjectState:
        ps = ProjectState(mission_id=project_id, goal=goal)
        self.projects[project_id] = ps
        return ps

    def add_episode(self, text: str, **meta: Any) -> None:
        self.episodic.append(MemoryEntry(text=text, meta=dict(meta)))

    def add_reflection(self, text: str, **meta: Any) -> None:
        self.reflections.append(MemoryEntry(text=text, meta=dict(meta)))

    def add_semantic(self, text: str, embedding: Optional[List[float]] = None, **meta: Any) -> None:
        m = dict(meta)
        if embedding is not None:
            m["embedding"] = embedding
        self.semantic.append(MemoryEntry(text=text, meta=m))

    def add_semantic_fact(self, project_id: str, fact: str) -> None:
        self.add_semantic(fact, project_id=project_id)

    def semantic_search(self, query: str, top_k: int = 5, limit: Optional[int] = None) -> List[MemoryEntry]:
        k = limit if limit is not None else top_k
        q = (query or "").lower().split()
        if not q:
            return self.semantic[:k]

        def score(entry: MemoryEntry) -> int:
            t = entry.text.lower()
            return sum(1 for w in q if w in t)

        ranked = sorted(self.semantic, key=score, reverse=True)
        return [e for e in ranked if score(e) > 0][:k]
