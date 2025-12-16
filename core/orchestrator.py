"""
Orchestrator Intelligence System
Central orchestrator with state machine, policy engine, credit assignment, and adaptive orchestration.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import math


class OrchestratorState(Enum):
    """Orchestrator state machine states"""
    IDLE = "idle"
    PLANNING = "planning"
    DECOMPOSING = "decomposing"
    ASSIGNING = "assigning"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    EVALUATING = "evaluating"
    RETRYING = "retrying"
    FALLBACK = "fallback"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5


class RetryStrategy(Enum):
    """Retry strategy types"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    NO_RETRY = "no_retry"


class FallbackStrategy(Enum):
    """Fallback strategy types"""
    NEXT_BEST_AGENT = "next_best_agent"
    HUMAN_INTERVENTION = "human_intervention"
    SIMPLIFY_TASK = "simplify_task"
    SKIP_TASK = "skip_task"
    ABORT_MISSION = "abort_mission"


class StoppingCondition(Enum):
    """Stopping condition types"""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    SCORE_CONVERGENCE = "score_convergence"
    HUMAN_INTERVENTION = "human_intervention"
    MAX_ITERATIONS = "max_iterations"
    TIME_LIMIT = "time_limit"
    SUCCESS_CRITERIA = "success_criteria"


@dataclass
class AgentCredit:
    """Credit assignment for agent contributions"""
    agent_id: str
    task_id: str
    mission_id: str
    contribution_score: float = 0.0
    success_credit: float = 0.0
    failure_credit: float = 0.0
    quality_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TaskAssignment:
    """Task assignment with priority and metadata"""
    task_id: str
    agent_id: str
    priority: TaskPriority
    retry_count: int = 0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    fallback_strategy: FallbackStrategy = FallbackStrategy.NEXT_BEST_AGENT
    assigned_at: datetime = field(default_factory=datetime.now)


@dataclass
class OrchestratorPolicy:
    """Policy configuration for orchestrator decisions"""
    agent_selection_strategy: str = "performance_based"
    task_prioritization_strategy: str = "dependency_aware"
    retry_enabled: bool = True
    max_retries_per_task: int = 3
    default_retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    fallback_enabled: bool = True
    default_fallback_strategy: FallbackStrategy = FallbackStrategy.NEXT_BEST_AGENT
    adaptive_learning_enabled: bool = True
    confidence_threshold: float = 0.8
    convergence_threshold: float = 0.01
    max_iterations: int = 100


@dataclass
class StoppingConditionConfig:
    """Configuration for stopping conditions"""
    condition_type: StoppingCondition
    threshold: float
    enabled: bool = True
    callback: Optional[Callable] = None


class StateMachine:
    """Orchestrator state machine"""
    
    def __init__(self):
        self.current_state = OrchestratorState.IDLE
        self.state_history: List[Dict[str, Any]] = []
        self.transitions: Dict[OrchestratorState, Set[OrchestratorState]] = {
            OrchestratorState.IDLE: {OrchestratorState.PLANNING, OrchestratorState.PAUSED},
            OrchestratorState.PLANNING: {OrchestratorState.DECOMPOSING, OrchestratorState.IDLE},
            OrchestratorState.DECOMPOSING: {OrchestratorState.ASSIGNING, OrchestratorState.PLANNING},
            OrchestratorState.ASSIGNING: {OrchestratorState.EXECUTING, OrchestratorState.DECOMPOSING},
            OrchestratorState.EXECUTING: {OrchestratorState.MONITORING, OrchestratorState.RETRYING, OrchestratorState.FALLBACK},
            OrchestratorState.MONITORING: {OrchestratorState.EXECUTING, OrchestratorState.EVALUATING, OrchestratorState.RETRYING},
            OrchestratorState.EVALUATING: {OrchestratorState.EXECUTING, OrchestratorState.COMPLETED, OrchestratorState.FAILED},
            OrchestratorState.RETRYING: {OrchestratorState.EXECUTING, OrchestratorState.FALLBACK},
            OrchestratorState.FALLBACK: {OrchestratorState.EXECUTING, OrchestratorState.FAILED, OrchestratorState.PAUSED},
            OrchestratorState.COMPLETED: {OrchestratorState.IDLE},
            OrchestratorState.FAILED: {OrchestratorState.IDLE, OrchestratorState.RETRYING},
            OrchestratorState.PAUSED: {OrchestratorState.IDLE, OrchestratorState.EXECUTING}
        }
    
    def transition(self, new_state: OrchestratorState) -> bool:
        """Transition to new state if valid"""
        if new_state in self.transitions.get(self.current_state, set()):
            old_state = self.current_state
            self.current_state = new_state
            self.state_history.append({
                "from": old_state,
                "to": new_state,
                "timestamp": datetime.now()
            })
            return True
        return False
    
    def can_transition_to(self, state: OrchestratorState) -> bool:
        """Check if transition to state is valid"""
        return state in self.transitions.get(self.current_state, set())
    
    def get_state(self) -> OrchestratorState:
        """Get current state"""
        return self.current_state


