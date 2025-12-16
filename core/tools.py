from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Protocol, List


class ToolResultStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class ToolPermission(str, Enum):
    FILESYSTEM = "FILESYSTEM"
    PYTHON = "PYTHON"
    SHELL = "SHELL"
    GIT = "GIT"
    WEB = "WEB"


@dataclass
class ToolResult:
    status: ToolResultStatus
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Tool(Protocol):
    name: str
    permission: ToolPermission
    def run(self, **kwargs: Any) -> ToolResult: ...


class WebSearchTool:
    name = "web_search"
    permission = ToolPermission.WEB
    def run(self, query: str, **kwargs: Any) -> ToolResult:
        return ToolResult(status=ToolResultStatus.NOT_IMPLEMENTED, output=[], error="WebSearchTool stub")


class GitTool:
    name = "git"
    permission = ToolPermission.GIT
    def run(self, args: list[str], **kwargs: Any) -> ToolResult:
        return ToolResult(status=ToolResultStatus.NOT_IMPLEMENTED, output="", error="GitTool stub")


class PythonSandbox:
    name = "python_sandbox"
    permission = ToolPermission.PYTHON
    def run(self, command: list[str], cwd: Optional[str] = None, **kwargs: Any) -> ToolResult:
        import subprocess
        try:
            proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
            return ToolResult(
                status=ToolResultStatus.OK if proc.returncode == 0 else ToolResultStatus.ERROR,
                output={"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr},
            )
        except Exception as e:
            return ToolResult(status=ToolResultStatus.ERROR, error=str(e))


class ToolRegistry:
    def __init__(self, allowed: Optional[set[ToolPermission]] = None):
        self.allowed = allowed if allowed is not None else set(ToolPermission)
        self._tools: Dict[str, Any] = {}
        # default tools so smoke test passes
        self.register(PythonSandbox())

    def register(self, tool: Any) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Any:
        return self._tools[name]

    def list_tools(self) -> List[str]:
        return sorted(self._tools.keys())

    def run(self, name: str, **kwargs: Any) -> ToolResult:
        tool = self.get(name)
        perm = getattr(tool, "permission", None)
        if perm is not None and perm not in self.allowed:
            return ToolResult(status=ToolResultStatus.ERROR, error=f"Permission denied: {perm}")
        return tool.run(**kwargs)
