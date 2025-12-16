import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    ExecutionFlow,
    OrchestratorPolicy,
    HumanApprovalManager,
    MilestoneType,
    Logger,
    LogLevel,
    MetricsCollector,
    Traceability
)

def approval_callback(request):
    print(f"\n[APPROVAL] {request.milestone_type.value}: {request.description[:50]}...")
    return True

def main():
    logger = Logger(log_file="logs/full_cycle.log", level=LogLevel.INFO)
    metrics = MetricsCollector()
    traceability = Traceability(logger, metrics)
    
    approval_manager = HumanApprovalManager()
    approval_manager.register_callback(MilestoneType.MISSION_PLAN, approval_callback)
    approval_manager.register_callback(MilestoneType.FINAL_DELIVERY, approval_callback)
    
    policy = OrchestratorPolicy(
        agent_selection_strategy="performance_based",
        task_prioritization_strategy="dependency_aware",
        retry_enabled=True,
        adaptive_learning_enabled=True
    )
    
    flow = ExecutionFlow(policy, approval_manager)
    
    goal = "Build a user authentication API with JWT tokens"
    
    trace_id = traceability.start_trace("full_cycle_1", "mission_full", goal)
    traceability.add_event(trace_id, "cycle_started", "Full execution cycle initiated")
    
    print("=" * 80)
    print("FULL EXECUTION CYCLE DEMONSTRATION")
    print("=" * 80)
    print(f"\nGoal: {goal}\n")
    
    print("Step 1: Mission Definition")
    print("-" * 80)
    result = flow.execute_mission(goal, priority=9)
    mission_id = result["mission_id"]
    print(f"Mission ID: {mission_id}")
    print(f"Status: {result['status']}\n")
    
    print("Step 2: Memory Verification")
    print("-" * 80)
    outcome = flow.memory_system.long_term.get_project_outcome(mission_id)
    if outcome:
        print(f"Outcome stored: {outcome.outcome.value}")
        print(f"Tasks: {outcome.tasks_count}")
        print(f"Agents used: {len(outcome.agents_used)}\n")
    
    print("Step 3: Execution Summary")
    print("-" * 80)
    summary = result.get("execution_summary", {})
    print(f"Phases: {len(summary.get('phases_completed', []))}")
    print(f"Tasks completed: {summary.get('tasks_completed', 0)}")
    print(f"Average score: {summary.get('average_score', 0.0):.2f}\n")
    
    print("Step 4: Approval History")
    print("-" * 80)
    approvals = approval_manager.get_approval_history(mission_id)
    for approval in approvals:
        print(f"{approval.milestone_type.value}: {approval.status.value}")
    
    traceability.end_trace(trace_id, result["status"], result)
    
    print("\n" + "=" * 80)
    print("FULL CYCLE COMPLETE")
    print("=" * 80)
    
    return result

if __name__ == "__main__":
    main()


