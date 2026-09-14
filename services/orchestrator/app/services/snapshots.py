from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ProjectSnapshot
from . import vfs


async def create_snapshot(
    db: AsyncSession,
    project_id: int,
    *,
    label: str,
    source: str = "manual",
) -> ProjectSnapshot:
    tree = await vfs.export_tree(db, project_id)
    snap = ProjectSnapshot(
        project_id=project_id,
        label=label[:200],
        source=source,
        file_count=len(tree),
        payload_json=json.dumps(tree),
    )
    db.add(snap)
    await db.commit()
    await db.refresh(snap)
    return snap


async def list_snapshots(db: AsyncSession, project_id: int) -> list[ProjectSnapshot]:
    result = await db.execute(
        select(ProjectSnapshot)
        .where(ProjectSnapshot.project_id == project_id)
        .order_by(ProjectSnapshot.id.desc())
        .limit(50)
    )
    return list(result.scalars().all())


async def restore_snapshot(db: AsyncSession, project_id: int, snapshot_id: int) -> ProjectSnapshot:
    snap = await db.get(ProjectSnapshot, snapshot_id)
    if not snap or snap.project_id != project_id:
        raise ValueError("Snapshot not found")

    # Safety snapshot of current state
    await create_snapshot(db, project_id, label=f"auto-before-restore-{snapshot_id}", source="system")

    current = await vfs.list_files(db, project_id)
    for f in current:
        if not f.is_directory:
            await vfs.delete_file(db, project_id, f.path)

    tree = json.loads(snap.payload_json)
    for path, content in tree.items():
        await vfs.upsert_file(db, project_id, path, content)

    snap.restored_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(snap)
    return snap
