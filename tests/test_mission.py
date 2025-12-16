import unittest
from core.mission import CoreMission, Mission, MissionStatus, Role


class TestCoreMission(unittest.TestCase):
    
    def setUp(self):
        self.mission_system = CoreMission()
    
    def test_define_mission(self):
        mission_id = self.mission_system.define_mission("Build web application", priority=8)
        self.assertIsNotNone(mission_id)
        self.assertTrue(mission_id.startswith("mission_"))
    
    def test_get_mission(self):
        mission_id = self.mission_system.define_mission("Test goal")
        mission = self.mission_system.get_mission(mission_id)
        self.assertIsNotNone(mission)
        self.assertEqual(mission.goal, "Test goal")
        self.assertEqual(mission.status, MissionStatus.PENDING)
    
    def test_update_mission_status(self):
        mission_id = self.mission_system.define_mission("Test goal")
        success = self.mission_system.update_mission_status(mission_id, MissionStatus.IN_PROGRESS)
        self.assertTrue(success)
        mission = self.mission_system.get_mission(mission_id)
        self.assertEqual(mission.status, MissionStatus.IN_PROGRESS)
    
    def test_validate_mission(self):
        valid_mission = Mission(goal="Valid goal")
        invalid_mission = Mission(goal="")
        self.assertTrue(self.mission_system.validate_mission(valid_mission))
        self.assertFalse(self.mission_system.validate_mission(invalid_mission))
    
    def test_get_role_responsibility(self):
        responsibility = self.mission_system.get_role_responsibility(Role.PRODUCT_OWNER)
        self.assertIsInstance(responsibility, str)
        self.assertGreater(len(responsibility), 0)


if __name__ == "__main__":
    unittest.main()


