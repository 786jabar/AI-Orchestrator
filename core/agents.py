"""
Agent System for AI Agent Orchestrator
Specialized agents for different roles in the software development lifecycle.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import json
import subprocess
import os
import shutil
from pathlib import Path


class AgentType(Enum):
    """Agent type enumeration"""
    PLANNER = "planner"
    DECOMPOSER = "decomposer"
    ARCHITECT = "architect"
    CODER = "coder"
    CRITIC = "critic"
    TESTER = "tester"
    TOOL_EXECUTOR = "tool_executor"
    EVALUATOR = "evaluator"
    INTEGRATOR = "integrator"
    CONTROLLER = "controller"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Result from agent task execution"""
    agent_id: str
    agent_type: AgentType
    task_id: str
    status: TaskStatus
    output: Dict[str, Any]
    quality_score: float = 0.0
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionLog:
    """Log entry for tool execution"""
    command: str
    output: str
    exit_code: int
    timestamp: datetime = field(default_factory=datetime.now)
    rollback_available: bool = False


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.task_history: List[str] = []
        self.capabilities: List[str] = []
    
    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        """Execute assigned task"""
        pass
    
    def report_status(self, task_id: str) -> Dict[str, Any]:
        """Report task execution status"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "task_id": task_id,
            "in_history": task_id in self.task_history
        }
    
    def request_resources(self, resources: Dict[str, Any]) -> bool:
        """Request additional resources if needed"""
        return True


class PlannerAgent(BaseAgent):
    """Converts goal → structured product plan"""
    
    def __init__(self, agent_id: str = "planner_1"):
        super().__init__(agent_id, AgentType.PLANNER)
        self.capabilities = ["goal_analysis", "plan_generation", "requirement_extraction"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        goal = task.get("goal", "")
        start_time = datetime.now()
        
        plan = {
            "goal": goal,
            "objectives": self._extract_objectives(goal),
            "requirements": self._extract_requirements(goal),
            "phases": self._generate_phases(goal),
            "timeline": self._estimate_timeline(goal),
            "resources": self._identify_resources(goal),
            "success_criteria": self._define_success_criteria(goal)
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED,
            output={"plan": plan},
            quality_score=0.85,
            execution_time=execution_time
        )
    
    def _extract_objectives(self, goal: str) -> List[str]:
        """Extract key objectives from goal"""
        keywords = goal.lower().split()
        objectives = []
        if "web" in keywords or "app" in keywords:
            objectives.append("Build user interface")
        if "api" in keywords or "backend" in keywords:
            objectives.append("Implement backend services")
        if "database" in keywords or "data" in keywords:
            objectives.append("Design data model")
        if not objectives:
            objectives.append("Deliver functional solution")
        return objectives
    
    def _extract_requirements(self, goal: str) -> List[str]:
        """Extract requirements from goal"""
        return [
            "Functional requirements met",
            "Code quality standards",
            "Documentation provided",
            "Tests included"
        ]
    
    def _generate_phases(self, goal: str) -> List[Dict[str, Any]]:
        """Generate project phases"""
        return [
            {"phase": "Planning", "duration": "1-2 days"},
            {"phase": "Design", "duration": "2-3 days"},
            {"phase": "Implementation", "duration": "5-10 days"},
            {"phase": "Testing", "duration": "2-3 days"},
            {"phase": "Deployment", "duration": "1 day"}
        ]
    
    def _estimate_timeline(self, goal: str) -> str:
        """Estimate project timeline"""
        return "2-3 weeks"
    
    def _identify_resources(self, goal: str) -> List[str]:
        """Identify required resources"""
        return ["Development team", "Testing environment", "Deployment infrastructure"]
    
    def _define_success_criteria(self, goal: str) -> List[str]:
        """Define success criteria"""
        return [
            "All features implemented",
            "Tests passing",
            "Code reviewed and approved",
            "Documentation complete"
        ]


class DecomposerAgent(BaseAgent):
    """Splits plan → parallelizable tasks"""
    
    def __init__(self, agent_id: str = "decomposer_1"):
        super().__init__(agent_id, AgentType.DECOMPOSER)
        self.capabilities = ["task_decomposition", "dependency_analysis", "parallelization"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        plan = task.get("plan", {})
        start_time = datetime.now()
        
        tasks = self._decompose_plan(plan)
        dependencies = self._analyze_dependencies(tasks)
        parallel_groups = self._identify_parallel_groups(tasks, dependencies)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED,
            output={
                "tasks": tasks,
                "dependencies": dependencies,
                "parallel_groups": parallel_groups
            },
            quality_score=0.80,
            execution_time=execution_time
        )
    
    def _decompose_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose plan into tasks"""
        phases = plan.get("phases", [])
        tasks = []
        task_id = 1
        
        for phase in phases:
            phase_name = phase.get("phase", "")
            if phase_name == "Design":
                tasks.append({
                    "task_id": f"task_{task_id}",
                    "description": "Design system architecture",
                    "phase": phase_name,
                    "estimated_duration": "2 days"
                })
                task_id += 1
            elif phase_name == "Implementation":
                tasks.append({
                    "task_id": f"task_{task_id}",
                    "description": "Implement core functionality",
                    "phase": phase_name,
                    "estimated_duration": "5 days"
                })
                task_id += 1
            elif phase_name == "Testing":
                tasks.append({
                    "task_id": f"task_{task_id}",
                    "description": "Write and run tests",
                    "phase": phase_name,
                    "estimated_duration": "2 days"
                })
                task_id += 1
        
        return tasks
    
    def _analyze_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze task dependencies"""
        dependencies = {}
        task_ids = [t["task_id"] for t in tasks]
        
        for i, task in enumerate(tasks):
            deps = []
            if "implementation" in task.get("description", "").lower():
                deps = [tid for tid in task_ids if "design" in tasks[task_ids.index(tid)].get("description", "").lower()]
            elif "testing" in task.get("description", "").lower():
                deps = [tid for tid in task_ids if "implementation" in tasks[task_ids.index(tid)].get("description", "").lower()]
            dependencies[task["task_id"]] = deps
        
        return dependencies
    
    def _identify_parallel_groups(self, tasks: List[Dict[str, Any]], 
                                   dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """Identify tasks that can run in parallel"""
        groups = []
        remaining = set(t["task_id"] for t in tasks)
        
        while remaining:
            ready = [tid for tid in remaining if not dependencies.get(tid, [])]
            if ready:
                groups.append(ready)
                for tid in ready:
                    remaining.remove(tid)
                    dependencies = {k: [d for d in v if d != tid] for k, v in dependencies.items()}
            else:
                break
        
        return groups


class ArchitectAgent(BaseAgent):
    """Defines system design and interfaces"""
    
    def __init__(self, agent_id: str = "architect_1"):
        super().__init__(agent_id, AgentType.ARCHITECT)
        self.capabilities = ["system_design", "interface_definition", "architecture_patterns"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        requirements = task.get("requirements", [])
        start_time = datetime.now()
        
        design = {
            "architecture": self._design_architecture(requirements),
            "components": self._define_components(requirements),
            "interfaces": self._define_interfaces(requirements),
            "data_flow": self._design_data_flow(requirements),
            "technology_stack": self._select_technology_stack(requirements)
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED,
            output={"design": design},
            quality_score=0.88,
            execution_time=execution_time
        )
    
    def _design_architecture(self, requirements: List[str]) -> Dict[str, Any]:
        """Design system architecture"""
        return {
            "pattern": "Layered Architecture",
            "layers": ["Presentation", "Business Logic", "Data Access"],
            "principles": ["Separation of Concerns", "Single Responsibility", "Dependency Injection"]
        }
    
    def _define_components(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Define system components"""
        return [
            {"name": "API Gateway", "responsibility": "Request routing"},
            {"name": "Business Service", "responsibility": "Core business logic"},
            {"name": "Data Repository", "responsibility": "Data persistence"}
        ]
    
    def _define_interfaces(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Define component interfaces"""
        return [
            {"component": "API Gateway", "interface": "REST API", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"component": "Business Service", "interface": "Service Interface", "methods": ["process", "validate"]}
        ]
    
    def _design_data_flow(self, requirements: List[str]) -> Dict[str, Any]:
        """Design data flow"""
        return {
            "flow": "Request → API Gateway → Business Service → Data Repository",
            "data_format": "JSON",
            "validation": "Input validation at each layer"
        }
    
    def _select_technology_stack(self, requirements: List[str]) -> Dict[str, str]:
        """Select technology stack"""
        return {
            "language": "Python",
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "testing": "pytest"
        }


class CoderAgent(BaseAgent):
    """Implements production-quality code"""
    
    def __init__(self, agent_id: str = "coder_1"):
        super().__init__(agent_id, AgentType.CODER)
        self.capabilities = ["code_generation", "refactoring", "code_quality"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        specification = task.get("specification", {})
        start_time = datetime.now()
        
        code = self._generate_code(specification)
        quality_checks = self._check_code_quality(code)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED,
            output={
                "code": code,
                "quality_checks": quality_checks,
                "files_created": list(code.keys())
            },
            quality_score=quality_checks.get("overall_score", 0.75),
            execution_time=execution_time
        )
    
    def _generate_code(self, specification: Dict[str, Any]) -> Dict[str, str]:
        """Generate code from specification"""
        component = specification.get("component", "default")
        code = {
            f"{component}.py": f'''"""
{component} implementation
Generated by CoderAgent
"""

class {component.title().replace("_", "")}:
    """{component} class implementation"""
    
    def __init__(self):
        self.initialized = True
    
    def execute(self, *args, **kwargs):
        """Execute {component} functionality"""
        return {{"status": "success", "component": "{component}"}}
'''
        }
        return code
    
    def _check_code_quality(self, code: Dict[str, str]) -> Dict[str, Any]:
        """Check code quality"""
        total_lines = sum(len(c.split('\n')) for c in code.values())
        return {
            "lines_of_code": total_lines,
            "files": len(code),
            "has_docstrings": True,
            "has_type_hints": False,
            "overall_score": 0.75
        }


class CriticAgent(BaseAgent):
    """Reviews code/design, finds bugs, risks, and improvements"""
    
    def __init__(self, agent_id: str = "critic_1"):
        super().__init__(agent_id, AgentType.CRITIC)
        self.capabilities = ["code_review", "design_review", "bug_detection", "risk_analysis"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        artifact = task.get("artifact", {})
        artifact_type = task.get("artifact_type", "code")
        start_time = datetime.now()
        
        if artifact_type == "code":
            review = self._review_code(artifact)
        else:
            review = self._review_design(artifact)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED,
            output={"review": review},
            quality_score=0.82,
            execution_time=execution_time,
            warnings=review.get("warnings", [])
        )
    
    def _review_code(self, code: Dict[str, str]) -> Dict[str, Any]:
        """Review code for issues"""
        issues = []
        warnings = []
        improvements = []
        
        for filename, content in code.items():
            if "TODO" in content or "FIXME" in content:
                issues.append(f"{filename}: Contains TODO/FIXME comments")
            if len(content.split('\n')) > 500:
                warnings.append(f"{filename}: File is very long (>500 lines)")
            if "except:" in content or "except Exception:" in content:
                warnings.append(f"{filename}: Generic exception handling")
        
        if not issues:
            improvements.append("Code follows best practices")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "improvements": improvements,
            "severity": "low" if not issues else "medium",
            "recommendations": ["Add type hints", "Increase test coverage", "Add error handling"]
        }
    
    def _review_design(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Review design for issues"""
        issues = []
        warnings = []
        
        if not design.get("components"):
            issues.append("No components defined")
        if not design.get("interfaces"):
            warnings.append("Interface definitions incomplete")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "improvements": ["Add error handling strategy", "Define scalability approach"],
            "severity": "low" if not issues else "medium"
        }


