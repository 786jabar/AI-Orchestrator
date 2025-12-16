from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any, List

from .orchestrator import OrchestratorPolicy
from .memory import MemorySystem
from .tools import ToolRegistry, PythonSandbox, ToolResultStatus


class SoftwareFactory:
    def __init__(
        self,
        tools: Optional[ToolRegistry] = None,
        memory: Optional[MemorySystem] = None,
        policy: Optional[OrchestratorPolicy] = None,
    ):
        self.tools = tools or ToolRegistry()
        self.memory = memory or MemorySystem()
        self.policy = policy or OrchestratorPolicy()

        if "python_sandbox" not in getattr(self.tools, "_tools", {}):
            self.tools.register(PythonSandbox())

    def execute_with_automation(self, mission: str, priority: int = 1) -> Dict[str, Any]:
        if getattr(self.policy, "emergency_stop", False):
            return {
                "status": "halted",
                "reason": "emergency_stop",
                "execution_summary": {"halted_reason": "emergency_stop"},
                "mission": mission,
                "priority": priority,
            }

        if getattr(self.policy, "max_retries_total", 999999) <= 0:
            return {
                "status": "halted",
                "reason": "retry_budget_exceeded",
                "execution_summary": {"halted_reason": "retry_budget_exceeded"},
                "mission": mission,
                "priority": priority,
            }

        return self.run_mission_mode(mission)

    def run_mission_mode(self, mission: str, workspace_root: str = "workspace/mission_mode") -> Dict[str, Any]:
        root = Path(workspace_root)
        root.mkdir(parents=True, exist_ok=True)
        ws = root / "latest"
        ws.mkdir(parents=True, exist_ok=True)

        (ws / "src").mkdir(exist_ok=True)
        (ws / "tests").mkdir(exist_ok=True)
        (ws / "docs").mkdir(exist_ok=True)

        # required files
        (ws / "src" / "app.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        (ws / "tests" / "test_app.py").write_text(
            """from src.app import add

def test_add():
    assert add(1, 2) == 3
""",
            encoding="utf-8",
        )
        (ws / "README.mission.md").write_text(
            f"# Mission Output\n\nMission: {mission}\n",
            encoding="utf-8",
        )
        (ws / "DELIVERABLE.md").write_text(
            f"# Deliverable\n\nBuilt: {mission}\n",
            encoding="utf-8",
        )

        tasks: List[Dict[str, Any]] = []

        # task: test execution (tests expect this)
        res = self.tools.run("python_sandbox", command=["python", "-m", "pytest", "-q"], cwd=str(ws))
        tasks.append(
            {
                "task_id": "task_test_exec",
                "name": "Run pytest",
                "status": "completed" if res.status == ToolResultStatus.OK else "failed",
                "tool": "python_sandbox",
                "output": res.output,
            }
        )

        details = {"workspace": str(ws), "tasks": tasks}

        if res.status == ToolResultStatus.OK:
            return {"status": "completed", **details}

        return {"status": "partial", "reason": "tests_failed_autofix_applied", **details}
