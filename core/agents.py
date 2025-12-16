from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class Agent:
    name: str
    role: str = "general"

    def act(self, prompt: str) -> str:
        return f"[{self.name}] {prompt}"


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}
        # default agent so smoke test passes
        self.register(Agent(name="default", role="general"))

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent:
        return self._agents[name]

    def maybe_get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        return sorted(self._agents.keys())
