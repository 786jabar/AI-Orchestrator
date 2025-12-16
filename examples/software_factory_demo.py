import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

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

def approval_callback(request):
    print(f"\n[HUMAN DECISION POINT] {request.milestone_type.value}")
    print(f"  Description: {request.description[:60]}...")
    print(f"  Auto-approving for demo...")
    return True

def main():
    logger = Logger(log_file="logs/factory.log", level=LogLevel.INFO)
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
    
    factory = SoftwareFactory(
        policy=policy,
        approval_manager=approval_manager,
        automation_level=AutomationLevel.SEMI_AUTOMATED
    )
    
    goal = "Build a secure user authentication system with password hashing"
    
    trace_id = traceability.start_trace("factory_1", "mission_factory", goal)
    traceability.add_event(trace_id, "factory_started", "AI Software Factory execution")
    
    print("=" * 80)
    print("AI SOFTWARE FACTORY - AUTOMATED EXECUTION")
    print("=" * 80)
    print(f"\nGoal: {goal}")
    print(f"Automation Level: {factory.automation_level.value}\n")
    
    print("Executing with automated review and improvement loops...")
    print("-" * 80)
    
    result = factory.execute_with_automation(goal, priority=9)
    
    print(f"\nMission ID: {result.get('mission_id')}")
    print(f"Status: {result.get('status')}")
    print(f"Iteration: {result.get('final_iteration', result.get('iteration', 1))}")
    
    if "review" in result:
        review = result["review"]
        print(f"\nAutomated Review:")
        print(f"  Passed: {review.passed}")
        print(f"  Score: {review.score:.2f}")
        if review.issues:
            print(f"  Issues: {len(review.issues)}")
        if review.recommendations:
            print(f"  Recommendations: {len(review.recommendations)}")
        print(f"  Requires Human Review: {review.requires_human_review}")
    
    if "execution_summary" in result:
        summary = result["execution_summary"]
        print(f"\nExecution Summary:")
        print(f"  Tasks Completed: {summary.get('tasks_completed', 0)}")
        print(f"  Average Score: {summary.get('average_score', 0.0):.2f}")
        print(f"  Agents Used: {len(summary.get('agents_used', []))}")
    
    history = factory.get_improvement_history()
    if history:
        print(f"\nImprovement History ({len(history)} iterations):")
        for entry in history:
            print(f"  Iteration {entry['iteration']}: Score {entry['score']:.2f}")
    
    traceability.end_trace(trace_id, result.get("status", "unknown"), result)
    
    print("\n" + "=" * 80)
    print("FACTORY EXECUTION COMPLETE")
    print("=" * 80)
    
    return result

if __name__ == "__main__":
    main()


