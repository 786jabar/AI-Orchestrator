import unittest
from core.execution_flow import ExecutionFlow, ExecutionContext
from core.orchestrator import OrchestratorPolicy
from core.mission import MissionStatus
from core.human_approval import HumanApprovalManager, MilestoneType


class TestExecutionFlow(unittest.TestCase):
    
    def setUp(self):
        approval_manager = HumanApprovalManager()
        approval_manager.register_auto_approve(MilestoneType.MISSION_PLAN)
        approval_manager.register_auto_approve(MilestoneType.FINAL_DELIVERY)
        self.flow = ExecutionFlow(approval_manager=approval_manager)
    
    def test_execute_mission(self):
        goal = "Build a simple web API"
        result = self.flow.execute_mission(goal)
        
        self.assertIn("mission_id", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "completed")
        self.assertIn("result", result)
        self.assertIn("execution_summary", result)
    
    def test_phase_planning(self):
        goal = "Create a calculator app"
        mission_id = self.flow.mission_system.define_mission(goal)
        self.flow.execution_context = ExecutionContext(mission_id=mission_id, goal=goal)
        
        plan = self.flow._phase_planning(goal)
        self.assertIsNotNone(plan)
        self.assertIn("objectives", plan)
        self.assertIn("requirements", plan)
    
    def test_phase_decomposition(self):
        goal = "Build web app"
        mission_id = self.flow.mission_system.define_mission(goal)
        self.flow.execution_context = ExecutionContext(mission_id=mission_id, goal=goal)
        
        plan = {
            "phases": [
                {"phase": "Design", "duration": "2 days"},
                {"phase": "Implementation", "duration": "5 days"}
            ]
        }
        
        tasks = self.flow._phase_decomposition(plan)
        self.assertGreater(len(tasks), 0)
        self.assertIn("task_id", tasks[0])
    
    def test_controller_select_agent(self):
        goal = "Test goal"
        mission_id = self.flow.mission_system.define_mission(goal)
        self.flow.execution_context = ExecutionContext(mission_id=mission_id, goal=goal)
        
        task_data = {
            "task_id": "task_1",
            "description": "Implement feature",
            "type": "coding"
        }
        
        agent = self.flow._controller_select_agent(task_data)
        self.assertIsNotNone(agent)
    
    def test_format_agent_output(self):
        from core.agents import AgentResult, TaskStatus, AgentType
        from datetime import datetime
        
        result = AgentResult(
            agent_id="test_agent",
            agent_type=AgentType.CODER,
            task_id="task_1",
            status=TaskStatus.COMPLETED,
            output={"code": "test"},
            quality_score=0.85
        )
        
        formatted = self.flow._format_agent_output(result, "coder")
        self.assertIn("status", formatted)
        self.assertIn("results", formatted)
        self.assertIn("confidence", formatted)
        self.assertEqual(formatted["confidence"], 0.85)
    
    def test_evaluate_output(self):
        goal = "Test goal"
        mission_id = self.flow.mission_system.define_mission(goal)
        self.flow.execution_context = ExecutionContext(mission_id=mission_id, goal=goal)
        
        output = {
            "status": "completed",
            "results": {"result": "test"},
            "confidence": 0.8
        }
        
        evaluator = self.flow.agent_registry.get_agent("evaluator_1")
        task_data = {"task_id": "task_1"}
        
        evaluation = self.flow._evaluate_output(output, evaluator, task_data)
        self.assertIn("overall_score", evaluation)
        self.assertIn("scores", evaluation)
    
    def test_controller_decide_action(self):
        from core.agents import AgentResult, TaskStatus, AgentType
        
        goal = "Test goal"
        mission_id = self.flow.mission_system.define_mission(goal)
        self.flow.execution_context = ExecutionContext(mission_id=mission_id, goal=goal)
        
        agent_result = AgentResult(
            agent_id="test",
            agent_type=AgentType.CODER,
            task_id="task_1",
            status=TaskStatus.COMPLETED,
            output={},
            quality_score=0.8
        )
        
        evaluation = {"overall_score": 0.85}
        controller = self.flow.agent_registry.get_agent("controller_1")
        
        decision = self.flow._controller_decide_action(agent_result, evaluation, controller)
        self.assertIn("action", decision)
        self.assertEqual(decision["action"], "continue")
    
    def test_get_execution_status(self):
        goal = "Build test app"
        result = self.flow.execute_mission(goal)
        mission_id = result["mission_id"]
        
        status = self.flow.get_execution_status(mission_id)
        self.assertIn("mission_id", status)
        self.assertIn("status", status)
        self.assertIn("tasks", status)
    
    def test_memory_recording(self):
        goal = "Test memory recording"
        result = self.flow.execute_mission(goal)
        mission_id = result["mission_id"]
        
        outcome = self.flow.memory_system.long_term.get_project_outcome(mission_id)
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.mission_id, mission_id)
        self.assertEqual(outcome.goal, goal)


if __name__ == "__main__":
    unittest.main()

