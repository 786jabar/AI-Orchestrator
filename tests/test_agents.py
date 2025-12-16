import unittest
import tempfile
import shutil
from pathlib import Path
from core.agents import (
    AgentType,
    TaskStatus,
    PlannerAgent,
    DecomposerAgent,
    ArchitectAgent,
    CoderAgent,
    CriticAgent,
    TesterAgent,
    ToolExecutorAgent,
    EvaluatorAgent,
    IntegratorAgent,
    ControllerAgent,
    AgentRegistry
)


class TestPlannerAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = PlannerAgent()
    
    def test_execute_task(self):
        task = {"task_id": "task_1", "goal": "Build web application"}
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("plan", result.output)
        self.assertIn("objectives", result.output["plan"])
    
    def test_report_status(self):
        status = self.agent.report_status("task_1")
        self.assertEqual(status["agent_id"], self.agent.agent_id)
        self.assertEqual(status["agent_type"], AgentType.PLANNER.value)


class TestDecomposerAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = DecomposerAgent()
    
    def test_execute_task(self):
        task = {
            "task_id": "task_1",
            "plan": {
                "phases": [
                    {"phase": "Design", "duration": "2 days"},
                    {"phase": "Implementation", "duration": "5 days"}
                ]
            }
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("tasks", result.output)
        self.assertIn("dependencies", result.output)


class TestArchitectAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = ArchitectAgent()
    
    def test_execute_task(self):
        task = {
            "task_id": "task_1",
            "requirements": ["Functional requirements", "Performance requirements"]
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("design", result.output)
        self.assertIn("architecture", result.output["design"])


class TestCoderAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = CoderAgent()
    
    def test_execute_task(self):
        task = {
            "task_id": "task_1",
            "specification": {"component": "api_service"}
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("code", result.output)
        self.assertGreater(len(result.output["code"]), 0)


class TestCriticAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = CriticAgent()
    
    def test_review_code(self):
        task = {
            "task_id": "task_1",
            "artifact_type": "code",
            "artifact": {"file.py": "def test(): pass"}
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("review", result.output)
        self.assertIn("issues", result.output["review"])


class TestTesterAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = TesterAgent()
    
    def test_execute_task(self):
        task = {
            "task_id": "task_1",
            "code": {"service.py": "class Service: pass"}
        }
        result = self.agent.execute_task(task)
        self.assertIn("tests", result.output)
        self.assertIn("test_results", result.output)


class TestToolExecutorAgent(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.agent = ToolExecutorAgent(work_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_shell_command(self):
        task = {
            "task_id": "task_1",
            "command": "echo 'test'",
            "command_type": "shell"
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertTrue(result.output.get("success"))
    
    def test_rollback(self):
        self.agent.execution_logs.append(
            type('obj', (object,), {
                'rollback_available': True,
                'command': 'test',
                'output': 'output',
                'exit_code': 0,
                'timestamp': None
            })()
        )
        self.assertTrue(self.agent.rollback(0))


class TestEvaluatorAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = EvaluatorAgent()
    
    def test_execute_task(self):
        task = {
            "task_id": "task_1",
            "output": {"result": "test"},
            "criteria": {"completeness": 1.0, "quality": 1.0}
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("scores", result.output)
        self.assertIn("overall_score", result.output)


class TestIntegratorAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = IntegratorAgent()
    
    def test_execute_task(self):
        task = {
            "task_id": "task_1",
            "solutions": [
                {"components": {"comp1": "impl1"}},
                {"components": {"comp2": "impl2"}}
            ]
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("integrated_solution", result.output)


class TestControllerAgent(unittest.TestCase):
    
    def setUp(self):
        self.agent = ControllerAgent()
    
    def test_monitor_execution(self):
        task = {
            "task_id": "task_1",
            "action": "monitor",
            "status": "in_progress"
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("monitored", result.output)
    
    def test_escalate_failure(self):
        task = {
            "task_id": "task_1",
            "action": "escalate"
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("escalated", result.output)
    
    def test_manage_retry(self):
        task = {
            "task_id": "task_1",
            "action": "retry",
            "retry_count": 1,
            "max_retries": 3
        }
        result = self.agent.execute_task(task)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIn("action", result.output)


class TestAgentRegistry(unittest.TestCase):
    
    def setUp(self):
        self.registry = AgentRegistry()
    
    def test_register_agent(self):
        agent = PlannerAgent("custom_planner")
        self.registry.register(agent)
        self.assertIsNotNone(self.registry.get_agent("custom_planner"))
    
    def test_get_agent(self):
        agent = self.registry.get_agent("planner_1")
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_type, AgentType.PLANNER)
    
    def test_get_agents_by_type(self):
        agents = self.registry.get_agents_by_type(AgentType.PLANNER)
        self.assertGreater(len(agents), 0)
        self.assertEqual(agents[0].agent_type, AgentType.PLANNER)
    
    def test_list_agents(self):
        agents = self.registry.list_agents()
        self.assertGreater(len(agents), 0)
        self.assertIn("agent_id", agents[0])
        self.assertIn("agent_type", agents[0])


if __name__ == "__main__":
    unittest.main()


