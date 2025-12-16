import unittest
from core import (
    ExecutionFlow,
    OrchestratorPolicy,
    HumanApprovalManager,
    MilestoneType,
    MemorySystem,
    CoreMission,
    MissionStatus
)


class TestFullExecutionCycle(unittest.TestCase):
    
    def setUp(self):
        approval_manager = HumanApprovalManager()
        approval_manager.register_auto_approve(MilestoneType.MISSION_PLAN)
        approval_manager.register_auto_approve(MilestoneType.FINAL_DELIVERY)
        
        policy = OrchestratorPolicy()
        self.flow = ExecutionFlow(policy, approval_manager)
    
    def test_full_cycle_mission_to_completion(self):
        goal = "Build a REST API endpoint for user registration"
        
        result = self.flow.execute_mission(goal, priority=8)
        
        self.assertEqual(result["status"], "completed")
        self.assertIn("mission_id", result)
        self.assertIn("execution_summary", result)
        
        mission_id = result["mission_id"]
        
        mission = self.flow.mission_system.get_mission(mission_id)
        self.assertIsNotNone(mission)
        self.assertEqual(mission.status, MissionStatus.COMPLETED)
        
        project_state = self.flow.memory_system.short_term.get_project_state(mission_id)
        if project_state:
            self.assertGreater(len(project_state.tasks), 0)
        
        outcome = self.flow.memory_system.long_term.get_project_outcome(mission_id)
        self.assertIsNotNone(outcome)
    
    def test_cycle_components_sequence(self):
        goal = "Create a simple calculator"
        
        mission_id = self.flow.mission_system.define_mission(goal)
        self.assertIsNotNone(mission_id)
        
        project_state = self.flow.memory_system.initialize_project(mission_id, goal)
        self.assertIsNotNone(project_state)
        
        self.flow.orchestrator.start_mission(mission_id)
        self.assertEqual(self.flow.orchestrator.get_state().value, "planning")
        
        result = self.flow.execute_mission(goal)
        self.assertEqual(result["status"], "completed")
    
    def test_human_approval_in_cycle(self):
        approval_manager = HumanApprovalManager()
        approval_manager.register_auto_approve(MilestoneType.MISSION_PLAN)
        approval_manager.register_auto_approve(MilestoneType.FINAL_DELIVERY)
        
        policy = OrchestratorPolicy()
        flow = ExecutionFlow(policy, approval_manager)
        
        goal = "Test approval cycle"
        result = flow.execute_mission(goal)
        
        approvals = approval_manager.get_approval_history(result["mission_id"])
        self.assertGreater(len(approvals), 0)
        
        for approval in approvals:
            self.assertIn(approval.status.value, ["approved", "auto_approved"])
    
    def test_memory_storage_after_completion(self):
        goal = "Test memory storage"
        result = self.flow.execute_mission(goal)
        mission_id = result["mission_id"]
        
        outcome = self.flow.memory_system.long_term.get_project_outcome(mission_id)
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.mission_id, mission_id)
        self.assertEqual(outcome.goal, goal)
        self.assertGreater(outcome.tasks_count, 0)


if __name__ == "__main__":
    unittest.main()


