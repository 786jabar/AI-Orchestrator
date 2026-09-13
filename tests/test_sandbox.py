import importlib.util
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]


def load_sandbox_app(monkeypatch, sandbox_root: Path):
    monkeypatch.setenv("SANDBOX_ROOT", str(sandbox_root))
    module_path = ROOT / "services" / "sandbox" / "app" / "main.py"
    # Avoid colliding with orchestrator's app.main on sys.path
    for key in list(sys.modules):
        if key == "app" or key.startswith("app."):
            del sys.modules[key]
    spec = importlib.util.spec_from_file_location("sandbox_main", module_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sandbox_main"] = mod
    # Ensure relative package imports inside sandbox aren't required — it's a flat module.
    # The sandbox main uses relative-free imports only.
    spec.loader.exec_module(mod)
    return mod.app


@pytest.mark.asyncio
async def test_sandbox_execute(tmp_path, monkeypatch):
    app = load_sandbox_app(monkeypatch, tmp_path / "sandboxes")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        result = await client.post(
            "/execute",
            json={
                "project_id": 1,
                "files": {"index.js": "console.log('sandbox-ok')\n"},
                "command": "node index.js",
                "timeout_seconds": 10,
            },
        )
        assert result.status_code == 200, result.text
        body = result.json()
        assert body["exit_code"] == 0
        assert "sandbox-ok" in body["stdout"]
