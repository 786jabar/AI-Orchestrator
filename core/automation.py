"""
Automation System for AI Software Factory
Automates execution, review, and improvement loops.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .execution_flow import ExecutionFlow
from .orchestrator import OrchestratorPolicy
from .human_approval import HumanApprovalManager, MilestoneType
from .memory import MemorySystem, OutcomeType


class AutomationLevel(Enum):
    """Automation level"""
    FULL_AUTOMATION = "full_automation"
    SEMI_AUTOMATED = "semi_automated"
    MANUAL = "manual"


@dataclass
class ReviewResult:
    """Result of automated review"""
    passed: bool
    score: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    requires_human_review: bool = False


@dataclass
class ImprovementPlan:
    """Plan for iterative improvement"""
    iteration: int
    target_score: float
    changes: List[Dict[str, Any]] = field(default_factory=list)
    rationale: str = ""


class AutomatedReviewer:
    """Automated code and design reviewer"""
    
    def __init__(self, quality_threshold: float = 0.7):
        self.quality_threshold = quality_threshold
    
    def review_output(self, output: Dict[str, Any], 
                     criteria: Dict[str, float]) -> ReviewResult:
        """Review agent output automatically"""
        score = output.get("confidence", 0.0)
        issues = output.get("errors", [])
        warnings = output.get("warnings", [])
        
        all_issues = issues + warnings
        passed = score >= self.quality_threshold and len(issues) == 0
        
        recommendations = []
        if score < self.quality_threshold:
            recommendations.append(f"Improve quality score (current: {score:.2f}, target: {self.quality_threshold})")
        if issues:
            recommendations.append("Fix critical errors before proceeding")
        if len(warnings) > 3:
            recommendations.append("Address multiple warnings")
        
        requires_human = score < 0.5 or len(issues) > 2
        
        return ReviewResult(
            passed=passed,
            score=score,
            issues=all_issues,
            recommendations=recommendations,
            requires_human_review=requires_human
        )
    
    def review_mission_result(self, result: Dict[str, Any]) -> ReviewResult:
        """Review complete mission result"""
        status = result.get("status", "unknown")
        summary = result.get("execution_summary", {})
        avg_score = summary.get("average_score", 0.0)
        
        passed = status == "completed" and avg_score >= self.quality_threshold
        issues = []
        
        if status != "completed":
            issues.append(f"Mission status: {status}")
        if avg_score < self.quality_threshold:
            issues.append(f"Average score below threshold: {avg_score:.2f}")
        
        recommendations = []
        if not passed:
            recommendations.append("Review failed tasks and retry")
            recommendations.append("Consider adjusting agent selection strategy")
        
        return ReviewResult(
            passed=passed,
            score=avg_score,
            issues=issues,
            recommendations=recommendations,
            requires_human_review=status == "failed" or avg_score < 0.6
        )


class ImprovementAutomation:
    """Automates iterative improvement loops"""
    
    def __init__(self, max_iterations: int = 3, target_score: float = 0.8):
        self.max_iterations = max_iterations
        self.target_score = target_score
        self.improvement_history: List[Dict[str, Any]] = []
    
    def should_improve(self, current_score: float, iteration: int) -> bool:
        """Determine if improvement iteration is needed"""
        if iteration >= self.max_iterations:
            return False
        if current_score >= self.target_score:
            return False
        return True
    
    def generate_improvement_plan(self, current_result: Dict[str, Any],
                                  review_result: ReviewResult,
                                  iteration: int) -> ImprovementPlan:
        """Generate plan for next improvement iteration"""
        summary = current_result.get("execution_summary", {})
        current_score = summary.get("average_score", 0.0)
        
        changes = []
        rationale = ""
        
        if review_result.score < self.target_score:
            changes.append({
                "type": "policy_adjustment",
                "description": "Adjust agent selection strategy based on performance"
            })
            rationale = f"Current score {current_score:.2f} below target {self.target_score}"
        
        if review_result.issues:
            changes.append({
                "type": "error_fix",
                "description": f"Address {len(review_result.issues)} identified issues"
            })
        
        if len(review_result.recommendations) > 0:
            changes.append({
                "type": "optimization",
                "description": "Apply recommended optimizations"
            })
        
        return ImprovementPlan(
            iteration=iteration + 1,
            target_score=self.target_score,
            changes=changes,
            rationale=rationale
        )
    
    def apply_improvements(self, flow: ExecutionFlow,
                          improvement_plan: ImprovementPlan) -> Dict[str, Any]:
        """Apply improvements and re-execute"""
        for change in improvement_plan.changes:
            if change["type"] == "policy_adjustment":
                if flow.orchestrator.policy.adaptive_learning_enabled:
                    flow.orchestrator.adaptive_orchestrator.adapt_agent_selection({})
        
        return {"improvements_applied": len(improvement_plan.changes)}


class SoftwareFactory:
    """AI Software Factory - Main automation orchestrator"""
    
    def __init__(self, 
                 policy: Optional[OrchestratorPolicy] = None,
                 approval_manager: Optional[HumanApprovalManager] = None,
                 automation_level: AutomationLevel = AutomationLevel.SEMI_AUTOMATED):
        self.flow = ExecutionFlow(policy, approval_manager)
        self.reviewer = AutomatedReviewer()
        self.improvement = ImprovementAutomation()
        self.automation_level = automation_level
        self.memory = MemorySystem()
    
    def execute_with_automation(self, goal: str, priority: int = 5,
                                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute mission with automated review and improvement"""
        iteration = 0
        best_result = None
        best_score = 0.0
        
        while iteration < self.improvement.max_iterations:
            result = self.flow.execute_mission(
                goal, 
                priority, 
                metadata,
                max_iterations=1
            )
            
            review = self.reviewer.review_mission_result(result)
            
            summary = result.get("execution_summary", {})
            current_score = summary.get("average_score", 0.0)
            
            if current_score > best_score:
                best_score = current_score
                best_result = result.copy()
                best_result["review"] = review
                best_result["iteration"] = iteration + 1
            
            if review.requires_human_review and self.automation_level != AutomationLevel.FULL_AUTOMATION:
                return {
                    **best_result,
                    "status": "requires_human_review",
                    "review": review
                }
            
            if review.passed or not self.improvement.should_improve(current_score, iteration):
                best_result["review"] = review
                best_result["final_iteration"] = iteration + 1
                return best_result
            
            improvement_plan = self.improvement.generate_improvement_plan(
                result, review, iteration
            )
            
            self.improvement.apply_improvements(self.flow, improvement_plan)
            self.improvement.improvement_history.append({
                "iteration": iteration + 1,
                "score": current_score,
                "plan": improvement_plan
            })
            
            iteration += 1
        
        if best_result:
            best_result["review"] = review
            best_result["final_iteration"] = iteration
            return best_result
        
        return {
            "status": "failed",
            "error": "Max iterations reached",
            "review": review
        }
    
    def get_improvement_history(self) -> List[Dict[str, Any]]:
        """Get improvement iteration history"""
        return self.improvement.improvement_history


