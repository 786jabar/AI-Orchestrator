from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ConversationMessage


async def add_message(
    db: AsyncSession,
    project_id: int,
    role: str,
    content: str,
    *,
    provider: str | None = None,
    task_id: int | None = None,
) -> ConversationMessage:
    msg = ConversationMessage(
        project_id=project_id,
        role=role,
        content=content,
        provider=provider,
        task_id=task_id,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def recent_memory(db: AsyncSession, project_id: int, limit: int = 12) -> list[ConversationMessage]:
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.project_id == project_id)
        .order_by(ConversationMessage.id.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


async def memory_strings(db: AsyncSession, project_id: int, limit: int = 12) -> list[str]:
    rows = await recent_memory(db, project_id, limit=limit)
    return [f"[{m.role}] {m.content}" for m in rows]
