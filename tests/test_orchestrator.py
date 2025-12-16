import unittest
from core.orchestrator import (
    OrchestratorIntelligence,
    OrchestratorPolicy,
    OrchestratorState,
    TaskPriority,
    RetryStrategy,
    FallbackStrategy,
    StoppingCondition,
    StoppingConditionConfig,
    StateMachine,
    CreditAssignment,
    PolicyEngine,
    AdaptiveOrchestrator,
    StoppingConditionManager
)


class TestStateMachine(unittest.TestCase):
    
    def setUp(self):
        self.sm = StateMachine()
    
    def test_initial_state(self):
        self.assertEqual(self.sm.get_state(), OrchestratorState.IDLE)
    
    def test_valid_transition(self):
        result = self.sm.transition(OrchestratorState.PLANNING)
        self.assertTrue(result)
        self.assertEqual(self.sm.get_state(), OrchestratorState.PLANNING)
    
    def test_invalid_transition(self):
        self.sm.transition(OrchestratorState.PLANNING)
        result = self.sm.transition(OrchestratorState.COMPLETED)
        self.assertFalse(result)
    
    def test_can_transition_to(self):
        self.assertTrue(self.sm.can_transition_to(OrchestratorState.PLANNING))
        self.assertFalse(self.sm.can_transition_to(OrchestratorState.COMPLETED))


class TestCreditAssignment(unittest.TestCase):
    
    def setUp(self):
        self.ca = CreditAssignment()
    
    def test_assign_credit_success(self):
        credit = self.ca.assign_credit("agent_1", "task_1", "mission_1", True, 0.9)
        self.assertEqual(credit.success_credit, 1.0)
        self.assertEqual(credit.failure_credit, 0.0)
    
    def test_assign_credit_failure(self):
        credit = self.ca.assign_credit("agent_1", "task_1", "mission_1", False, 0.3)
        self.assertEqual(credit.success_credit, 0.0)
        self.assertEqual(credit.failure_credit, 1.0)
    
    def test_get_agent_total_credit(self):
        self.ca.assign_credit("agent_1", "task_1", "mission_1", True, 0.9)
        self.ca.assign_credit("agent_1", "task_2", "mission_1", True, 0.8)
        total = self.ca.get_agent_total_credit("agent_1")
        self.assertGreater(total, 0.0)
    
    def test_get_agent_success_rate(self):
        self.ca.assign_credit("agent_1", "task_1", "mission_1", True)
        self.ca.assign_credit("agent_1", "task_2", "mission_1", True)
        self.ca.assign_credit("agent_1", "task_3", "mission_1", False)
        rate = self.ca.get_agent_success_rate("agent_1")
        self.assertAlmostEqual(rate, 2/3, places=2)


class TestPolicyEngine(unittest.TestCase):
    
    def setUp(self):
        policy = OrchestratorPolicy()
        self.engine = PolicyEngine(policy)
    
    def test_select_agent_performance_based(self):
        agents = [
            {"agent_id": "agent_1", "type": "developer"},
            {"agent_id": "agent_2", "type": "developer"}
        ]
        performance = {
            "agent_1": {"success_rate": 0.9, "quality_score": 0.8},
            "agent_2": {"success_rate": 0.7, "quality_score": 0.6}
        }
        selected = self.engine.select_agent("dev", "test", agents, performance)
        self.assertEqual(selected, "agent_1")
    
    def test_prioritize_tasks_dependency_aware(self):
        tasks = [
            {"task_id": "task_1", "description": "Task 1"},
            {"task_id": "task_2", "description": "Task 2"}
        ]
        dependencies = {"task_2": ["task_1"]}
        prioritized = self.engine.prioritize_tasks(tasks, dependencies)
        self.assertEqual(prioritized[0]["task_id"], "task_1")
    
    def test_should_retry(self):
        self.assertTrue(self.engine.should_retry("task_1", 0))
        self.assertTrue(self.engine.should_retry("task_1", 2))
        self.assertFalse(self.engine.should_retry("task_1", 3))
    
    def test_get_retry_delay_exponential(self):
        delay1 = self.engine.get_retry_delay(1, RetryStrategy.EXPONENTIAL_BACKOFF)
        delay2 = self.engine.get_retry_delay(2, RetryStrategy.EXPONENTIAL_BACKOFF)
        self.assertGreater(delay2, delay1)


