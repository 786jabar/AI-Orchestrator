import unittest
from core.human_approval import (
    HumanApprovalManager,
    MilestoneType,
    ApprovalStatus,
    ApprovalRequest
)


class TestHumanApprovalManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = HumanApprovalManager()
    
    def test_request_approval(self):
        request = self.manager.request_approval(
            MilestoneType.MISSION_PLAN,
            "mission_1",
            "Test plan",
            {"plan": "test"}
        )
        self.assertIsNotNone(request)
        self.assertEqual(request.status, ApprovalStatus.PENDING)
        self.assertEqual(request.milestone_type, MilestoneType.MISSION_PLAN)
    
    def test_approve(self):
        request = self.manager.request_approval(
            MilestoneType.MISSION_PLAN,
            "mission_1",
            "Test plan",
            {"plan": "test"}
        )
        result = self.manager.approve(request.request_id, "human_user")
        self.assertTrue(result)
        self.assertEqual(request.status, ApprovalStatus.APPROVED)
    
    def test_reject(self):
        request = self.manager.request_approval(
            MilestoneType.MISSION_PLAN,
            "mission_1",
            "Test plan",
            {"plan": "test"}
        )
        result = self.manager.reject(request.request_id, "human_user", "Not good")
        self.assertTrue(result)
        self.assertEqual(request.status, ApprovalStatus.REJECTED)
    
    def test_auto_approve(self):
        self.manager.register_auto_approve(MilestoneType.MISSION_PLAN)
        request = self.manager.request_approval(
            MilestoneType.MISSION_PLAN,
            "mission_1",
            "Test plan",
            {"plan": "test"}
        )
        self.assertEqual(request.status, ApprovalStatus.AUTO_APPROVED)
    
    def test_is_approved(self):
        request = self.manager.request_approval(
            MilestoneType.MISSION_PLAN,
            "mission_1",
            "Test plan",
            {"plan": "test"}
        )
        self.assertFalse(self.manager.is_approved(request.request_id))
        
        self.manager.approve(request.request_id, "user")
        self.assertTrue(self.manager.is_approved(request.request_id))
    
    def test_get_pending_requests(self):
        self.manager.request_approval(
            MilestoneType.MISSION_PLAN,
            "mission_1",
            "Plan 1",
            {}
        )
        self.manager.request_approval(
            MilestoneType.ARCHITECTURE_DESIGN,
            "mission_1",
            "Design 1",
            {}
        )
        
        pending = self.manager.get_pending_requests("mission_1")
        self.assertEqual(len(pending), 2)


if __name__ == "__main__":
    unittest.main()