class CreditAssignment:
    """Track and assign credit to agents for their contributions"""
    
    def __init__(self):
        self.credits: List[AgentCredit] = []
        self.agent_credits: Dict[str, List[AgentCredit]] = defaultdict(list)
    
    def assign_credit(self, agent_id: str, task_id: str, mission_id: str,
                     success: bool, quality_score: float = 0.0,
                     contribution_weight: float = 1.0) -> AgentCredit:
        """Assign credit to agent for task execution"""
        credit = AgentCredit(
            agent_id=agent_id,
            task_id=task_id,
            mission_id=mission_id,
            contribution_score=contribution_weight,
            success_credit=1.0 if success else 0.0,
            failure_credit=0.0 if success else 1.0,
            quality_score=quality_score
        )
        self.credits.append(credit)
        self.agent_credits[agent_id].append(credit)
        return credit
    
    def get_agent_total_credit(self, agent_id: str) -> float:
        """Get total credit for agent"""
        credits = self.agent_credits.get(agent_id, [])
        if not credits:
            return 0.0
        return sum(c.success_credit * c.contribution_score for c in credits)
    
    def get_agent_success_rate(self, agent_id: str) -> float:
        """Get success rate for agent"""
        credits = self.agent_credits.get(agent_id, [])
        if not credits:
            return 0.0
        total = len(credits)
        successes = sum(1 for c in credits if c.success_credit > 0)
        return successes / total if total > 0 else 0.0
    
    def get_agent_average_quality(self, agent_id: str) -> float:
        """Get average quality score for agent"""
        credits = self.agent_credits.get(agent_id, [])
        if not credits:
            return 0.0
        return sum(c.quality_score for c in credits) / len(credits) if credits else 0.0
    
    def get_mission_credits(self, mission_id: str) -> List[AgentCredit]:
        """Get all credits for a mission"""
        return [c for c in self.credits if c.mission_id == mission_id]


