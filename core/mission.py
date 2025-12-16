"""
Core Mission Definition for AI Agent Orchestrator
Defines the fundamental purpose, roles, and responsibilities of the system.
"""

from enum import Enum
from typing import Protocol, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


class Role(Enum):
    """System role definitions"""
    PRODUCT_OWNER = "product_owner"
    CTO = "cto"
    ENGINEERING_MANAGER = "engineering_manager"
    SPECIALIZED_ENGINEER = "specialized_engineer"


class MissionStatus(Enum):
    """Mission execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Mission:
    """Core mission representation"""
    goal: str
    status: MissionStatus = MissionStatus.PENDING
    priority: int = 5
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class HumanInterface(Protocol):
    """Interface for Product Owner/CEO role"""
    
    def define_goal(self, goal: str, priority: int = 5, metadata: Optional[Dict[str, Any]] = None) -> Mission:
        """Define a high-level goal"""
        ...
    
    def approve_plan(self, plan: Dict[str, Any]) -> bool:
        """Approve or reject execution plan"""
        ...
    
    def provide_feedback(self, mission_id: str, feedback: str) -> None:
        """Provide feedback on mission progress"""
        ...


class OrchestratorInterface(Protocol):
    """Interface for CTO/Engineering Manager role"""
    
    def receive_mission(self, mission: Mission) -> str:
        """Receive mission from Product Owner"""
        ...
    
    def decompose_mission(self, mission: Mission) -> Dict[str, Any]:
        """Break down mission into actionable tasks"""
        ...
    
    def assign_tasks(self, tasks: Dict[str, Any]) -> Dict[str, str]:
        """Assign tasks to specialized agents"""
        ...
    
    def coordinate_execution(self, mission_id: str) -> MissionStatus:
        """Coordinate execution across agents"""
        ...
    
    def monitor_progress(self, mission_id: str) -> Dict[str, Any]:
        """Monitor mission progress"""
        ...


class AgentInterface(Protocol):
    """Interface for specialized engineer agents"""
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute assigned task"""
        ...
    
    def report_status(self, task_id: str) -> Dict[str, Any]:
        """Report task execution status"""
        ...
    
    def request_resources(self, resources: Dict[str, Any]) -> bool:
        """Request additional resources if needed"""
        ...


class CoreMission:
    """Core mission orchestrator - transforms goals into working software"""
    
    def __init__(self):
        self.missions: Dict[str, Mission] = {}
        self.role_hierarchy = {
            Role.PRODUCT_OWNER: "Human",
            Role.CTO: "Orchestrator",
            Role.ENGINEERING_MANAGER: "Orchestrator",
            Role.SPECIALIZED_ENGINEER: "AI Agent"
        }
    
    def define_mission(self, goal: str, priority: int = 5, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Define a new mission from high-level goal"""
        mission = Mission(goal=goal, priority=priority, metadata=metadata or {})
        mission_id = f"mission_{len(self.missions) + 1}"
        self.missions[mission_id] = mission
        return mission_id
    
    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Retrieve mission by ID"""
        return self.missions.get(mission_id)
    
    def update_mission_status(self, mission_id: str, status: MissionStatus) -> bool:
        """Update mission status"""
        if mission_id in self.missions:
            self.missions[mission_id].status = status
            return True
        return False
    
    def get_role_responsibility(self, role: Role) -> str:
        """Get responsibility description for role"""
        responsibilities = {
            Role.PRODUCT_OWNER: "Define high-level goals and business objectives",
            Role.CTO: "Architect system design and technical strategy",
            Role.ENGINEERING_MANAGER: "Coordinate execution and manage resources",
            Role.SPECIALIZED_ENGINEER: "Execute specialized technical tasks"
        }
        return responsibilities.get(role, "Unknown role")
    
    def validate_mission(self, mission: Mission) -> bool:
        """Validate mission completeness"""
        return bool(mission.goal and len(mission.goal.strip()) > 0)


