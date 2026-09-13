from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import AiProvider, Project, Task, TaskCategory, TaskStatus, User, UserApiKey
from . import vfs
from .crypto import decrypt_secret
from .providers import (
    ClaudeProvider,
    GeminiProvider,
    MockProvider,
    OpenAIProvider,
    parse_file_blocks,
)
from .providers.base import AiProviderClient, AiResponse
from .routing import classify_task, route_provider


def _build_context(files: dict[str, str], prior_results: list[str]) -> str:
    parts: list[str] = []
    for path, content in sorted(files.items()):
        snippet = content if len(content) < 4000 else content[:4000] + "\n…(truncated)"
        parts.append(f"### {path}\n```\n{snippet}\n```")
    if prior_results:
        parts.append("## Prior AI outputs")
        for idx, result in enumerate(prior_results[-3:], start=1):
            parts.append(f"### Output {idx}\n{result[:2000]}")
    return "\n\n".join(parts)


async def resolve_provider_client(
    db: AsyncSession,
    user_id: int,
    provider: AiProvider,
) -> AiProviderClient:
    settings = get_settings()
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == user_id, UserApiKey.provider == provider)
    )
    row = result.scalar_one_or_none()
    user_key = decrypt_secret(row.encrypted_key) if row else ""

    if provider == AiProvider.claude:
        key = user_key or settings.anthropic_api_key
        return ClaudeProvider(key) if key else MockProvider()
    if provider == AiProvider.gpt:
        key = user_key or settings.openai_api_key
        return OpenAIProvider(key) if key else MockProvider()
    if provider == AiProvider.gemini:
        key = user_key or settings.google_api_key
        return GeminiProvider(key) if key else MockProvider()
    return MockProvider()


async def get_or_create_user(db: AsyncSession, email: str, display_name: str = "Developer") -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(email=email, display_name=display_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_and_run_task(
    db: AsyncSession,
    project: Project,
    prompt: str,
    *,
    title: str | None = None,
    category: TaskCategory | None = None,
    provider_override: AiProvider | None = None,
    target_path: str | None = None,
    parent_id: int | None = None,
    auto_run: bool = True,
) -> Task:
    resolved_category = category or classify_task(prompt)
    provider, manual = route_provider(resolved_category, provider_override)

    task = Task(
        project_id=project.id,
        parent_id=parent_id,
        title=title or prompt[:80],
        prompt=prompt,
        category=resolved_category,
        status=TaskStatus.queued,
        assigned_provider=provider,
        manual_override=manual,
        target_path=target_path,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    if auto_run:
        await execute_task(db, task)
    return task


async def execute_task(db: AsyncSession, task: Task) -> Task:
    result = await db.execute(select(Project).where(Project.id == task.project_id))
    project = result.scalar_one()

    task.status = TaskStatus.running
    task.started_at = datetime.now(timezone.utc)
    await db.commit()

    try:
        files = await vfs.export_tree(db, project.id)
        prior = await db.execute(
            select(Task)
            .where(Task.project_id == project.id, Task.status == TaskStatus.completed)
            .order_by(Task.id.desc())
            .limit(3)
        )
        prior_results = [t.result for t in prior.scalars().all() if t.result]
        context = _build_context(files, prior_results)
        if task.target_path:
            context = f"Preferred target file: {task.target_path}\n\n" + context

        preferred = task.assigned_provider
        client = await resolve_provider_client(db, project.owner_id, preferred)
        response: AiResponse = await client.send_prompt(task.prompt, context)

        if isinstance(client, MockProvider):
            note = ""
            if preferred != AiProvider.mock:
                note = f"[Note: No API key for `{preferred.value}`; used mock provider.]\n\n"
                task.assigned_provider = AiProvider.mock
            task.result = note + response.content
        else:
            task.result = response.content

        written = parse_file_blocks(response.content)
        if not written and task.target_path:
            written = {task.target_path: response.content}

        for path, content in written.items():
            await vfs.upsert_file(db, project.id, path, content)

        task.status = TaskStatus.completed
        task.completed_at = datetime.now(timezone.utc)
        task.error = ""
    except Exception as exc:  # noqa: BLE001
        task.status = TaskStatus.failed
        task.error = str(exc)
        task.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)
    return task


async def decompose_and_run(db: AsyncSession, project: Project, prompt: str) -> list[Task]:
    """Split a high-level goal into category-scoped sub-tasks and run them sequentially."""
    parent = await create_and_run_task(
        db,
        project,
        prompt=f"Create a concise implementation plan (bullets only) for: {prompt}",
        title="Plan",
        category=TaskCategory.architecture,
        auto_run=True,
    )

    children_specs = [
        (TaskCategory.code_generation, f"Implement the core Node.js logic for: {prompt}", "index.js"),
        (TaskCategory.ui_generation, f"Improve the HTML/CSS UI for: {prompt}", "index.js"),
        (TaskCategory.testing, f"Add a simple Node.js test script validating: {prompt}", "test.js"),
    ]

    tasks = [parent]
    for category, child_prompt, target in children_specs:
        child = await create_and_run_task(
            db,
            project,
            prompt=child_prompt,
            title=category.value.replace("_", " ").title(),
            category=category,
            target_path=target,
            parent_id=parent.id,
            auto_run=True,
        )
        tasks.append(child)
    return tasks
