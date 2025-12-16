"""
Human Approval Example
Demonstrates human-in-the-loop approval for key milestones.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    ExecutionFlow,
    OrchestratorPolicy,
    HumanApprovalManager,
    MilestoneType
)


def approval_callback(request):
    """Example approval callback - in production, this would be a UI or API"""
    print(f"\n[APPROVAL REQUIRED]")
    print(f"Milestone: {request.milestone_type.value}")
    print(f"Description: {request.description}")
    print(f"Mission ID: {request.mission_id}")
    
    # In production, this would wait for human input
    # For demo, auto-approve after showing the request
    return True


def main():
    """Run example with human approval"""
    
    print("=" * 80)
    print("HUMAN-IN-THE-LOOP APPROVAL EXAMPLE")
    print("=" * 80)
    print()
    
    approval_manager = HumanApprovalManager()
    
    # Register callback for mission plan approval
    approval_manager.register_callback(MilestoneType.MISSION_PLAN, approval_callback)
    approval_manager.register_callback(MilestoneType.FINAL_DELIVERY, approval_callback)
    
    # Auto-approve architecture design (not a key milestone)
    approval_manager.register_auto_approve(MilestoneType.ARCHITECTURE_DESIGN)
    
    policy = OrchestratorPolicy()
    flow = ExecutionFlow(policy, approval_manager)
    
    goal = "Build a simple calculator API"
    print(f"Goal: {goal}")
    print()
    
    try:
        result = flow.execute_mission(goal, priority=7)
        print(f"\nMission Status: {result['status']}")
        print(f"Mission ID: {result['mission_id']}")
        
        # Show approval history
        approvals = approval_manager.get_approval_history(result['mission_id'])
        print(f"\nApproval History ({len(approvals)} requests):")
        for approval in approvals:
            print(f"  - {approval.milestone_type.value}: {approval.status.value}")
            if approval.approved_by:
                print(f"    Approved by: {approval.approved_by}")
    except Exception as e:
        print(f"\nError: {e}")
        print("This is expected if approval was not granted")
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()