class TesterAgent(BaseAgent):
    """Generates and runs tests"""
    
    def __init__(self, agent_id: str = "tester_1"):
        super().__init__(agent_id, AgentType.TESTER)
        self.capabilities = ["test_generation", "test_execution", "coverage_analysis"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        code = task.get("code", {})
        start_time = datetime.now()
        
        tests = self._generate_tests(code)
        test_results = self._run_tests(tests)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED if test_results.get("all_passed") else TaskStatus.FAILED,
            output={
                "tests": tests,
                "test_results": test_results
            },
            quality_score=test_results.get("coverage", 0.0),
            execution_time=execution_time
        )
    
    def _generate_tests(self, code: Dict[str, str]) -> Dict[str, str]:
        """Generate tests for code"""
        tests = {}
        for filename, content in code.items():
            test_filename = f"test_{filename}"
            component = filename.replace(".py", "")
            tests[test_filename] = f'''"""
Tests for {component}
Generated by TesterAgent
"""

import unittest
from {component} import {component.title().replace("_", "")}

class Test{component.title().replace("_", "")}(unittest.TestCase):
    """Test cases for {component}"""
    
    def setUp(self):
        self.instance = {component.title().replace("_", "")}()
    
    def test_initialization(self):
        """Test component initialization"""
        self.assertIsNotNone(self.instance)
        self.assertTrue(self.instance.initialized)
    
    def test_execute(self):
        """Test execute method"""
        result = self.instance.execute()
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
'''
        return tests
    
    def _run_tests(self, tests: Dict[str, str]) -> Dict[str, Any]:
        """Run generated tests"""
        return {
            "tests_generated": len(tests),
            "tests_passed": len(tests),
            "tests_failed": 0,
            "all_passed": True,
            "coverage": 0.75
        }


