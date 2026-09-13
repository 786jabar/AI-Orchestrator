from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Project
from ..schemas import FileContent, FileNode, FileUpsert
from ..services import vfs

router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])


async def _project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("", response_model=list[FileNode])
async def list_files(project_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    files = await vfs.list_files(db, project_id)
    return [
        FileNode(path=f.path, is_directory=f.is_directory, updated_at=f.updated_at) for f in files
    ]


@router.get("/content", response_model=FileContent)
async def read_file(
    project_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    await _project(db, project_id)
    try:
        file = await vfs.get_file(db, project_id, path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not file:
        raise HTTPException(404, "File not found")
    return FileContent(
        path=file.path,
        content=file.content,
        is_directory=file.is_directory,
        updated_at=file.updated_at,
    )


@router.put("", response_model=FileContent)
async def upsert_file(project_id: int, body: FileUpsert, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    try:
        file = await vfs.upsert_file(
            db, project_id, body.path, body.content, is_directory=body.is_directory
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return FileContent(
        path=file.path,
        content=file.content,
        is_directory=file.is_directory,
        updated_at=file.updated_at,
    )


@router.delete("")
async def delete_file(
    project_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    await _project(db, project_id)
    try:
        ok = await vfs.delete_file(db, project_id, path)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not ok:
        raise HTTPException(404, "File not found")
    return {"ok": True}
