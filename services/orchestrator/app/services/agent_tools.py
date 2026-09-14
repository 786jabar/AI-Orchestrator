from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from . import vfs
from .sandbox_client import run_in_sandbox


@dataclass
class ToolResult:
    name: str
    ok: bool
    output: str
    data: dict = field(default_factory=dict)


async def tool_list_files(db: AsyncSession, project_id: int) -> ToolResult:
    files = await vfs.list_files(db, project_id)
    listing = "\n".join(
        ("dir  " if f.is_directory else "file ") + f.path for f in files
    )
    return ToolResult("list_files", True, listing or "(empty)", {"count": len(files)})


async def tool_read_file(db: AsyncSession, project_id: int, path: str) -> ToolResult:
    try:
        file = await vfs.get_file(db, project_id, path)
    except ValueError as exc:
        return ToolResult("read_file", False, str(exc))
    if not file or file.is_directory:
        return ToolResult("read_file", False, f"File not found: {path}")
    return ToolResult("read_file", True, file.content, {"path": path})


async def tool_write_file(
    db: AsyncSession, project_id: int, path: str, content: str
) -> ToolResult:
    try:
        await vfs.upsert_file(db, project_id, path, content)
    except ValueError as exc:
        return ToolResult("write_file", False, str(exc))
    return ToolResult("write_file", True, f"Wrote {path} ({len(content)} bytes)", {"path": path})


async def tool_run_tests(db: AsyncSession, project_id: int) -> ToolResult:
    files = await vfs.export_tree(db, project_id)
    command = "node --test test.js 2>&1 || node test.js 2>&1 || echo 'No tests found'"
    try:
        result = await run_in_sandbox(
            project_id=project_id, files=files, command=command, timeout_seconds=25
        )
    except Exception as exc:  # noqa: BLE001
        return ToolResult("run_tests", False, str(exc))
    ok = result.get("exit_code", 1) == 0
    out = (result.get("stdout") or "") + (result.get("stderr") or "")
    return ToolResult("run_tests", ok, out[-8000:], result)


TOOL_SPEC = """
You may request tools using this exact XML-ish form (one or more):
<tool name="list_files" />
<tool name="read_file"><path>index.js</path></tool>
<tool name="write_file"><path>index.js</path><content><![CDATA[
...file contents...
]]></content></tool>
<tool name="run_tests" />
When finished, provide the final answer and any remaining file edits as ```path fenced blocks.
"""


_TOOL_RE = re.compile(
    r'<tool\s+name="(?P<name>list_files|read_file|write_file|run_tests)"\s*(?:/>|>(?P<body>.*?)</tool>)',
    re.DOTALL,
)


async def execute_tool_requests(
    db: AsyncSession, project_id: int, model_text: str
) -> tuple[list[ToolResult], str]:
    results: list[ToolResult] = []
    for match in _TOOL_RE.finditer(model_text):
        name = match.group("name")
        body = match.group("body") or ""
        if name == "list_files":
            results.append(await tool_list_files(db, project_id))
        elif name == "read_file":
            path_m = re.search(r"<path>(.*?)</path>", body, re.DOTALL)
            path = (path_m.group(1).strip() if path_m else "").strip()
            results.append(await tool_read_file(db, project_id, path))
        elif name == "write_file":
            path_m = re.search(r"<path>(.*?)</path>", body, re.DOTALL)
            content_m = re.search(
                r"<content>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</content>", body, re.DOTALL
            )
            path = (path_m.group(1).strip() if path_m else "").strip()
            content = content_m.group(1) if content_m else ""
            results.append(await tool_write_file(db, project_id, path, content))
        elif name == "run_tests":
            results.append(await tool_run_tests(db, project_id))
    report = "\n\n".join(
        f"[tool:{r.name}] {'ok' if r.ok else 'ERR'}\n{r.output[:4000]}" for r in results
    )
    return results, report


def strip_tool_markup(text: str) -> str:
    return _TOOL_RE.sub("", text).strip()
