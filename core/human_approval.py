"""
Human-in-the-Loop Approval System
Humans approve key milestones but not every step.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


class ApprovalStatus(Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class MilestoneType(Enum):
    """Key milestone types requiring human approval"""
    MISSION_PLAN = "mission_plan"
    ARCHITECTURE_DESIGN = "architecture_design"
    MAJOR_IMPLEMENTATION = "major_implementation"
    INTEGRATION_POINT = "integration_point"
    FINAL_DELIVERY = "final_delivery"


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    milestone_type: MilestoneType
    mission_id: str
    task_id: Optional[str] = None
    description: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    comments: Optional[str] = None
    auto_approve_after: Optional[datetime] = None


class HumanApprovalManager:
    """Manages human approval for key milestones"""
    
    def __init__(self, auto_approve_enabled: bool = False, auto_approve_timeout: int = 3600):
        self.auto_approve_enabled = auto_approve_enabled
        self.auto_approve_timeout = auto_approve_timeout
        self.requests: Dict[str, ApprovalRequest] = {}
        self.approval_callbacks: Dict[MilestoneType, Callable] = {}
        self.auto_approved_milestones: List[MilestoneType] = []
    
    def register_auto_approve(self, milestone_type: MilestoneType):
        """Register milestone type for auto-approval"""
        if milestone_type not in self.auto_approved_milestones:
            self.auto_approved_milestones.append(milestone_type)
    
    def register_callback(self, milestone_type: MilestoneType, callback: Callable):
        """Register callback for approval decision"""
        self.approval_callbacks[milestone_type] = callback
    
    def request_approval(self, milestone_type: MilestoneType, mission_id: str,
                        description: str, content: Dict[str, Any],
                        task_id: Optional[str] = None) -> ApprovalRequest:
        """Request human approval for milestone"""
        if milestone_type in self.auto_approved_milestones:
            request = ApprovalRequest(
                request_id=f"approval_{len(self.requests) + 1}",
                milestone_type=milestone_type,
                mission_id=mission_id,
                task_id=task_id,
                description=description,
                content=content,
                status=ApprovalStatus.AUTO_APPROVED,
                approved_at=datetime.now(),
                approved_by="system"
            )
            self.requests[request.request_id] = request
            return request
        
        request = ApprovalRequest(
            request_id=f"approval_{len(self.requests) + 1}",
            milestone_type=milestone_type,
            mission_id=mission_id,
            task_id=task_id,
            description=description,
            content=content
        )
        
        if self.auto_approve_enabled:
            request.auto_approve_after = datetime.fromtimestamp(
                datetime.now().timestamp() + self.auto_approve_timeout
            )
        
        self.requests[request.request_id] = request
        
        if milestone_type in self.approval_callbacks:
            callback = self.approval_callbacks[milestone_type]
            result = callback(request)
            if result:
                self.approve(request.request_id, "callback")
        
        return request
    
    def approve(self, request_id: str, approved_by: str, comments: Optional[str] = None) -> bool:
        """Approve a request"""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_at = datetime.now()
        request.approved_by = approved_by
        request.comments = comments
        
        return True
    
    def reject(self, request_id: str, rejected_by: str, comments: Optional[str] = None) -> bool:
        """Reject a request"""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.approved_at = datetime.now()
        request.approved_by = rejected_by
        request.comments = comments
        
        return True
    
    def check_approval(self, request_id: str) -> Optional[ApprovalStatus]:
        """Check approval status"""
        if request_id not in self.requests:
            return None
        
        request = self.requests[request_id]
        
        if request.status == ApprovalStatus.PENDING and request.auto_approve_after:
            if datetime.now() >= request.auto_approve_after:
                request.status = ApprovalStatus.AUTO_APPROVED
                request.approved_at = datetime.now()
                request.approved_by = "system"
        
        return request.status
    
    def get_pending_requests(self, mission_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests"""
        requests = [r for r in self.requests.values() if r.status == ApprovalStatus.PENDING]
        if mission_id:
            requests = [r for r in requests if r.mission_id == mission_id]
        return requests
    
    def is_approved(self, request_id: str) -> bool:
        """Check if request is approved"""
        status = self.check_approval(request_id)
        return status in [ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED]
    
    def get_approval_history(self, mission_id: str) -> List[ApprovalRequest]:
        """Get approval history for mission"""
        return [r for r in self.requests.values() if r.mission_id == mission_id]