class TestAdaptiveOrchestrator(unittest.TestCase):
    
    def setUp(self):
        policy = OrchestratorPolicy(adaptive_learning_enabled=True)
        engine = PolicyEngine(policy)
        ca = CreditAssignment()
        self.adaptive = AdaptiveOrchestrator(engine, ca)
    
    def test_adapt_agent_selection(self):
        performance = {
            "agent_1": {"success_rate": 0.9, "quality_score": 0.8}
        }
        self.adaptive.adapt_agent_selection(performance)
        self.assertIn("agent_1", self.adaptive.adaptation_weights)
    
    def test_get_adaptive_agent_score(self):
        self.adaptive.adaptation_weights["agent_1"] = 0.9
        score = self.adaptive.get_adaptive_agent_score("agent_1", 0.8)
        self.assertAlmostEqual(score, 0.72, places=2)


class TestStoppingConditionManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = StoppingConditionManager()
    
    def test_add_condition(self):
        condition = StoppingConditionConfig(
            StoppingCondition.CONFIDENCE_THRESHOLD,
            0.8
        )
        self.manager.add_condition(condition)
        self.assertEqual(len(self.manager.conditions), 1)
    
    def test_check_confidence_threshold(self):
        condition = StoppingConditionConfig(
            StoppingCondition.CONFIDENCE_THRESHOLD,
            0.8
        )
        self.manager.add_condition(condition)
        result = self.manager.check_conditions({"confidence": 0.9})
        self.assertEqual(result, StoppingCondition.CONFIDENCE_THRESHOLD)
    
    def test_check_max_iterations(self):
        condition = StoppingConditionConfig(
            StoppingCondition.MAX_ITERATIONS,
            5
        )
        self.manager.add_condition(condition)
        for i in range(6):
            result = self.manager.check_conditions({})
        self.assertEqual(result, StoppingCondition.MAX_ITERATIONS)


class TestOrchestratorIntelligence(unittest.TestCase):
    
    def setUp(self):
        policy = OrchestratorPolicy()
        self.orchestrator = OrchestratorIntelligence(policy)
    
    def test_start_mission(self):
        result = self.orchestrator.start_mission("mission_1")
        self.assertTrue(result)
        self.assertEqual(self.orchestrator.get_state(), OrchestratorState.PLANNING)
    
    def test_decompose_mission(self):
        self.orchestrator.start_mission("mission_1")
        tasks = self.orchestrator.decompose_mission("mission_1", "Test goal")
        self.assertGreater(len(tasks), 0)
    
    def test_assign_tasks(self):
        self.orchestrator.start_mission("mission_1")
        tasks = self.orchestrator.decompose_mission("mission_1", "Test goal")
        agents = [
            {"agent_id": "agent_1", "type": "developer"},
            {"agent_id": "agent_2", "type": "developer"}
        ]
        performance = {
            "agent_1": {"success_rate": 0.9, "quality_score": 0.8}
        }
        assignments = self.orchestrator.assign_tasks("mission_1", tasks, agents, performance)
        self.assertGreater(len(assignments), 0)
    
    def test_assign_credit(self):
        credit = self.orchestrator.assign_credit("agent_1", "task_1", "mission_1", True, 0.9)
        self.assertIsNotNone(credit)
        self.assertEqual(credit.agent_id, "agent_1")
    
    def test_get_agent_credits(self):
        self.orchestrator.assign_credit("agent_1", "task_1", "mission_1", True, 0.9)
        credits = self.orchestrator.get_agent_credits("agent_1")
        self.assertIn("total_credit", credits)
        self.assertIn("success_rate", credits)


if __name__ == "__main__":
    unittest.main()

