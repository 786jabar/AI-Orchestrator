"""
Execution Flow System
Orchestrates the complete workflow from goal to working system.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from .mission import CoreMission, MissionStatus
from .memory import MemorySystem, OutcomeType
from .orchestrator import OrchestratorIntelligence, OrchestratorPolicy, OrchestratorState
from .agents import (
    AgentRegistry, AgentType, BaseAgent, PlannerAgent, DecomposerAgent,
    ControllerAgent, EvaluatorAgent, IntegratorAgent, AgentResult, TaskStatus
)
from .human_approval import HumanApprovalManager, MilestoneType, ApprovalStatus


@dataclass
class ExecutionContext:
    """Context for execution flow"""
    mission_id: str
    goal: str
    current_phase: str = "planning"
    completed_tasks: List[str] = field(default_factory=list)
    active_tasks: List[str] = field(default_factory=list)
    agent_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionFlow:
    """Main execution flow orchestrator"""
    
    def __init__(self, policy: Optional[OrchestratorPolicy] = None,
                 approval_manager: Optional[HumanApprovalManager] = None):
        self.mission_system = CoreMission()
        self.memory_system = MemorySystem()
        self.orchestrator = OrchestratorIntelligence(policy)
        self.agent_registry = AgentRegistry()
        self.approval_manager = approval_manager or HumanApprovalManager()
        self.execution_context: Optional[ExecutionContext] = None
    
    def execute_mission(self, goal: str, priority: int = 5, 
                       metadata: Optional[Dict[str, Any]] = None,
                       max_iterations: int = 1) -> Dict[str, Any]:
        """Execute complete mission from goal to working system"""
        mission_id = self.mission_system.define_mission(goal, priority, metadata)
        self.mission_system.update_mission_status(mission_id, MissionStatus.IN_PROGRESS)
        
        self.execution_context = ExecutionContext(
            mission_id=mission_id,
            goal=goal,
            metadata=metadata or {}
        )
        
        project_state = self.memory_system.initialize_project(mission_id, goal, metadata)
        
        iteration = 0
        best_result = None
        best_score = 0.0
        
        while iteration < max_iterations:
            try:
                plan = self._phase_planning(goal)
                tasks = self._phase_decomposition(plan)
                system = self._phase_execution(tasks)
                final_result = self._phase_integration(system)
                
                summary = self._generate_execution_summary()
                current_score = summary.get("average_score", 0.0)
                
                if current_score > best_score:
                    best_score = current_score
                    best_result = {
                        "mission_id": mission_id,
                        "status": "completed",
                        "result": final_result,
                        "execution_summary": summary,
                        "iteration": iteration + 1
                    }
                
                if current_score >= 0.8 or iteration >= max_iterations - 1:
                    self.mission_system.update_mission_status(mission_id, MissionStatus.COMPLETED)
                    self.memory_system.record_mission_completion(
                        mission_id,
                        OutcomeType.SUCCESS,
                        project_state,
                        completion_time=self._calculate_execution_time(),
                        lessons=self._extract_lessons(),
                        patterns=self._extract_patterns()
                    )
                    return best_result or {
                        "mission_id": mission_id,
                        "status": "completed",
                        "result": final_result,
                        "execution_summary": summary,
                        "iteration": iteration + 1
                    }
                
                iteration += 1
                self.memory_system.short_term.clear_project(mission_id)
                project_state = self.memory_system.initialize_project(mission_id, goal, metadata)
                
            except Exception as e:
                if iteration == 0:
                    self.mission_system.update_mission_status(mission_id, MissionStatus.FAILED)
                    self.memory_system.record_mission_completion(
                        mission_id,
                        OutcomeType.FAILURE,
                        project_state,
                        lessons=[f"Execution failed: {str(e)}"]
                    )
                    return {
                        "mission_id": mission_id,
                        "status": "failed",
                        "error": str(e)
                    }
                break
        
        if best_result:
            self.mission_system.update_mission_status(mission_id, MissionStatus.COMPLETED)
            self.memory_system.record_mission_completion(
                mission_id,
                OutcomeType.SUCCESS,
                project_state,
                completion_time=self._calculate_execution_time(),
                lessons=self._extract_lessons(),
                patterns=self._extract_patterns()
            )
            return best_result
        
        return {
            "mission_id": mission_id,
            "status": "failed",
            "error": "Max iterations reached without acceptable result"
        }
    
    def _phase_planning(self, goal: str) -> Dict[str, Any]:
        """Phase 1: Planner generates plan from goal"""
        self.execution_context.current_phase = "planning"
        self.orchestrator.start_mission(self.execution_context.mission_id)
        
        planner = self.agent_registry.get_agent("planner_1")
        if not planner:
            planner = PlannerAgent()
        
        task = {
            "task_id": f"{self.execution_context.mission_id}_planning",
            "goal": goal
        }
        
        result = planner.execute_task(task)
        plan = self._format_agent_output(result, "planner")
        
        approval_request = self.approval_manager.request_approval(
            MilestoneType.MISSION_PLAN,
            self.execution_context.mission_id,
            f"Mission plan for: {goal}",
            {"plan": plan["results"]["plan"]},
            task["task_id"]
        )
        
        if not self.approval_manager.is_approved(approval_request.request_id):
            raise Exception(f"Mission plan not approved: {approval_request.request_id}")
        
        self.memory_system.short_term.add_artifact(
            self.execution_context.mission_id,
            {"type": "plan", "content": plan, "approval_id": approval_request.request_id}
        )
        
        self.execution_context.agent_outputs["planner"] = plan
        self.execution_context.completed_tasks.append(task["task_id"])
        
        return plan["results"]["plan"]
    
    def _phase_decomposition(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Phase 2: Decomposer breaks plan into tasks"""
        self.execution_context.current_phase = "decomposition"
        
        project_state = self.memory_system.short_term.get_project_state(self.execution_context.mission_id)
        if not project_state:
            self.memory_system.initialize_project(
                self.execution_context.mission_id,
                self.execution_context.goal
            )
        
        decomposer = self.agent_registry.get_agent("decomposer_1")
        if not decomposer:
            decomposer = DecomposerAgent()
        
        task = {
            "task_id": f"{self.execution_context.mission_id}_decomposition",
            "plan": plan
        }
        
        result = decomposer.execute_task(task)
        decomposition = self._format_agent_output(result, "decomposer")
        
        tasks = decomposition["results"]["tasks"]
        
        for task_data in tasks:
            task_id = task_data["task_id"]
            self.memory_system.short_term.add_task(
                self.execution_context.mission_id,
                task_id,
                task_data.get("description", ""),
                task_data.get("dependencies", [])
            )
            self.execution_context.active_tasks.append(task_id)
        
        self.execution_context.agent_outputs["decomposer"] = decomposition
        self.execution_context.completed_tasks.append(task["task_id"])
        
        return tasks
    
    def _phase_execution(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phase 3: Execute tasks with controller coordination"""
        self.execution_context.current_phase = "execution"
        
        controller = self.agent_registry.get_agent("controller_1")
        if not controller:
            controller = ControllerAgent()
        
        evaluator = self.agent_registry.get_agent("evaluator_1")
        if not evaluator:
            evaluator = EvaluatorAgent()
        
        all_outputs = {}
        
        for task_data in tasks:
            task_id = task_data["task_id"]
            task_description = task_data.get("description", "")
            
            self.memory_system.short_term.update_task_status(task_id, "in_progress")
            
            selected_agent = self._controller_select_agent(task_data)
            if not selected_agent:
                continue
            
            agent_result = selected_agent.execute_task({
                "task_id": task_id,
                "description": task_description,
                **task_data
            })
            
            formatted_output = self._format_agent_output(agent_result, selected_agent.agent_type.value)
            all_outputs[task_id] = formatted_output
            
            self.memory_system.short_term.add_task_output(task_id, formatted_output)
            
            evaluation = self._evaluate_output(formatted_output, evaluator, task_data)
            self.execution_context.scores[task_id] = evaluation.get("overall_score", 0.0)
            
            decision = self._controller_decide_action(agent_result, evaluation, controller)
            
            if decision["action"] == "continue":
                self.memory_system.short_term.update_task_status(task_id, "completed")
                self.execution_context.completed_tasks.append(task_id)
                if task_id in self.execution_context.active_tasks:
                    self.execution_context.active_tasks.remove(task_id)
            elif decision["action"] == "retry":
                self._handle_retry(task_id, task_data, selected_agent, decision)
            elif decision["action"] == "escalate":
                self._handle_escalation(task_id, decision)
            
            self.orchestrator.assign_credit(
                selected_agent.agent_id,
                task_id,
                self.execution_context.mission_id,
                agent_result.status == TaskStatus.COMPLETED,
                evaluation.get("overall_score", 0.0)
            )
        
        return all_outputs
    
    def _controller_select_agent(self, task_data: Dict[str, Any]) -> Optional[BaseAgent]:
        """Controller selects next agent using policy logic"""
        task_type = task_data.get("type", "general")
        task_description = task_data.get("description", "")
        
        available_agents = self.agent_registry.list_agents()
        agent_list = [{"agent_id": a["agent_id"], "type": a["agent_type"]} for a in available_agents]
        
        agent_performance = {}
        for agent_info in available_agents:
            agent_id = agent_info["agent_id"]
            credits = self.orchestrator.get_agent_credits(agent_id)
            agent_performance[agent_id] = {
                "success_rate": credits.get("success_rate", 0.5),
                "quality_score": credits.get("average_quality", 0.5)
            }
        
        selected_id = self.orchestrator.policy_engine.select_agent(
            task_type,
            task_description,
            agent_list,
            agent_performance
        )
        
        if selected_id:
            agent = self.agent_registry.get_agent(selected_id)
            if agent:
                self.memory_system.short_term.assign_agent_to_task(
                    task_data["task_id"],
                    agent.agent_id
                )
            return agent
        
        return None
    
    def _format_agent_output(self, result: AgentResult, agent_type: str) -> Dict[str, Any]:
        """Format agent output as structured JSON"""
        return {
            "status": result.status.value,
            "results": result.output,
            "confidence": result.quality_score,
            "agent_type": agent_type,
            "agent_id": result.agent_id,
            "execution_time": result.execution_time,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": result.timestamp.isoformat(),
            "metadata": result.metadata
        }
    
    def _evaluate_output(self, output: Dict[str, Any], evaluator: EvaluatorAgent,
                        task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluator scores outputs"""
        criteria = {
            "completeness": 1.0,
            "quality": 1.0,
            "performance": 0.8
        }
        
        eval_task = {
            "task_id": f"eval_{task_data['task_id']}",
            "output": output["results"],
            "criteria": criteria
        }
        
        eval_result = evaluator.execute_task(eval_task)
        return eval_result.output
    
    def _controller_decide_action(self, agent_result: AgentResult,
                                  evaluation: Dict[str, Any],
                                  controller: ControllerAgent) -> Dict[str, Any]:
        """Controller decides continue/retry/escalate"""
        overall_score = evaluation.get("overall_score", 0.0)
        status = agent_result.status
        
        if status == TaskStatus.COMPLETED and overall_score >= 0.7:
            return {"action": "continue"}
        elif status == TaskStatus.FAILED:
            controller_task = {
                "task_id": agent_result.task_id,
                "action": "escalate"
            }
            controller_result = controller.execute_task(controller_task)
            return controller_result.output
        else:
            controller_task = {
                "task_id": agent_result.task_id,
                "action": "retry",
                "retry_count": 0,
                "max_retries": 3
            }
            controller_result = controller.execute_task(controller_task)
            return controller_result.output
    
    def _handle_retry(self, task_id: str, task_data: Dict[str, Any],
                     agent: BaseAgent, decision: Dict[str, Any]) -> None:
        """Handle task retry"""
        retry_count = decision.get("retry_count", 1)
        if retry_count <= decision.get("max_retries", 3):
            self.memory_system.short_term.update_task_status(task_id, "retrying")
            self.execution_context.metadata[f"{task_id}_retries"] = retry_count
    
    def _handle_escalation(self, task_id: str, decision: Dict[str, Any]) -> None:
        """Handle task escalation"""
        self.memory_system.short_term.update_task_status(task_id, "failed")
        escalation_level = decision.get("level", "medium")
        self.execution_context.metadata[f"{task_id}_escalation"] = escalation_level
    
    def _phase_integration(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Integrator merges outputs into working system"""
        self.execution_context.current_phase = "integration"
        
        integrator = self.agent_registry.get_agent("integrator_1")
        if not integrator:
            integrator = IntegratorAgent()
        
        solutions = []
        for task_id, output in outputs.items():
            solutions.append({
                "task_id": task_id,
                "components": output.get("results", {})
            })
        
        task = {
            "task_id": f"{self.execution_context.mission_id}_integration",
            "solutions": solutions
        }
        
        result = integrator.execute_task(task)
        integrated = self._format_agent_output(result, "integrator")
        
        self.execution_context.agent_outputs["integrator"] = integrated
        
        self.memory_system.short_term.add_artifact(
            self.execution_context.mission_id,
            {
                "type": "integrated_system",
                "content": integrated["results"]["integrated_solution"]
            }
        )
        
        return integrated["results"]["integrated_solution"]
    
    def _calculate_execution_time(self) -> float:
        """Calculate total execution time"""
        total_time = 0.0
        for output in self.execution_context.agent_outputs.values():
            if isinstance(output, dict) and "execution_time" in output:
                total_time += output["execution_time"]
        return total_time
    
    def _extract_lessons(self) -> List[str]:
        """Extract lessons learned from execution"""
        lessons = []
        for task_id, score in self.execution_context.scores.items():
            if score < 0.7:
                lessons.append(f"Task {task_id} scored below threshold: {score:.2f}")
        return lessons
    
    def _extract_patterns(self) -> List[str]:
        """Extract patterns from execution"""
        patterns = []
        if len(self.execution_context.completed_tasks) > 0:
            patterns.append("Sequential task execution")
        if any("retry" in str(v) for v in self.execution_context.metadata.values()):
            patterns.append("Retry mechanism used")
        return patterns
    
    def _generate_execution_summary(self) -> Dict[str, Any]:
        """Generate execution summary"""
        return {
            "mission_id": self.execution_context.mission_id,
            "goal": self.execution_context.goal,
            "phases_completed": ["planning", "decomposition", "execution", "integration"],
            "tasks_completed": len(self.execution_context.completed_tasks),
            "tasks_active": len(self.execution_context.active_tasks),
            "average_score": sum(self.execution_context.scores.values()) / len(self.execution_context.scores) if self.execution_context.scores else 0.0,
            "agents_used": list(set(output.get("agent_id") for output in self.execution_context.agent_outputs.values() if isinstance(output, dict))),
            "execution_time": self._calculate_execution_time()
        }
    
    def get_execution_status(self, mission_id: str) -> Dict[str, Any]:
        """Get current execution status"""
        mission = self.mission_system.get_mission(mission_id)
        if not mission:
            return {"error": "Mission not found"}
        
        project_state = self.memory_system.short_term.get_project_state(mission_id)
        outcome = self.memory_system.long_term.get_project_outcome(mission_id)
        
        if not project_state and not outcome:
            return {"status": "not_started"}
        
        if outcome:
            return {
                "mission_id": mission_id,
                "status": mission.status.value,
                "goal": mission.goal,
                "outcome": outcome.outcome.value,
                "tasks": {
                    "total": outcome.tasks_count,
                    "completed": outcome.successful_tasks,
                    "failed": outcome.failed_tasks
                },
                "completed_at": outcome.completed_at.isoformat()
            }
        
        return {
            "mission_id": mission_id,
            "status": mission.status.value,
            "goal": mission.goal,
            "tasks": {
                "total": len(project_state.tasks),
                "completed": sum(1 for t in project_state.tasks.values() if t.status == "completed"),
                "in_progress": sum(1 for t in project_state.tasks.values() if t.status == "in_progress"),
                "failed": sum(1 for t in project_state.tasks.values() if t.status == "failed")
            },
            "artifacts": len(project_state.artifacts)
        }