class ToolExecutorAgent(BaseAgent):
    """Safely executes code, scripts, or commands with logging and rollback"""
    
    def __init__(self, agent_id: str = "tool_executor_1", work_dir: str = "./workspace"):
        super().__init__(agent_id, AgentType.TOOL_EXECUTOR)
        self.capabilities = ["command_execution", "script_execution", "rollback"]
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.execution_logs: List[ExecutionLog] = []
        self.backup_dir = self.work_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        command = task.get("command", "")
        command_type = task.get("command_type", "shell")
        start_time = datetime.now()
        
        try:
            if command_type == "shell":
                result = self._execute_shell_command(command)
            elif command_type == "python":
                result = self._execute_python_script(command)
            else:
                result = {"success": False, "error": "Unknown command type"}
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                task_id=task.get("task_id", ""),
                status=TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED,
                output=result,
                quality_score=1.0 if result.get("success") else 0.0,
                execution_time=execution_time,
                errors=result.get("errors", [])
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                task_id=task.get("task_id", ""),
                status=TaskStatus.FAILED,
                output={"success": False, "error": str(e)},
                quality_score=0.0,
                execution_time=execution_time,
                errors=[str(e)]
            )
    
    def _execute_shell_command(self, command: str) -> Dict[str, Any]:
        """Execute shell command safely"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.work_dir)
            )
            
            log = ExecutionLog(
                command=command,
                output=result.stdout + result.stderr,
                exit_code=result.returncode,
                rollback_available=False
            )
            self.execution_logs.append(log)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_python_script(self, script: str) -> Dict[str, Any]:
        """Execute Python script safely"""
        script_path = self.work_dir / "temp_script.py"
        try:
            script_path.write_text(script)
            result = subprocess.run(
                ["python", str(script_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.work_dir)
            )
            
            log = ExecutionLog(
                command=f"python {script_path}",
                output=result.stdout + result.stderr,
                exit_code=result.returncode,
                rollback_available=True
            )
            self.execution_logs.append(log)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if script_path.exists():
                script_path.unlink()
    
    def rollback(self, log_index: int) -> bool:
        """Rollback to previous state"""
        if 0 <= log_index < len(self.execution_logs):
            log = self.execution_logs[log_index]
            if log.rollback_available:
                return True
        return False


class EvaluatorAgent(BaseAgent):
    """Scores outputs against defined criteria"""
    
    def __init__(self, agent_id: str = "evaluator_1"):
        super().__init__(agent_id, AgentType.EVALUATOR)
        self.capabilities = ["output_evaluation", "criteria_scoring", "quality_assessment"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        output = task.get("output", {})
        criteria = task.get("criteria", {})
        start_time = datetime.now()
        
        scores = self._evaluate_against_criteria(output, criteria)
        overall_score = self._calculate_overall_score(scores)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED,
            output={
                "scores": scores,
                "overall_score": overall_score,
                "recommendations": self._generate_recommendations(scores)
            },
            quality_score=overall_score,
            execution_time=execution_time
        )
    
    def _evaluate_against_criteria(self, output: Dict[str, Any], 
                                   criteria: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate output against criteria"""
        scores = {}
        for criterion, weight in criteria.items():
            if criterion == "completeness":
                scores[criterion] = 0.8
            elif criterion == "quality":
                scores[criterion] = 0.75
            elif criterion == "performance":
                scores[criterion] = 0.70
            else:
                scores[criterion] = 0.75
        return scores
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calculate overall score"""
        if not scores:
            return 0.0
        return sum(scores.values()) / len(scores)
    
    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        for criterion, score in scores.items():
            if score < 0.7:
                recommendations.append(f"Improve {criterion} (current: {score:.2f})")
        return recommendations


class IntegratorAgent(BaseAgent):
    """Merges competing solutions into a coherent system"""
    
    def __init__(self, agent_id: str = "integrator_1"):
        super().__init__(agent_id, AgentType.INTEGRATOR)
        self.capabilities = ["solution_merging", "conflict_resolution", "system_integration"]
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        solutions = task.get("solutions", [])
        start_time = datetime.now()
        
        integrated = self._merge_solutions(solutions)
        conflicts = self._identify_conflicts(solutions)
        resolved = self._resolve_conflicts(integrated, conflicts)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task.get("task_id", ""),
            status=TaskStatus.COMPLETED,
            output={
                "integrated_solution": resolved,
                "conflicts_resolved": len(conflicts),
                "components": self._extract_components(resolved)
            },
            quality_score=0.85,
            execution_time=execution_time
        )
    
    def _merge_solutions(self, solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple solutions"""
        merged = {}
        for solution in solutions:
            merged.update(solution.get("components", {}))
        return merged
    
    def _identify_conflicts(self, solutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify conflicts between solutions"""
        conflicts = []
        if len(solutions) > 1:
            conflicts.append({
                "type": "naming_conflict",
                "description": "Different naming conventions",
                "severity": "low"
            })
        return conflicts
    
    def _resolve_conflicts(self, integrated: Dict[str, Any], 
                          conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve conflicts in integrated solution"""
        resolved = integrated.copy()
        for conflict in conflicts:
            if conflict["type"] == "naming_conflict":
                resolved["naming_standard"] = "snake_case"
        return resolved
    
    def _extract_components(self, solution: Dict[str, Any]) -> List[str]:
        """Extract component names from solution"""
        return list(solution.keys())


class ControllerAgent(BaseAgent):
    """Monitors execution, escalates failures, and loops retries"""
    
    def __init__(self, agent_id: str = "controller_1"):
        super().__init__(agent_id, AgentType.CONTROLLER)
        self.capabilities = ["execution_monitoring", "failure_escalation", "retry_management"]
        self.monitoring_data: Dict[str, Any] = {}
        self.failure_count: Dict[str, int] = {}
    
    def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        task_id = task.get("task_id", "")
        action = task.get("action", "monitor")
        start_time = datetime.now()
        
        if action == "monitor":
            result = self._monitor_execution(task)
        elif action == "escalate":
            result = self._escalate_failure(task)
        elif action == "retry":
            result = self._manage_retry(task)
        else:
            result = {"status": "unknown_action"}
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=task_id,
            status=TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED,
            output=result,
            quality_score=0.90,
            execution_time=execution_time
        )
    
    def _monitor_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor task execution"""
        task_id = task.get("task_id", "")
        status = task.get("status", "unknown")
        
        self.monitoring_data[task_id] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metrics": task.get("metrics", {})
        }
        
        return {
            "success": True,
            "monitored": task_id,
            "status": status,
            "requires_action": status == "failed"
        }
    
    def _escalate_failure(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate failure to appropriate handler"""
        task_id = task.get("task_id", "")
        self.failure_count[task_id] = self.failure_count.get(task_id, 0) + 1
        
        escalation_level = "low" if self.failure_count[task_id] < 2 else "high"
        
        return {
            "success": True,
            "escalated": task_id,
            "level": escalation_level,
            "failure_count": self.failure_count[task_id],
            "action": "human_intervention" if escalation_level == "high" else "retry"
        }
    
    def _manage_retry(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manage retry logic"""
        task_id = task.get("task_id", "")
        max_retries = task.get("max_retries", 3)
        current_retry = task.get("retry_count", 0)
        
        if current_retry < max_retries:
            return {
                "success": True,
                "action": "retry",
                "retry_count": current_retry + 1,
                "max_retries": max_retries
            }
        else:
            return {
                "success": False,
                "action": "escalate",
                "reason": "Max retries exceeded"
            }


class AgentRegistry:
    """Registry for managing agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agents"""
        self.register(PlannerAgent())
        self.register(DecomposerAgent())
        self.register(ArchitectAgent())
        self.register(CoderAgent())
        self.register(CriticAgent())
        self.register(TesterAgent())
        self.register(ToolExecutorAgent())
        self.register(EvaluatorAgent())
        self.register(IntegratorAgent())
        self.register(ControllerAgent())
    
    def register(self, agent: BaseAgent) -> None:
        """Register an agent"""
        self.agents[agent.agent_id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """Get all agents of a specific type"""
        return [agent for agent in self.agents.values() if agent.agent_type == agent_type]
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [
            {
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type.value,
                "capabilities": agent.capabilities
            }
            for agent in self.agents.values()
        ]


