"""
End-to-End Example: Goal → Plan → Tasks → Code → Evaluation → Integration → Final Output
Demonstrates the complete AI Agent Orchestrator workflow.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    ExecutionFlow,
    OrchestratorPolicy,
    ToolRegistry,
    ToolPermission,
    Logger,
    LogLevel,
    LogCategory,
    MetricsCollector,
    Traceability
)


def main():
    """Run end-to-end example"""
    
    print("=" * 80)
    print("AI AGENT ORCHESTRATOR - END-TO-END EXAMPLE")
    print("=" * 80)
    print()
    
    logger = Logger(log_file="logs/orchestrator.log", level=LogLevel.INFO)
    metrics = MetricsCollector()
    traceability = Traceability(logger, metrics)
    
    tool_registry = ToolRegistry()
    
    policy = OrchestratorPolicy(
        agent_selection_strategy="performance_based",
        task_prioritization_strategy="dependency_aware",
        retry_enabled=True,
        max_retries_per_task=3,
        adaptive_learning_enabled=True
    )
    
    flow = ExecutionFlow(policy)
    
    goal = "Build a REST API for user management with authentication"
    print(f"Goal: {goal}")
    print()
    
    trace_id = traceability.start_trace("trace_1", "mission_example", goal)
    
    traceability.add_event(trace_id, "mission_started", "Starting mission execution")
    
    print("Phase 1: Planning")
    print("-" * 80)
    result = flow.execute_mission(goal, priority=8)
    mission_id = result["mission_id"]
    
    traceability.add_event(trace_id, "mission_completed", f"Mission {mission_id} completed", {
        "status": result["status"],
        "tasks_completed": result.get("execution_summary", {}).get("tasks_completed", 0)
    })
    
    print(f"Mission ID: {mission_id}")
    print(f"Status: {result['status']}")
    print()
    
    if result["status"] == "completed":
        summary = result.get("execution_summary", {})
        print("Execution Summary:")
        print(f"  - Phases: {', '.join(summary.get('phases_completed', []))}")
        print(f"  - Tasks completed: {summary.get('tasks_completed', 0)}")
        print(f"  - Average score: {summary.get('average_score', 0.0):.2f}")
        print(f"  - Agents used: {', '.join(summary.get('agents_used', []))}")
        print(f"  - Execution time: {summary.get('execution_time', 0.0):.2f}s")
        print()
        
        print("Phase 2: Results")
        print("-" * 80)
        integrated_solution = result.get("result", {})
        if integrated_solution:
            print("Integrated Solution Components:")
            components = integrated_solution.get("components", [])
            if isinstance(components, list):
                for comp in components:
                    print(f"  - {comp}")
            elif isinstance(components, dict):
                for key, value in components.items():
                    print(f"  - {key}: {type(value).__name__}")
        print()
        
        print("Phase 3: Metrics & Traceability")
        print("-" * 80)
        status = flow.get_execution_status(mission_id)
        print(f"Mission Status: {status.get('status')}")
        if 'tasks' in status:
            print(f"Tasks: {status['tasks']}")
        print()
        
        mission_metrics = metrics.get_mission_metrics(mission_id)
        if mission_metrics.get("summary"):
            print("Metrics Summary:")
            for metric_name, stats in mission_metrics["summary"].items():
                if stats:
                    print(f"  - {metric_name}:")
                    print(f"      Count: {stats.get('count', 0)}")
                    print(f"      Mean: {stats.get('mean', 0.0):.2f}")
                    print(f"      Min: {stats.get('min', 0.0):.2f}")
                    print(f"      Max: {stats.get('max', 0.0):.2f}")
        print()
        
        trace_summary = traceability.get_trace_summary(trace_id)
        print("Trace Summary:")
        print(f"  - Trace ID: {trace_summary.get('trace_id')}")
        print(f"  - Status: {trace_summary.get('status')}")
        print(f"  - Duration: {trace_summary.get('duration', 0.0):.2f}s")
        print(f"  - Events: {trace_summary.get('event_count', 0)}")
        print()
        
        recent_logs = logger.get_logs(mission_id=mission_id)
        if recent_logs:
            print(f"Recent Logs ({len(recent_logs)} entries):")
            for log in recent_logs[-5:]:
                print(f"  [{log.level.value}] {log.category.value}: {log.message}")
        print()
    
    traceability.end_trace(trace_id, result["status"], result)
    
    print("=" * 80)
    print("END-TO-END EXAMPLE COMPLETE")
    print("=" * 80)
    print()
    print("Check logs/orchestrator.log for detailed execution logs")
    
    return result


if __name__ == "__main__":
    main()


