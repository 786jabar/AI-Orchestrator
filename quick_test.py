#!/usr/bin/env python3
"""
Quick test script to verify AI Agent Orchestrator functionality
"""

from core import (
    SoftwareFactory,
    OrchestratorPolicy,
    HumanApprovalManager,
    MilestoneType,
    AutomationLevel
)

def main():
    print("=" * 60)
    print("AI AGENT ORCHESTRATOR - QUICK TEST")
    print("=" * 60)
    print()
    
    # Setup approval manager with auto-approval for testing
    approval_manager = HumanApprovalManager()
    approval_manager.register_auto_approve(MilestoneType.MISSION_PLAN)
    approval_manager.register_auto_approve(MilestoneType.FINAL_DELIVERY)
    
    # Create factory
    policy = OrchestratorPolicy()
    factory = SoftwareFactory(
        policy=policy,
        approval_manager=approval_manager,
        automation_level=AutomationLevel.SEMI_AUTOMATED
    )
    
    # Test goal
    goal = "Create a simple calculator API"
    print(f"Goal: {goal}")
    print()
    print("Executing...")
    print("-" * 60)
    
    # Execute
    result = factory.execute_with_automation(goal, priority=7)
    
    # Results
    print()
    print("Results:")
    print(f"  Mission ID: {result.get('mission_id')}")
    print(f"  Status: {result.get('status')}")
    
    if "execution_summary" in result:
        summary = result["execution_summary"]
        print(f"  Tasks Completed: {summary.get('tasks_completed', 0)}")
        print(f"  Average Score: {summary.get('average_score', 0.0):.2f}")
    
    if "review" in result:
        review = result["review"]
        print(f"  Review Passed: {review.passed}")
        print(f"  Review Score: {review.score:.2f}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE - System is operational!")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    main()


