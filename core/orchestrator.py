from __future__ import annotations
from dataclasses import dataclass

@dataclass
class OrchestratorPolicy:
    max_tokens: int = 200000
    max_retries: int = 6
    max_retries_total: int = 20
    max_tool_calls: int = 200
    require_plan_approval: bool = False
    require_final_approval: bool = False
    emergency_stop: bool = False


@dataclass
class OrchestratorIntelligence:
    enable_debate: bool = True
    enable_reflection: bool = True
    enable_reroute: bool = True
    parallel_tasks: bool = True

    def start_mission(self, mission_id: str) -> bool:
        # smoke-test friendly stub
        return True
