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
    provider, manual = route_provider(TaskCategory.ui_generation, AiProvider.claude)
    assert provider == AiProvider.claude and manual is True


def test_parse_file_blocks():
    from app.services.providers import parse_file_blocks

    md = "Here you go\n```index.js\nconsole.log('hi')\n```\n"
    assert parse_file_blocks(md)["index.js"].startswith("console.log")


@pytest.mark.asyncio
async def test_project_workspace_flow(client):
    created = await client.post("/api/projects", json={"name": "Alpha", "description": "test"})
    assert created.status_code == 200, created.text
    project = created.json()
    pid = project["id"]

    files = await client.get(f"/api/projects/{pid}/files")
    paths = {f["path"] for f in files.json()}
    assert "index.js" in paths

    saved = await client.put(
        f"/api/projects/{pid}/files",
        json={"path": "hello.js", "content": "console.log(1)\n"},
    )
    assert saved.status_code == 200
    read = await client.get(f"/api/projects/{pid}/files/content", params={"path": "hello.js"})
    assert read.json()["content"] == "console.log(1)\n"

    task = await client.post(
        f"/api/projects/{pid}/tasks",
        json={"prompt": "Implement a hello endpoint", "provider_override": "mock"},
    )
    assert task.status_code == 200, task.text
    body = task.json()
    assert body["status"] == "completed"
    assert body["assigned_provider"] == "mock"
