"""
Memory System for AI Agent Orchestrator
Manages short-term and long-term memory for project state and historical data.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


class MemoryType(Enum):
    """Memory type classification"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class OutcomeType(Enum):
    """Project outcome classification"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class TaskState:
    """Represents current task state in short-term memory"""
    task_id: str
    mission_id: str
    description: str
    status: str
    assigned_agent: Optional[str] = None
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProjectState:
    """Current project state in short-term memory"""
    mission_id: str
    goal: str
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentPerformance:
    """Agent performance metrics for long-term memory"""
    agent_id: str
    agent_type: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    success_rate: float = 0.0
    average_execution_time: float = 0.0
    strengths: Set[str] = field(default_factory=set)
    weaknesses: Set[str] = field(default_factory=set)
    last_used: Optional[datetime] = None


@dataclass
class ProjectOutcome:
    """Historical project outcome for long-term memory"""
    mission_id: str
    goal: str
    outcome: OutcomeType
    completion_time: Optional[float] = None
    tasks_count: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    agents_used: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    patterns_identified: List[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.now)


class ShortTermMemory:
    """Manages current project state, tasks, and outputs"""
    
    def __init__(self):
        self.projects: Dict[str, ProjectState] = {}
        self.active_tasks: Dict[str, TaskState] = {}
    
    def create_project_state(self, mission_id: str, goal: str, metadata: Optional[Dict[str, Any]] = None) -> ProjectState:
        """Create new project state"""
        project = ProjectState(
            mission_id=mission_id,
            goal=goal,
            metadata=metadata or {}
        )
        self.projects[mission_id] = project
        return project
    
    def get_project_state(self, mission_id: str) -> Optional[ProjectState]:
        """Retrieve project state"""
        return self.projects.get(mission_id)
    
    def add_task(self, mission_id: str, task_id: str, description: str, dependencies: Optional[List[str]] = None) -> TaskState:
        """Add task to project state"""
        if mission_id not in self.projects:
            raise ValueError(f"Project {mission_id} not found")
        
        task = TaskState(
            task_id=task_id,
            mission_id=mission_id,
            description=description,
            status="pending",
            dependencies=dependencies or []
        )
        self.projects[mission_id].tasks[task_id] = task
        self.active_tasks[task_id] = task
        self.projects[mission_id].updated_at = datetime.now()
        return task
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = status
            task.updated_at = datetime.now()
            if task.mission_id in self.projects:
                self.projects[task.mission_id].updated_at = datetime.now()
            return True
        return False
    
    def assign_agent_to_task(self, task_id: str, agent_id: str) -> bool:
        """Assign agent to task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].assigned_agent = agent_id
            self.active_tasks[task_id].updated_at = datetime.now()
            return True
        return False
    
    def add_task_output(self, task_id: str, output: Dict[str, Any]) -> bool:
        """Add output to task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].outputs.append(output)
            self.active_tasks[task_id].updated_at = datetime.now()
            return True
        return False
    
    def add_artifact(self, mission_id: str, artifact: Dict[str, Any]) -> bool:
        """Add artifact to project"""
        if mission_id in self.projects:
            self.projects[mission_id].artifacts.append(artifact)
            self.projects[mission_id].updated_at = datetime.now()
            return True
        return False
    
    def get_active_tasks(self, mission_id: Optional[str] = None) -> List[TaskState]:
        """Get active tasks, optionally filtered by mission"""
        if mission_id:
            return [task for task in self.active_tasks.values() if task.mission_id == mission_id]
        return list(self.active_tasks.values())
    
    def get_task_dependencies(self, task_id: str) -> List[str]:
        """Get task dependencies"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].dependencies
        return []
    
    def clear_project(self, mission_id: str) -> bool:
        """Clear project from short-term memory"""
        if mission_id in self.projects:
            task_ids = list(self.projects[mission_id].tasks.keys())
            for task_id in task_ids:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
            del self.projects[mission_id]
            return True
        return False


