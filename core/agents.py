from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class Role(str, Enum):
    GENERAL = "general"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    DEBUGGER = "debugger"
    SAFETY = "safety"
    CRITIC = "critic"
    EXECUTIVE = "executive"


@dataclass
class Agent:
    name: str
    role: str = Role.GENERAL.value

    def act(self, prompt: str) -> str:
        return f"[{self.name}] {prompt}"


class AgentRegistry:
    """Minimal registry for smoke tests and orchestration wiring."""
    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}
        # ensure at least one agent exists for smoke tests
        self.register(Agent(name="default", role=Role.GENERAL.value))

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent:
        return self._agents[name]

    def all(self) -> Dict[str, Agent]:
        return dict(self._agents)

    def maybe_get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def list_agents(self):
        return list(self._agents.values())
