"""
Automation helpers: SoftwareFactory using MissionModeExecutor.
"""

from dataclasses import dataclass
from typing import Any, Optional

from .mission_mode import MissionModeExecutor, MissionModeResult
from .agents import AgentRegistry
from .tools import ToolRegistry
from .memory import MemorySystem
from .logging import AuditLogger
from .orchestrator import OrchestratorPolicy
from .human_approval import HumanApprovalManager


@dataclass
class FactoryConfig:
    workspace: str = "workspace/mission_mode"


class SoftwareFactory:
    def __init__(self, agent_registry: Optional[AgentRegistry] = None, tools: Optional[ToolRegistry] = None, memory: Optional[MemorySystem] = None, audit: Optional[AuditLogger] = None, config: Optional[FactoryConfig] = None, policy: Optional[OrchestratorPolicy] = None, approval_manager: Optional[HumanApprovalManager] = None):
        self.agent_registry = agent_registry or AgentRegistry()
        self.tools = tools or ToolRegistry()
        self.memory = memory or MemorySystem()
        self.audit = audit or AuditLogger("software_factory")
        self.config = config or FactoryConfig()
        self.policy = policy or OrchestratorPolicy()
        self.approval_manager = approval_manager or HumanApprovalManager()
        self.executor = MissionModeExecutor(self.agent_registry, self.tools, self.memory, self.audit)

    def run_mission(self, mission_id: str, goal: str) -> MissionModeResult:
        self.audit.log_event("factory_mission_started", {"mission_id": mission_id, "goal": goal})
        result = self.executor.run(mission_id, goal, workspace=self.config.workspace)
        self.audit.log_event("factory_mission_completed", {"mission_id": mission_id, "status": result.status})
        return result

    def run_mission_mode(self, goal: str) -> MissionModeResult:
        mission_id = "mission_mode_1"
        return self.run_mission(mission_id, goal)