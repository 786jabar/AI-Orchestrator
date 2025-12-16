import unittest

from core import (
    CoreMission,
    MissionStatus,
    MemorySystem,
    OrchestratorIntelligence,
    AgentRegistry,
    ToolRegistry,
)


class TestSmoke(unittest.TestCase):
    def test_mission_create(self):
        cm = CoreMission()
        mid = cm.define_mission('test goal')
        m = cm.get_mission(mid)
        self.assertIsNotNone(m)
        self.assertEqual(m.status, MissionStatus.PENDING)

    def test_memory(self):
        mem = MemorySystem()
        ps = mem.initialize_project('m1', 'goal')
        self.assertEqual(ps.mission_id, 'm1')

    def test_orchestrator_state(self):
        orch = OrchestratorIntelligence()
        self.assertTrue(orch.start_mission('m1'))

    def test_agents_registry(self):
        reg = AgentRegistry()
        self.assertGreater(len(reg.list_agents()), 0)

    def test_tools_registry(self):
        reg = ToolRegistry()
        self.assertGreater(len(reg.list_tools()), 0)


def test_collection_sanity():
    assert True


if __name__ == '__main__':
    unittest.main()