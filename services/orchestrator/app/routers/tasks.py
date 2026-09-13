from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Project, Task
from ..schemas import (
    GenerateCodeRequest,
    PipelineOut,
    RunProjectRequest,
    RunResult,
    TaskCreate,
    TaskOut,
)
from ..services import vfs
from ..services.orchestrator import create_and_run_task, decompose_and_run, execute_task
from ..services.sandbox_client import run_in_sandbox

router = APIRouter(prefix="/api/projects/{project_id}", tags=["tasks"])


async def _project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(project_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.id.asc())
    )
    return list(result.scalars().all())


@router.get("/pipeline", response_model=PipelineOut)
async def pipeline(project_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.id.asc())
    )
    tasks = list(result.scalars().all())
    return PipelineOut(project_id=project_id, tasks=tasks)


@router.post("/tasks", response_model=TaskOut)
async def create_task(project_id: int, body: TaskCreate, db: AsyncSession = Depends(get_db)):
    project = await _project(db, project_id)
    task = await create_and_run_task(
        db,
        project,
        prompt=body.prompt,
        title=body.title,
        category=body.category,
        provider_override=body.provider_override,
        target_path=body.target_path,
        auto_run=body.auto_run,
    )
    return task


@router.post("/generate", response_model=TaskOut)
async def generate_code(
    project_id: int, body: GenerateCodeRequest, db: AsyncSession = Depends(get_db)
):
    project = await _project(db, project_id)
    return await create_and_run_task(
        db,
        project,
        prompt=body.prompt,
        title="Generate code",
        category=body.category,
        provider_override=body.provider_override,
        target_path=body.target_path,
        auto_run=True,
    )


@router.post("/orchestrate", response_model=list[TaskOut])
async def orchestrate(project_id: int, body: TaskCreate, db: AsyncSession = Depends(get_db)):
    project = await _project(db, project_id)
    return await decompose_and_run(db, project, body.prompt)


@router.post("/tasks/{task_id}/run", response_model=TaskOut)
async def rerun_task(project_id: int, task_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    task = await db.get(Task, task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(404, "Task not found")
    return await execute_task(db, task)


@router.post("/run", response_model=RunResult)
async def run_project(
    project_id: int, body: RunProjectRequest, db: AsyncSession = Depends(get_db)
):
    project = await _project(db, project_id)
    files = await vfs.export_tree(db, project_id)
    await vfs.sync_project_to_disk(db, project_id)
    entrypoint = body.entrypoint or project.entrypoint
    # Default preview run exits after printing HTML (FORGELINK_ONCE) so servers don't hang.
    command = body.command or f"FORGELINK_ONCE=1 node {entrypoint}"
    try:
        result = await run_in_sandbox(
            project_id=project_id, files=files, command=command, timeout_seconds=20
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Sandbox error: {exc}") from exc
    return RunResult(**result)
