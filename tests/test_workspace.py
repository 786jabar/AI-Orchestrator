import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "orchestrator"))


@pytest.fixture
async def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    projects = tmp_path / "projects"
    projects.mkdir()
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("PROJECTS_ROOT", str(projects))

    from app.config import get_settings

    get_settings.cache_clear()

    from app import db as dbmod
    from app.db import init_db
    from app.main import app
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    dbmod.engine = create_async_engine(get_settings().database_url, echo=False)
    dbmod.SessionLocal = async_sessionmaker(dbmod.engine, expire_on_commit=False)
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    get_settings.cache_clear()


def test_classify_and_route():
    from app.models import AiProvider, TaskCategory
    from app.services.routing import classify_task, route_provider

    assert classify_task("Please debug this stack trace") == TaskCategory.debugging
    provider, manual = route_provider(TaskCategory.ui_generation)
    assert provider == AiProvider.gemini and manual is False


def test_smart_context_ranks_files():
    from app.services.context import build_smart_context, rank_files

    files = {
        "index.js": "server listen html",
        "test.js": "assert equal",
        "README.md": "docs",
        "misc.txt": "zzzz",
    }
    ranked = rank_files("improve html ui layout", files, limit=3)
    assert ranked[0][0] in {"index.js", "README.md"}
    ctx = build_smart_context("improve html ui", files, ["[user] hi"], [])
    assert "Relevant project files" in ctx


@pytest.mark.asyncio
async def test_project_workspace_flow(client):
    created = await client.post("/api/projects", json={"name": "Alpha", "description": "test"})
    assert created.status_code == 200, created.text
    pid = created.json()["id"]

    task = await client.post(
        f"/api/projects/{pid}/tasks",
        json={
            "prompt": "Implement a hello endpoint",
            "provider_override": "mock",
            "use_tools": True,
            "auto_improve": False,
        },
    )
    assert task.status_code == 200, task.text
    body = task.json()
    assert body["status"] == "completed"
    assert body["quality_score"] > 0

    snap = await client.post(f"/api/projects/{pid}/snapshots", json={"label": "checkpoint"})
    assert snap.status_code == 200
    snaps = await client.get(f"/api/projects/{pid}/snapshots")
    assert len(snaps.json()) >= 1

    mem = await client.get(f"/api/projects/{pid}/memory")
    assert len(mem.json()) >= 2


@pytest.mark.asyncio
async def test_approval_gated_diffs(client):
    created = await client.post("/api/projects", json={"name": "Beta"})
    pid = created.json()["id"]
    task = await client.post(
        f"/api/projects/{pid}/tasks",
        json={
            "prompt": "Build a status page",
            "provider_override": "mock",
            "require_approval": True,
            "auto_improve": False,
        },
    )
    assert task.status_code == 200, task.text
    changes = await client.get(f"/api/projects/{pid}/changes")
    assert changes.status_code == 200
    pending = changes.json()
    assert len(pending) >= 1
    applied = await client.post(f"/api/projects/{pid}/changes/{pending[0]['id']}/apply")
    assert applied.status_code == 200
    assert applied.json()["status"] == "applied"
