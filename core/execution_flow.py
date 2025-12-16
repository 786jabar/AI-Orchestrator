"""
Execution flow with DAG task handling, retries, and audit trail.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading

from .agents import AgentRegistry, AgentType, TaskStatus, AgentResult
from .memory import MemorySystem, OutcomeType
from .human_approval import HumanApprovalManager, MilestoneType
from .logging import AuditLogger
from .tools import ToolRegistry, ToolPermission


class NodeState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class TaskNode:
    task_id: str
    description: str
    agent_type: AgentType
    payload: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retries: int = 0
    max_retries: int = 2
    state: NodeState = NodeState.PENDING
    last_result: Optional[AgentResult] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_ready(self, completed: set[str]) -> bool:
        return self.state == NodeState.PENDING and all(dep in completed for dep in self.dependencies)


@dataclass
class ExecutionContext:
    mission_id: str
    goal: str
    audit: AuditLogger
    memory: MemorySystem
    approvals: HumanApprovalManager
    tools: ToolRegistry
    agent_registry: AgentRegistry
    budget: Dict[str, Any] = field(default_factory=dict)
    retries_total: int = 0
    tool_calls: int = 0


def _execute_task(context: ExecutionContext, node: TaskNode) -> TaskNode:
    node.state = NodeState.RUNNING
    node.updated_at = datetime.utcnow()
    context.audit.log_event("task_started", {"task_id": node.task_id, "agent_type": node.agent_type.value, "payload": node.payload})
    agent = context.agent_registry.get_agents_by_type(node.agent_type)[0]
    result = agent.execute_task({"task_id": node.task_id, **node.payload})
    node.last_result = result
    if result.status == TaskStatus.COMPLETED:
        node.state = NodeState.COMPLETED
        context.memory.short_term.add_task_output(node.task_id, result.output)
        context.audit.log_event("task_completed", {"task_id": node.task_id, "output": result.output, "confidence": result.confidence})
    else:
        node.state = NodeState.FAILED
        context.audit.log_event("task_failed", {"task_id": node.task_id, "errors": result.errors, "warnings": result.warnings})
    node.updated_at = datetime.utcnow()
    return node


def run_dag(mission: Dict[str, Any], agent_registry: AgentRegistry, tools: ToolRegistry, memory: MemorySystem, approvals: HumanApprovalManager, audit: AuditLogger, max_workers: int = 4, budget: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    mission_id = mission.get("mission_id", "mission_1")
    goal = mission.get("goal", "")
    budget = budget or {"max_retries": 8, "max_tool_calls": 50}

    context = ExecutionContext(mission_id=mission_id, goal=goal, audit=audit, memory=memory, approvals=approvals, tools=tools, agent_registry=agent_registry, budget=budget)
    memory.initialize_project(mission_id, goal)

    planner = agent_registry.get_agents_by_type(AgentType.PLANNER)[0]
    plan_res = planner.execute_task({"task_id": "plan_1", "goal": goal})
    decomposer = agent_registry.get_agents_by_type(AgentType.DECOMPOSER)[0]
    dec_res = decomposer.execute_task({"task_id": "decompose_1", "plan": plan_res.output.get("plan", {})})
    tasks_def = dec_res.output.get("tasks", [])

    nodes: Dict[str, TaskNode] = {}
    for t in tasks_def:
        nodes[t["task_id"]] = TaskNode(task_id=t["task_id"], description=t.get("description", ""), agent_type=AgentType.CODER if "code" in t.get("description", "") else AgentType.INTEGRATOR, payload={"description": t.get("description", "")}, dependencies=t.get("dependencies", []))
        memory.short_term.add_task(mission_id, t["task_id"], t.get("description", ""), dependencies=t.get("dependencies", []))

    completed: set[str] = set()
    failed: set[str] = set()
    lock = threading.Lock()

    def worker(node: TaskNode):
        updated = _execute_task(context, node)
        with lock:
            if updated.state == NodeState.COMPLETED:
                completed.add(updated.task_id)
            else:
                failed.add(updated.task_id)
        return updated

    while len(completed) + len(failed) < len(nodes):
        ready = [n for n in nodes.values() if n.is_ready(completed)]
        if not ready:
            context.audit.log_event("dag_blocked", {"completed": list(completed), "failed": list(failed)})
            break
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(worker, n): n.task_id for n in ready}
            for fut in as_completed(futures):
                fut.result()

        to_retry = [n for n in nodes.values() if n.state == NodeState.FAILED and n.retries < n.max_retries]
        for n in to_retry:
            n.retries += 1
            n.state = NodeState.PENDING
            context.audit.log_event("task_retry", {"task_id": n.task_id, "retries": n.retries})

    outcome = OutcomeType.SUCCESS if not failed else OutcomeType.FAILURE
    memory.record_mission_completion(mission_id, outcome, memory.short_term.get_project_state(mission_id))
    return {"mission_id": mission_id, "status": outcome.value, "completed": list(completed), "failed": list(failed)}