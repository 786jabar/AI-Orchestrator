from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from ..db import get_db
from ..models import PendingChange, Project, Task
from ..schemas import (
    GenerateCodeRequest,
    MemoryMessageOut,
    PendingChangeOut,
    PipelineOut,
    RunProjectRequest,
    RunResult,
    SnapshotCreate,
    SnapshotOut,
    TaskCreate,
    TaskOut,
)
from ..services import memory, snapshots, vfs
from ..services.events import event_bus
from ..services.orchestrator import (
    apply_pending_change,
    create_and_run_task,
    decompose_and_run,
    execute_task,
    reject_pending_change,
)
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
        require_approval=body.require_approval,
        use_tools=body.use_tools,
        auto_improve=body.auto_improve,
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
        use_tools=True,
    )


@router.post("/orchestrate", response_model=list[TaskOut])
async def orchestrate(project_id: int, body: TaskCreate, db: AsyncSession = Depends(get_db)):
    project = await _project(db, project_id)
    return await decompose_and_run(
        db,
        project,
        body.prompt,
        require_approval=body.require_approval,
        auto_improve=body.auto_improve if body.auto_improve is not None else True,
    )


@router.post("/tasks/{task_id}/run", response_model=TaskOut)
async def rerun_task(project_id: int, task_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    task = await db.get(Task, task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(404, "Task not found")
    return await execute_task(db, task, use_tools=True, auto_improve=False)


@router.post("/run", response_model=RunResult)
async def run_project(
    project_id: int, body: RunProjectRequest, db: AsyncSession = Depends(get_db)
):
    project = await _project(db, project_id)
    files = await vfs.export_tree(db, project_id)
    await vfs.sync_project_to_disk(db, project_id)
    entrypoint = body.entrypoint or project.entrypoint
    command = body.command or f"FORGELINK_ONCE=1 node {entrypoint}"
    try:
        result = await run_in_sandbox(
            project_id=project_id, files=files, command=command, timeout_seconds=20
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Sandbox error: {exc}") from exc
    return RunResult(**result)


@router.get("/events")
async def stream_events(project_id: int):
    import json

    async def gen():
        async for event in event_bus.subscribe(project_id):
            yield {"event": event.type, "data": json.dumps(event.to_dict())}

    return EventSourceResponse(gen())


@router.get("/memory", response_model=list[MemoryMessageOut])
async def get_memory(project_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    return await memory.recent_memory(db, project_id, limit=40)


@router.get("/snapshots", response_model=list[SnapshotOut])
async def get_snapshots(project_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    return await snapshots.list_snapshots(db, project_id)


@router.post("/snapshots", response_model=SnapshotOut)
async def post_snapshot(
    project_id: int, body: SnapshotCreate, db: AsyncSession = Depends(get_db)
):
    await _project(db, project_id)
    return await snapshots.create_snapshot(db, project_id, label=body.label, source="manual")


@router.post("/snapshots/{snapshot_id}/restore", response_model=SnapshotOut)
async def restore_snapshot_route(
    project_id: int, snapshot_id: int, db: AsyncSession = Depends(get_db)
):
    await _project(db, project_id)
    try:
        return await snapshots.restore_snapshot(db, project_id, snapshot_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/changes", response_model=list[PendingChangeOut])
async def list_changes(project_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    result = await db.execute(
        select(PendingChange)
        .where(PendingChange.project_id == project_id, PendingChange.status == "pending")
        .order_by(PendingChange.id.desc())
    )
    return list(result.scalars().all())


@router.post("/changes/{change_id}/apply", response_model=PendingChangeOut)
async def apply_change(project_id: int, change_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    try:
        change = await apply_pending_change(db, change_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if change.project_id != project_id:
        raise HTTPException(404, "Change not found")
    return change


@router.post("/changes/{change_id}/reject", response_model=PendingChangeOut)
async def reject_change(project_id: int, change_id: int, db: AsyncSession = Depends(get_db)):
    await _project(db, project_id)
    try:
        change = await reject_pending_change(db, change_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if change.project_id != project_id:
        raise HTTPException(404, "Change not found")
    return change
