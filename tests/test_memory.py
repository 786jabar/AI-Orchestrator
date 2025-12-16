import unittest
from datetime import datetime
from core.memory import (
    ShortTermMemory,
    LongTermMemory,
    MemorySystem,
    TaskState,
    ProjectState,
    ProjectOutcome,
    OutcomeType,
    AgentPerformance
)


class TestShortTermMemory(unittest.TestCase):
    
    def setUp(self):
        self.memory = ShortTermMemory()
    
    def test_create_project_state(self):
        project = self.memory.create_project_state("mission_1", "Build web app")
        self.assertIsNotNone(project)
        self.assertEqual(project.mission_id, "mission_1")
        self.assertEqual(project.goal, "Build web app")
    
    def test_add_task(self):
        self.memory.create_project_state("mission_1", "Test goal")
        task = self.memory.add_task("mission_1", "task_1", "Implement feature")
        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, "task_1")
        self.assertEqual(task.status, "pending")
    
    def test_update_task_status(self):
        self.memory.create_project_state("mission_1", "Test goal")
        self.memory.add_task("mission_1", "task_1", "Test task")
        success = self.memory.update_task_status("task_1", "in_progress")
        self.assertTrue(success)
        task = self.memory.active_tasks["task_1"]
        self.assertEqual(task.status, "in_progress")
    
    def test_assign_agent_to_task(self):
        self.memory.create_project_state("mission_1", "Test goal")
        self.memory.add_task("mission_1", "task_1", "Test task")
        success = self.memory.assign_agent_to_task("task_1", "agent_1")
        self.assertTrue(success)
        self.assertEqual(self.memory.active_tasks["task_1"].assigned_agent, "agent_1")
    
    def test_add_task_output(self):
        self.memory.create_project_state("mission_1", "Test goal")
        self.memory.add_task("mission_1", "task_1", "Test task")
        output = {"result": "success", "data": "test"}
        success = self.memory.add_task_output("task_1", output)
        self.assertTrue(success)
        self.assertIn(output, self.memory.active_tasks["task_1"].outputs)


class TestLongTermMemory(unittest.TestCase):
    
    def setUp(self):
        self.memory = LongTermMemory()
    
    def test_record_project_outcome(self):
        outcome = ProjectOutcome(
            mission_id="mission_1",
            goal="Test project",
            outcome=OutcomeType.SUCCESS,
            tasks_count=5,
            successful_tasks=5
        )
        self.memory.record_project_outcome(outcome)
        self.assertIn("mission_1", self.memory.project_outcomes)
    
    def test_update_agent_performance(self):
        self.memory.update_agent_performance("agent_1", "developer", True, 10.5)
        perf = self.memory.get_agent_performance("agent_1")
        self.assertIsNotNone(perf)
        self.assertEqual(perf.tasks_completed, 1)
        self.assertEqual(perf.success_rate, 1.0)
    
    def test_get_best_agents_for_task(self):
        self.memory.update_agent_performance("agent_1", "developer", True)
        self.memory.update_agent_performance("agent_1", "developer", True)
        self.memory.update_agent_performance("agent_2", "developer", True)
        self.memory.update_agent_performance("agent_2", "developer", False)
        self.memory.add_agent_strength("agent_1", "backend")
        agents = self.memory.get_best_agents_for_task("backend", limit=2)
        self.assertGreaterEqual(len(agents), 1)
        self.assertEqual(agents[0].agent_id, "agent_1")
    
    def test_get_similar_past_projects(self):
        outcome1 = ProjectOutcome(
            mission_id="mission_1",
            goal="Build web application",
            outcome=OutcomeType.SUCCESS
        )
        outcome2 = ProjectOutcome(
            mission_id="mission_2",
            goal="Create mobile app",
            outcome=OutcomeType.SUCCESS
        )
        self.memory.record_project_outcome(outcome1)
        self.memory.record_project_outcome(outcome2)
        similar = self.memory.get_similar_past_projects("Build web app", limit=2)
        self.assertGreaterEqual(len(similar), 1)


class TestMemorySystem(unittest.TestCase):
    
    def setUp(self):
        self.memory = MemorySystem()
    
    def test_initialize_project(self):
        project = self.memory.initialize_project("mission_1", "Build web app")
        self.assertIsNotNone(project)
        self.assertEqual(project.mission_id, "mission_1")
    
    def test_guide_task_decomposition(self):
        outcome = ProjectOutcome(
            mission_id="mission_1",
            goal="Build web app",
            outcome=OutcomeType.SUCCESS,
            tasks_count=5,
            patterns_identified=["Use REST API", "Implement authentication"]
        )
        self.memory.long_term.record_project_outcome(outcome)
        guidance = self.memory.guide_task_decomposition("Build web application")
        self.assertIn("similar_projects", guidance)
        self.assertIn("recommended_approach", guidance)
    
    def test_record_mission_completion(self):
        project = self.memory.initialize_project("mission_1", "Test project")
        self.memory.short_term.add_task("mission_1", "task_1", "Test task")
        self.memory.record_mission_completion(
            "mission_1",
            OutcomeType.SUCCESS,
            project,
            completion_time=100.0
        )
        outcome = self.memory.long_term.get_project_outcome("mission_1")
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.outcome, OutcomeType.SUCCESS)


if __name__ == "__main__":
    unittest.main()