class PolicyEngine:
    """Policy-driven decision making engine"""
    
    def __init__(self, policy: OrchestratorPolicy):
        self.policy = policy
        self.decision_history: List[Dict[str, Any]] = []
    
    def select_agent(self, task_type: str, task_description: str,
                    available_agents: List[Dict[str, Any]],
                    agent_performance: Dict[str, Any]) -> Optional[str]:
        """Select agent based on policy"""
        if not available_agents:
            return None
        
        if self.policy.agent_selection_strategy == "performance_based":
            return self._select_by_performance(available_agents, agent_performance)
        elif self.policy.agent_selection_strategy == "round_robin":
            return self._select_round_robin(available_agents)
        elif self.policy.agent_selection_strategy == "random":
            import random
            return random.choice(available_agents)["agent_id"]
        else:
            return available_agents[0]["agent_id"]
    
    def _select_by_performance(self, agents: List[Dict[str, Any]],
                              performance: Dict[str, Any]) -> str:
        """Select agent based on performance metrics"""
        scored_agents = []
        for agent in agents:
            agent_id = agent["agent_id"]
            perf = performance.get(agent_id, {})
            score = perf.get("success_rate", 0.0) * 0.6 + perf.get("quality_score", 0.0) * 0.4
            scored_agents.append((score, agent_id))
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        return scored_agents[0][1] if scored_agents else None
    
    def _select_round_robin(self, agents: List[Dict[str, Any]]) -> str:
        """Select agent using round-robin"""
        if not hasattr(self, "_round_robin_index"):
            self._round_robin_index = 0
        agent = agents[self._round_robin_index % len(agents)]
        self._round_robin_index += 1
        return agent["agent_id"]
    
    def prioritize_tasks(self, tasks: List[Dict[str, Any]],
                        dependencies: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Prioritize tasks based on policy"""
        if self.policy.task_prioritization_strategy == "dependency_aware":
            return self._prioritize_by_dependencies(tasks, dependencies)
        elif self.policy.task_prioritization_strategy == "priority_value":
            return sorted(tasks, key=lambda x: x.get("priority", 5))
        else:
            return tasks
    
    def _prioritize_by_dependencies(self, tasks: List[Dict[str, Any]],
                                   dependencies: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Prioritize tasks considering dependencies"""
        task_map = {t["task_id"]: t for t in tasks}
        ready_tasks = []
        remaining = set(task_map.keys())
        
        while remaining:
            batch = []
            for task_id in list(remaining):
                deps = dependencies.get(task_id, [])
                if all(dep not in remaining for dep in deps):
                    batch.append(task_id)
            
            if not batch:
                break
            
            for task_id in batch:
                ready_tasks.append(task_map[task_id])
                remaining.remove(task_id)
        
        for task_id in remaining:
            ready_tasks.append(task_map[task_id])
        
        return ready_tasks
    
    def should_retry(self, task_id: str, retry_count: int, error: Optional[str] = None) -> bool:
        """Decide if task should be retried"""
        if not self.policy.retry_enabled:
            return False
        if retry_count >= self.policy.max_retries_per_task:
            return False
        return True
    
    def get_retry_delay(self, retry_count: int, strategy: RetryStrategy) -> float:
        """Calculate retry delay based on strategy"""
        if strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return min(2 ** retry_count, 60.0)
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return retry_count * 5.0
        else:
            return 0.0
    
    def select_fallback(self, task_id: str, failed_agent_id: str,
                       available_agents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select fallback strategy"""
        if not self.policy.fallback_enabled:
            return None
        
        strategy = self.policy.default_fallback_strategy
        if strategy == FallbackStrategy.NEXT_BEST_AGENT:
            remaining = [a for a in available_agents if a["agent_id"] != failed_agent_id]
            return remaining[0] if remaining else None
        elif strategy == FallbackStrategy.HUMAN_INTERVENTION:
            return {"type": "human_intervention", "task_id": task_id}
        elif strategy == FallbackStrategy.SIMPLIFY_TASK:
            return {"type": "simplify_task", "task_id": task_id}
        elif strategy == FallbackStrategy.SKIP_TASK:
            return {"type": "skip_task", "task_id": task_id}
        else:
            return {"type": "abort_mission"}


class AdaptiveOrchestrator:
    """Adaptive orchestration that learns from past performance"""
    
    def __init__(self, policy_engine: PolicyEngine, credit_assignment: CreditAssignment):
        self.policy_engine = policy_engine
        self.credit_assignment = credit_assignment
        self.performance_history: List[Dict[str, Any]] = []
        self.adaptation_weights: Dict[str, float] = defaultdict(lambda: 1.0)
    
    def adapt_agent_selection(self, agent_performance: Dict[str, Any]) -> None:
        """Adapt agent selection based on performance"""
        if not self.policy_engine.policy.adaptive_learning_enabled:
            return
        
        for agent_id, perf in agent_performance.items():
            success_rate = perf.get("success_rate", 0.0)
            quality = perf.get("quality_score", 0.0)
            combined_score = success_rate * 0.6 + quality * 0.4
            self.adaptation_weights[agent_id] = combined_score
    
    def adapt_task_prioritization(self, task_outcomes: Dict[str, bool]) -> None:
        """Adapt task prioritization based on outcomes"""
        if not self.policy_engine.policy.adaptive_learning_enabled:
            return
        
        for task_id, success in task_outcomes.items():
            if not success:
                self.adaptation_weights[f"task_{task_id}"] *= 0.9
    
    def get_adaptive_agent_score(self, agent_id: str, base_score: float) -> float:
        """Get adaptive score for agent"""
        weight = self.adaptation_weights.get(agent_id, 1.0)
        return base_score * weight
    
    def update_from_credits(self) -> None:
        """Update adaptation weights from credit assignment"""
        for agent_id in self.credit_assignment.agent_credits.keys():
            success_rate = self.credit_assignment.get_agent_success_rate(agent_id)
            quality = self.credit_assignment.get_agent_average_quality(agent_id)
            self.adaptation_weights[agent_id] = success_rate * 0.6 + quality * 0.4


class StoppingConditionManager:
    """Manage configurable stopping conditions"""
    
    def __init__(self):
        self.conditions: List[StoppingConditionConfig] = []
        self.metrics: Dict[str, float] = {}
        self.iteration_count: int = 0
        self.start_time: Optional[datetime] = None
    
    def add_condition(self, condition: StoppingConditionConfig) -> None:
        """Add stopping condition"""
        self.conditions.append(condition)
    
    def check_conditions(self, current_metrics: Dict[str, float]) -> Optional[StoppingCondition]:
        """Check if any stopping condition is met"""
        self.metrics.update(current_metrics)
        self.iteration_count += 1
        
        if self.start_time is None:
            self.start_time = datetime.now()
        
        for condition in self.conditions:
            if not condition.enabled:
                continue
            
            if condition.condition_type == StoppingCondition.CONFIDENCE_THRESHOLD:
                confidence = current_metrics.get("confidence", 0.0)
                if confidence >= condition.threshold:
                    if condition.callback:
                        condition.callback(condition.condition_type, current_metrics)
                    return condition.condition_type
            
            elif condition.condition_type == StoppingCondition.SCORE_CONVERGENCE:
                if len(self.metrics.get("scores", [])) >= 2:
                    scores = self.metrics.get("scores", [])
                    if abs(scores[-1] - scores[-2]) < condition.threshold:
                        if condition.callback:
                            condition.callback(condition.condition_type, current_metrics)
                        return condition.condition_type
            
            elif condition.condition_type == StoppingCondition.MAX_ITERATIONS:
                if self.iteration_count >= condition.threshold:
                    if condition.callback:
                        condition.callback(condition.condition_type, current_metrics)
                    return condition.condition_type
            
            elif condition.condition_type == StoppingCondition.TIME_LIMIT:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                if elapsed >= condition.threshold:
                    if condition.callback:
                        condition.callback(condition.condition_type, current_metrics)
                    return condition.condition_type
        
        return None
    
    def reset(self) -> None:
        """Reset stopping condition manager"""
        self.metrics.clear()
        self.iteration_count = 0
        self.start_time = None


class OrchestratorIntelligence:
    """Central orchestrator intelligence system"""
    
    def __init__(self, policy: Optional[OrchestratorPolicy] = None):
        self.state_machine = StateMachine()
        self.policy = policy or OrchestratorPolicy()
        self.policy_engine = PolicyEngine(self.policy)
        self.credit_assignment = CreditAssignment()
        self.adaptive_orchestrator = AdaptiveOrchestrator(self.policy_engine, self.credit_assignment)
        self.stopping_manager = StoppingConditionManager()
        self.active_assignments: Dict[str, TaskAssignment] = {}
        self.mission_tasks: Dict[str, List[str]] = defaultdict(list)
    
    def start_mission(self, mission_id: str) -> bool:
        """Start orchestrating a mission"""
        if self.state_machine.transition(OrchestratorState.PLANNING):
            return True
        return False
    
    def decompose_mission(self, mission_id: str, goal: str) -> List[Dict[str, Any]]:
        """Decompose mission into tasks"""
        if self.state_machine.transition(OrchestratorState.DECOMPOSING):
            tasks = [
                {"task_id": f"{mission_id}_task_{i}", "description": f"Task {i}", "priority": TaskPriority.MEDIUM}
                for i in range(1, 4)
            ]
            self.mission_tasks[mission_id] = [t["task_id"] for t in tasks]
            return tasks
        return []
    
    def assign_tasks(self, mission_id: str, tasks: List[Dict[str, Any]],
                    available_agents: List[Dict[str, Any]],
                    agent_performance: Dict[str, Any]) -> List[TaskAssignment]:
        """Assign tasks to agents"""
        if self.state_machine.transition(OrchestratorState.ASSIGNING):
            prioritized = self.policy_engine.prioritize_tasks(tasks, {})
            assignments = []
            
            for task in prioritized:
                agent_id = self.policy_engine.select_agent(
                    task.get("type", "general"),
                    task.get("description", ""),
                    available_agents,
                    agent_performance
                )
                
                if agent_id:
                    assignment = TaskAssignment(
                        task_id=task["task_id"],
                        agent_id=agent_id,
                        priority=task.get("priority", TaskPriority.MEDIUM),
                        max_retries=self.policy.max_retries_per_task,
                        retry_strategy=self.policy.default_retry_strategy,
                        fallback_strategy=self.policy.default_fallback_strategy
                    )
                    self.active_assignments[task["task_id"]] = assignment
                    assignments.append(assignment)
            
            return assignments
        return []
    
    def execute_task(self, task_id: str) -> bool:
        """Execute assigned task"""
        if task_id in self.active_assignments:
            if self.state_machine.transition(OrchestratorState.EXECUTING):
                return True
        return False
    
    def monitor_execution(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Monitor task execution"""
        if self.state_machine.transition(OrchestratorState.MONITORING):
            assignment = self.active_assignments.get(task_id)
            if assignment:
                if status == "failed" and self.policy_engine.should_retry(task_id, assignment.retry_count):
                    assignment.retry_count += 1
                    return {"action": "retry", "delay": self.policy_engine.get_retry_delay(
                        assignment.retry_count, assignment.retry_strategy)}
                elif status == "failed":
                    fallback = self.policy_engine.select_fallback(task_id, assignment.agent_id, [])
                    return {"action": "fallback", "strategy": fallback}
                elif status == "completed":
                    return {"action": "continue"}
            return {"action": "unknown"}
        return {}
    
    def assign_credit(self, agent_id: str, task_id: str, mission_id: str,
                     success: bool, quality_score: float = 0.0) -> AgentCredit:
        """Assign credit for task execution"""
        credit = self.credit_assignment.assign_credit(
            agent_id, task_id, mission_id, success, quality_score
        )
        self.adaptive_orchestrator.update_from_credits()
        return credit
    
    def check_stopping_conditions(self, metrics: Dict[str, float]) -> Optional[StoppingCondition]:
        """Check if stopping conditions are met"""
        return self.stopping_manager.check_conditions(metrics)
    
    def get_state(self) -> OrchestratorState:
        """Get current orchestrator state"""
        return self.state_machine.get_state()
    
    def get_agent_credits(self, agent_id: str) -> Dict[str, float]:
        """Get credit summary for agent"""
        return {
            "total_credit": self.credit_assignment.get_agent_total_credit(agent_id),
            "success_rate": self.credit_assignment.get_agent_success_rate(agent_id),
            "average_quality": self.credit_assignment.get_agent_average_quality(agent_id)
        }


