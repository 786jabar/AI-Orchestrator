import unittest
from core.automation import (
    AutomatedReviewer,
    ImprovementAutomation,
    SoftwareFactory,
    AutomationLevel,
    ReviewResult,
    ImprovementPlan
)
from core import OrchestratorPolicy, HumanApprovalManager, MilestoneType


class TestAutomatedReviewer(unittest.TestCase):
    
    def setUp(self):
        self.reviewer = AutomatedReviewer(quality_threshold=0.7)
    
    def test_review_output_passed(self):
        output = {
            "confidence": 0.85,
            "errors": [],
            "warnings": []
        }
        result = self.reviewer.review_output(output, {})
        self.assertTrue(result.passed)
        self.assertEqual(result.score, 0.85)
    
    def test_review_output_failed(self):
        output = {
            "confidence": 0.5,
            "errors": ["Error 1"],
            "warnings": ["Warning 1"]
        }
        result = self.reviewer.review_output(output, {})
        self.assertFalse(result.passed)
        self.assertGreater(len(result.issues), 0)
    
    def test_review_mission_result(self):
        result = {
            "status": "completed",
            "execution_summary": {"average_score": 0.8}
        }
        review = self.reviewer.review_mission_result(result)
        self.assertTrue(review.passed)
        self.assertEqual(review.score, 0.8)


class TestImprovementAutomation(unittest.TestCase):
    
    def setUp(self):
        self.improvement = ImprovementAutomation(max_iterations=3, target_score=0.8)
    
    def test_should_improve(self):
        self.assertTrue(self.improvement.should_improve(0.6, 0))
        self.assertFalse(self.improvement.should_improve(0.9, 0))
        self.assertFalse(self.improvement.should_improve(0.6, 3))
    
    def test_generate_improvement_plan(self):
        result = {
            "execution_summary": {"average_score": 0.6}
        }
        review = ReviewResult(passed=False, score=0.6, issues=["Issue 1"])
        plan = self.improvement.generate_improvement_plan(result, review, 0)
        self.assertIsInstance(plan, ImprovementPlan)
        self.assertGreater(len(plan.changes), 0)


class TestSoftwareFactory(unittest.TestCase):
    
    def setUp(self):
        approval_manager = HumanApprovalManager()
        approval_manager.register_auto_approve(MilestoneType.MISSION_PLAN)
        approval_manager.register_auto_approve(MilestoneType.FINAL_DELIVERY)
        
        policy = OrchestratorPolicy()
        self.factory = SoftwareFactory(
            policy=policy,
            approval_manager=approval_manager,
            automation_level=AutomationLevel.SEMI_AUTOMATED
        )
    
    def test_execute_with_automation(self):
        goal = "Build a test API"
        result = self.factory.execute_with_automation(goal)
        
        self.assertIn("status", result)
        self.assertIn("mission_id", result)
        if "review" in result:
            self.assertIsNotNone(result["review"])


if __name__ == "__main__":
    unittest.main()


