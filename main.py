#!/usr/bin/env python3
"""
AI Agent Orchestrator - Main Entry Point
Production-ready AI Software Factory
"""

import sys
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core import (
    SoftwareFactory,
    OrchestratorPolicy,
    HumanApprovalManager,
    MilestoneType,
    AutomationLevel,
    Logger,
    LogLevel,
    MetricsCollector,
    Traceability
)
from core.llm_integration import load_llm_config, ConfigurableLLMInterface


def approval_callback(request):
    """Human approval callback - customize for your needs"""
    print(f"\n{'='*60}")
    print(f"[HUMAN APPROVAL REQUIRED]")
    print(f"{'='*60}")
    print(f"Milestone: {request.milestone_type.value}")
    print(f"Description: {request.description}")
    print(f"Mission ID: {request.mission_id}")
    print(f"\nContent Preview:")
    content = request.content
    if isinstance(content, dict):
        for key in list(content.keys())[:3]:
            print(f"  - {key}: {type(content[key]).__name__}")
    print(f"\n{'='*60}")
    
    # For interactive mode, uncomment below:
    # response = input("Approve? (y/n): ").lower().strip()
    # return response == 'y'
    
    # Auto-approve for demo (change to False to require manual approval)
    return True


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    else:
        goal = input("Enter your goal: ").strip()
        if not goal:
            goal = "Build a REST API for user management"
            print(f"Using default goal: {goal}")
    
    print("\n" + "="*60)
    print("AI AGENT ORCHESTRATOR")
    print("="*60)
    print(f"\nGoal: {goal}\n")
    
    # Setup logging and metrics
    logger = Logger(log_file="logs/orchestrator.log", level=LogLevel.INFO)
    metrics = MetricsCollector()
    traceability = Traceability(logger, metrics)
    
    # Setup human approval
    approval_manager = HumanApprovalManager()
    approval_manager.register_callback(MilestoneType.MISSION_PLAN, approval_callback)
    approval_manager.register_callback(MilestoneType.FINAL_DELIVERY, approval_callback)
    
    # Configure policy
    policy = OrchestratorPolicy(
        agent_selection_strategy="performance_based",
        task_prioritization_strategy="dependency_aware",
        retry_enabled=True,
        max_retries_per_task=3,
        adaptive_learning_enabled=True,
        confidence_threshold=0.8
    )
    
    # Create software factory
    factory = SoftwareFactory(
        policy=policy,
        approval_manager=approval_manager,
        automation_level=AutomationLevel.SEMI_AUTOMATED
    )
    
    # Start trace
    trace_id = traceability.start_trace("main_execution", "mission_main", goal)
    traceability.add_event(trace_id, "execution_started", "Mission execution initiated")
    
    print("Executing mission with automated review and improvement...")
    print("-"*60)
    
    try:
        # Execute mission
        result = factory.execute_with_automation(goal, priority=8)
        
        # Display results
        print("\n" + "="*60)
        print("EXECUTION RESULTS")
        print("="*60)
        print(f"\nMission ID: {result.get('mission_id')}")
        print(f"Status: {result.get('status')}")
        print(f"Iteration: {result.get('final_iteration', result.get('iteration', 1))}")
        
        if "execution_summary" in result:
            summary = result["execution_summary"]
            print(f"\nExecution Summary:")
            print(f"  Phases Completed: {len(summary.get('phases_completed', []))}")
            print(f"  Tasks Completed: {summary.get('tasks_completed', 0)}")
            print(f"  Average Score: {summary.get('average_score', 0.0):.2f}")
            print(f"  Agents Used: {', '.join(summary.get('agents_used', []))}")
            print(f"  Execution Time: {summary.get('execution_time', 0.0):.2f}s")
        
        if "review" in result:
            review = result["review"]
            print(f"\nAutomated Review:")
            print(f"  Passed: {review.passed}")
            print(f"  Score: {review.score:.2f}")
            if review.issues:
                print(f"  Issues Found: {len(review.issues)}")
                for issue in review.issues[:3]:
                    print(f"    - {issue}")
            if review.recommendations:
                print(f"  Recommendations: {len(review.recommendations)}")
                for rec in review.recommendations[:3]:
                    print(f"    - {rec}")
            print(f"  Requires Human Review: {review.requires_human_review}")
        
        # Improvement history
        history = factory.get_improvement_history()
        if history:
            print(f"\nImprovement History:")
            for entry in history:
                print(f"  Iteration {entry['iteration']}: Score {entry['score']:.2f}")
        
        # Approval history
        approvals = approval_manager.get_approval_history(result.get('mission_id', ''))
        if approvals:
            print(f"\nApproval History:")
            for approval in approvals:
                print(f"  {approval.milestone_type.value}: {approval.status.value}")
                if approval.approved_by:
                    print(f"    Approved by: {approval.approved_by}")
        
        traceability.end_trace(trace_id, result.get("status", "unknown"), result)
        
        print("\n" + "="*60)
        print("EXECUTION COMPLETE")
        print("="*60)
        print(f"\nCheck logs/orchestrator.log for detailed execution logs")
        
        return result
        
    except Exception as e:
        print(f"\nError: {e}")
        traceability.end_trace(trace_id, "failed", {"error": str(e)})
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    main()

