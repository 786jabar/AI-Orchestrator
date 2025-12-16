"""
Human approval management for governance checkpoints.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MilestoneType(Enum):
    MISSION_PLAN = "mission_plan"
    FINAL_OUTPUT = "final_output"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class ApprovalRequest:
    milestone: MilestoneType
    description: str
    mission_id: str
    content_preview: Dict[str, Any]
    requested_at: datetime = field(default_factory=datetime.utcnow)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    decision_at: Optional[datetime] = None


class HumanApprovalManager:
    def __init__(self, auto_approve: bool = True):
        self.auto_approve = auto_approve
        self.requests: List[ApprovalRequest] = []

    def request_approval(self, milestone: MilestoneType, payload: Dict[str, Any]) -> bool:
        req = ApprovalRequest(milestone=milestone, description=payload.get("description", payload), mission_id=payload.get("mission_id", "mission"), content_preview=payload)
        if self.auto_approve:
            req.status = ApprovalStatus.APPROVED
            req.approved_by = "callback"
            req.decision_at = datetime.utcnow()
            self.requests.append(req)
            return True
        self.requests.append(req)
        return False

    def list_requests(self) -> List[ApprovalRequest]:
        return self.requests