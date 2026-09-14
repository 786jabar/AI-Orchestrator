from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import Project, ProjectFile


STARTER_FILES: dict[str, str] = {
    "package.json": """{
  "name": "orchestrator-project",
  "version": "1.0.0",
  "private": true,
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "node --test"
  }
}
""",
    "index.js": """const http = require("http");

const port = process.env.PORT || 3000;
const html = `<!doctype html>
<html>
  <head><title>AI Orchestrator Project</title></head>
  <body style="font-family: system-ui; padding: 2rem;">
    <h1>Hello from your shared workspace</h1>
    <p>Edit <code>index.js</code> and run the sandbox preview.</p>
  </body>
</html>`;

if (process.env.FORGELINK_ONCE === "1") {
  process.stdout.write(html);
  process.exit(0);
}

const server = http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(html);
});

server.listen(port, () => {
  console.log(`Server listening on http://127.0.0.1:${port}`);
});
""",
    "README.md": """# Project Workspace

This Node.js project is managed by the AI Orchestrator Platform.
All AI agents read and write these shared files.
""",
}


def disk_root_for(project_id: int) -> Path:
    root = Path(get_settings().projects_root) / str(project_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def normalize_path(path: str) -> str:
    cleaned = path.replace("\\", "/").lstrip("/")
    parts = [p for p in cleaned.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise ValueError("Path traversal is not allowed")
    return "/".join(parts)


async def seed_project_files(db: AsyncSession, project: Project) -> None:
    root = disk_root_for(project.id)
    for path, content in STARTER_FILES.items():
        await upsert_file(db, project.id, path, content, is_directory=False, sync_disk=True)
    (root / "src").mkdir(exist_ok=True)
    await upsert_file(db, project.id, "src", "", is_directory=True, sync_disk=False)


async def list_files(db: AsyncSession, project_id: int) -> list[ProjectFile]:
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id).order_by(ProjectFile.path)
    )
    return list(result.scalars().all())


async def get_file(db: AsyncSession, project_id: int, path: str) -> ProjectFile | None:
    path = normalize_path(path)
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id, ProjectFile.path == path)
    )
    return result.scalar_one_or_none()


async def upsert_file(
    db: AsyncSession,
    project_id: int,
    path: str,
    content: str,
    is_directory: bool = False,
    sync_disk: bool = True,
) -> ProjectFile:
    path = normalize_path(path)
    existing = await get_file(db, project_id, path)
    if existing:
        existing.content = "" if is_directory else content
        existing.is_directory = is_directory
        file = existing
    else:
        file = ProjectFile(
            project_id=project_id,
            path=path,
            content="" if is_directory else content,
            is_directory=is_directory,
        )
        db.add(file)

    if sync_disk and not is_directory:
        disk_path = disk_root_for(project_id) / path
        disk_path.parent.mkdir(parents=True, exist_ok=True)
        disk_path.write_text(content, encoding="utf-8")
    elif sync_disk and is_directory:
        (disk_root_for(project_id) / path).mkdir(parents=True, exist_ok=True)

    await db.commit()
    await db.refresh(file)
    return file


async def delete_file(db: AsyncSession, project_id: int, path: str) -> bool:
    path = normalize_path(path)
    file = await get_file(db, project_id, path)
    if not file:
        return False
    await db.delete(file)
    # Also delete nested paths
    result = await db.execute(select(ProjectFile).where(ProjectFile.project_id == project_id))
    for child in result.scalars().all():
        if child.path.startswith(path + "/"):
            await db.delete(child)
    await db.commit()

    disk_path = disk_root_for(project_id) / path
    if disk_path.is_file():
        disk_path.unlink(missing_ok=True)
    elif disk_path.is_dir():
        import shutil

        shutil.rmtree(disk_path, ignore_errors=True)
    return True


async def export_tree(db: AsyncSession, project_id: int) -> dict[str, str]:
    files = await list_files(db, project_id)
    return {f.path: f.content for f in files if not f.is_directory}


async def sync_project_to_disk(db: AsyncSession, project_id: int) -> Path:
    root = disk_root_for(project_id)
    files = await list_files(db, project_id)
    for file in files:
        target = root / file.path
        if file.is_directory:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(file.content, encoding="utf-8")
    return root