class LongTermMemory:
    """Manages historical project outcomes, agent performance, and patterns"""
    
    def __init__(self):
        self.project_outcomes: Dict[str, ProjectOutcome] = {}
        self.agent_performance: Dict[str, AgentPerformance] = {}
        self.patterns: List[Dict[str, Any]] = []
        self.lessons_learned: List[str] = []
    
    def record_project_outcome(self, outcome: ProjectOutcome) -> None:
        """Record project outcome"""
        self.project_outcomes[outcome.mission_id] = outcome
        self.lessons_learned.extend(outcome.lessons_learned)
        for pattern in outcome.patterns_identified:
            if pattern not in [p.get("pattern") for p in self.patterns]:
                self.patterns.append({
                    "pattern": pattern,
                    "first_seen": outcome.completed_at,
                    "frequency": 1
                })
    
    def get_project_outcome(self, mission_id: str) -> Optional[ProjectOutcome]:
        """Retrieve project outcome"""
        return self.project_outcomes.get(mission_id)
    
    def update_agent_performance(self, agent_id: str, agent_type: str, success: bool, execution_time: Optional[float] = None) -> None:
        """Update agent performance metrics"""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = AgentPerformance(
                agent_id=agent_id,
                agent_type=agent_type
            )
        
        perf = self.agent_performance[agent_id]
        if success:
            perf.tasks_completed += 1
        else:
            perf.tasks_failed += 1
        
        total = perf.tasks_completed + perf.tasks_failed
        perf.success_rate = perf.tasks_completed / total if total > 0 else 0.0
        
        if execution_time is not None:
            if perf.average_execution_time == 0.0:
                perf.average_execution_time = execution_time
            else:
                perf.average_execution_time = (perf.average_execution_time + execution_time) / 2
        
        perf.last_used = datetime.now()
    
    def get_agent_performance(self, agent_id: str) -> Optional[AgentPerformance]:
        """Get agent performance data"""
        return self.agent_performance.get(agent_id)
    
    def get_best_agents_for_task(self, task_type: str, limit: int = 5) -> List[AgentPerformance]:
        """Get best performing agents for a task type"""
        relevant_agents = [
            perf for perf in self.agent_performance.values()
            if task_type in perf.strengths or perf.agent_type == task_type
        ]
        sorted_agents = sorted(
            relevant_agents,
            key=lambda x: (x.success_rate, x.tasks_completed),
            reverse=True
        )
        return sorted_agents[:limit]
    
    def add_agent_strength(self, agent_id: str, strength: str) -> None:
        """Add strength to agent profile"""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = AgentPerformance(
                agent_id=agent_id,
                agent_type="unknown"
            )
        self.agent_performance[agent_id].strengths.add(strength)
    
    def add_agent_weakness(self, agent_id: str, weakness: str) -> None:
        """Add weakness to agent profile"""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = AgentPerformance(
                agent_id=agent_id,
                agent_type="unknown"
            )
        self.agent_performance[agent_id].weaknesses.add(weakness)
    
    def get_similar_past_projects(self, goal: str, limit: int = 5) -> List[ProjectOutcome]:
        """Get similar past projects based on goal similarity"""
        goal_keywords = set(goal.lower().split())
        scored_projects = []
        
        for outcome in self.project_outcomes.values():
            outcome_keywords = set(outcome.goal.lower().split())
            similarity = len(goal_keywords.intersection(outcome_keywords)) / len(goal_keywords.union(outcome_keywords)) if goal_keywords.union(outcome_keywords) else 0.0
            scored_projects.append((similarity, outcome))
        
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        return [outcome for _, outcome in scored_projects[:limit]]
    
    def get_failure_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns from failed projects"""
        failed_outcomes = [
            outcome for outcome in self.project_outcomes.values()
            if outcome.outcome == OutcomeType.FAILURE
        ]
        patterns = defaultdict(int)
        for outcome in failed_outcomes:
            for pattern in outcome.patterns_identified:
                patterns[pattern] += 1
        return [{"pattern": p, "frequency": f} for p, f in patterns.items()]
    
    def get_success_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns from successful projects"""
        successful_outcomes = [
            outcome for outcome in self.project_outcomes.values()
            if outcome.outcome == OutcomeType.SUCCESS
        ]
        patterns = defaultdict(int)
        for outcome in successful_outcomes:
            for pattern in outcome.patterns_identified:
                patterns[pattern] += 1
        return [{"pattern": p, "frequency": f} for p, f in patterns.items()]


class MemorySystem:
    """Unified memory system combining short-term and long-term memory"""
    
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
    
    def initialize_project(self, mission_id: str, goal: str, metadata: Optional[Dict[str, Any]] = None) -> ProjectState:
        """Initialize project in short-term memory"""
        similar_projects = self.long_term.get_similar_past_projects(goal, limit=3)
        if similar_projects:
            metadata = metadata or {}
            metadata["similar_past_projects"] = [p.mission_id for p in similar_projects]
        return self.short_term.create_project_state(mission_id, goal, metadata)
    
    def suggest_agents_for_task(self, task_type: str, task_description: str, limit: int = 3) -> List[AgentPerformance]:
        """Suggest agents based on historical performance"""
        return self.long_term.get_best_agents_for_task(task_type, limit)
    
    def guide_task_decomposition(self, goal: str) -> Dict[str, Any]:
        """Guide task decomposition using historical patterns"""
        similar_projects = self.long_term.get_similar_past_projects(goal, limit=5)
        success_patterns = self.long_term.get_success_patterns()
        failure_patterns = self.long_term.get_failure_patterns()
        
        guidance = {
            "similar_projects": len(similar_projects),
            "recommended_approach": [],
            "warnings": [],
            "suggested_tasks": []
        }
        
        if similar_projects:
            avg_tasks = sum(p.tasks_count for p in similar_projects) / len(similar_projects)
            guidance["suggested_tasks"].append(f"Average task count from similar projects: {avg_tasks:.1f}")
        
        for pattern in success_patterns[:3]:
            guidance["recommended_approach"].append(pattern["pattern"])
        
        for pattern in failure_patterns[:3]:
            guidance["warnings"].append(f"Avoid: {pattern['pattern']}")
        
        return guidance
    
    def record_mission_completion(self, mission_id: str, outcome: OutcomeType, 
                                  short_term_state: Optional[ProjectState] = None,
                                  completion_time: Optional[float] = None,
                                  lessons: Optional[List[str]] = None,
                                  patterns: Optional[List[str]] = None) -> None:
        """Record mission completion and move to long-term memory"""
        if short_term_state:
            project_outcome = ProjectOutcome(
                mission_id=mission_id,
                goal=short_term_state.goal,
                outcome=outcome,
                completion_time=completion_time,
                tasks_count=len(short_term_state.tasks),
                successful_tasks=sum(1 for t in short_term_state.tasks.values() if t.status == "completed"),
                failed_tasks=sum(1 for t in short_term_state.tasks.values() if t.status == "failed"),
                agents_used=list(set(t.assigned_agent for t in short_term_state.tasks.values() if t.assigned_agent)),
                lessons_learned=lessons or [],
                patterns_identified=patterns or []
            )
            self.long_term.record_project_outcome(project_outcome)
            self.short_term.clear_project(mission_id)


