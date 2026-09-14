from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import (
    AiProvider,
    PendingChange,
    Project,
    Task,
    TaskCategory,
    TaskStatus,
    User,
    UserApiKey,
)
from . import memory, snapshots, vfs
from .agent_tools import TOOL_SPEC, execute_tool_requests, strip_tool_markup
from .context import build_smart_context, summarize_change_set, unified_diff
from .crypto import decrypt_secret
from .events import PlatformEvent, event_bus
from .providers import (
    ClaudeProvider,
    GeminiProvider,
    MockProvider,
    OpenAIProvider,
    parse_file_blocks,
)
from .providers.base import AiProviderClient, AiResponse
from .routing import classify_task, route_provider
from .sandbox_client import run_in_sandbox


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


def _score_output(content: str, written: dict[str, str], tool_ok: bool) -> float:
    score = 0.4
    if written:
        score += 0.3
    if "```" in content:
        score += 0.1
    if len(content) > 120:
        score += 0.1
    if tool_ok:
        score += 0.1
    return round(min(score, 1.0), 2)


async def _emit(project_id: int, type_: str, payload: dict) -> None:
    await event_bus.publish(PlatformEvent(type=type_, project_id=project_id, payload=payload))


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
    require_approval: bool = False,
    use_tools: bool = True,
    auto_improve: bool = False,
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
    await _emit(
        project.id,
        "task_queued",
        {
            "task_id": task.id,
            "title": task.title,
            "category": task.category.value,
            "provider": task.assigned_provider.value,
        },
    )

    if auto_run:
        await execute_task(
            db,
            task,
            require_approval=require_approval,
            use_tools=use_tools,
            auto_improve=auto_improve,
        )
    return task


async def execute_task(
    db: AsyncSession,
    task: Task,
    *,
    require_approval: bool = False,
    use_tools: bool = True,
    auto_improve: bool = False,
) -> Task:
    result = await db.execute(select(Project).where(Project.id == task.project_id))
    project = result.scalar_one()

    task.status = TaskStatus.running
    task.started_at = datetime.now(timezone.utc)
    await db.commit()
    await _emit(project.id, "task_running", {"task_id": task.id, "title": task.title})

    try:
        await snapshots.create_snapshot(
            db,
            project.id,
            label=f"before-task-{task.id}",
            source="pre_task",
        )

        before = await vfs.export_tree(db, project.id)
        mem = await memory.memory_strings(db, project.id)
        prior = await db.execute(
            select(Task)
            .where(Task.project_id == project.id, Task.status == TaskStatus.completed)
            .order_by(Task.id.desc())
            .limit(3)
        )
        prior_results = [t.result for t in prior.scalars().all() if t.result]
        context = build_smart_context(task.prompt, before, mem, prior_results)
        if task.target_path:
            context = f"Preferred target file: {task.target_path}\n\n" + context
        if use_tools:
            context = context + "\n\n" + TOOL_SPEC

        preferred = task.assigned_provider
        client = await resolve_provider_client(db, project.owner_id, preferred)

        await memory.add_message(db, project.id, "user", task.prompt, task_id=task.id)

        # Multi-round tool loop (max 3)
        transcript = ""
        tool_trace_parts: list[str] = []
        prompt_round = task.prompt
        final_text = ""
        for round_idx in range(3 if use_tools else 1):
            await _emit(
                project.id,
                "agent_round",
                {"task_id": task.id, "round": round_idx + 1, "provider": preferred.value},
            )
            response: AiResponse = await client.send_prompt(prompt_round, context + transcript)
            final_text = response.content
            if isinstance(client, MockProvider) and preferred != AiProvider.mock:
                task.assigned_provider = AiProvider.mock

            tool_results, report = await execute_tool_requests(db, project.id, final_text)
            if not tool_results:
                break
            tool_trace_parts.append(report)
            transcript += f"\n\n## Tool results (round {round_idx + 1})\n{report}\n"
            prompt_round = (
                f"{task.prompt}\n\nContinue after tool results. Prefer completing the task now.\n"
                f"Tool results:\n{report}"
            )

        cleaned = strip_tool_markup(final_text)
        written = parse_file_blocks(cleaned)
        if not written and task.target_path and "```" not in cleaned:
            # only if it looks like code
            if "function" in cleaned or "const " in cleaned or "require(" in cleaned:
                written = {task.target_path: cleaned}

        # Pending diffs vs auto-apply
        changes = []
        for path, content in written.items():
            before_content = before.get(path, "")
            changes.append(
                {
                    "path": path,
                    "action": "create" if path not in before else "update",
                    "before": before_content,
                    "after": content,
                }
            )

        if require_approval and changes:
            for ch in changes:
                pending = PendingChange(
                    project_id=project.id,
                    task_id=task.id,
                    path=ch["path"],
                    action=ch["action"],
                    before_content=ch["before"],
                    after_content=ch["after"],
                    diff_text=unified_diff(ch["path"], ch["before"], ch["after"]),
                    status="pending",
                )
                db.add(pending)
            await db.commit()
            await _emit(
                project.id,
                "diffs_pending",
                {"task_id": task.id, "count": len(changes), "paths": [c["path"] for c in changes]},
            )
        else:
            for ch in changes:
                await vfs.upsert_file(db, project.id, ch["path"], ch["after"])

        after = await vfs.export_tree(db, project.id)
        diff_summary = json.dumps(summarize_change_set(before, after))

        note = ""
        if isinstance(client, MockProvider) and preferred != AiProvider.mock:
            note = f"[Note: No API key for `{preferred.value}`; used mock provider.]\n\n"

        task.result = note + cleaned
        task.tool_trace = "\n\n".join(tool_trace_parts)
        task.diff_summary = diff_summary
        task.quality_score = _score_output(cleaned, written, bool(tool_trace_parts))
        task.status = TaskStatus.completed
        task.completed_at = datetime.now(timezone.utc)
        task.error = ""
        await db.commit()

        await memory.add_message(
            db,
            project.id,
            "assistant",
            cleaned[:4000],
            provider=task.assigned_provider.value,
            task_id=task.id,
        )

        # Critic pass
        critic_score = await _run_critic(db, project, task, after)
        task.quality_score = max(task.quality_score, critic_score)
        await db.commit()

        if auto_improve and critic_score < 0.75:
            await _emit(project.id, "auto_improve", {"task_id": task.id, "score": critic_score})
            fix = await create_and_run_task(
                db,
                project,
                prompt=(
                    f"Improve the implementation based on critic feedback. Original goal: {task.prompt}"
                ),
                title="Auto-improve",
                category=TaskCategory.debugging,
                target_path=task.target_path,
                parent_id=task.id,
                auto_run=True,
                require_approval=require_approval,
                use_tools=True,
                auto_improve=False,
            )
            await db.refresh(fix)

        await _emit(
            project.id,
            "task_completed",
            {
                "task_id": task.id,
                "provider": task.assigned_provider.value,
                "quality_score": task.quality_score,
                "files_changed": [c["path"] for c in changes],
            },
        )
    except Exception as exc:  # noqa: BLE001
        task.status = TaskStatus.failed
        task.error = str(exc)
        task.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await _emit(project.id, "task_failed", {"task_id": task.id, "error": str(exc)})

    await db.refresh(task)
    return task


async def _run_critic(
    db: AsyncSession, project: Project, task: Task, files: dict[str, str]
) -> float:
    """Secondary reviewer agent scores the result and may leave memory notes."""
    await _emit(project.id, "critic_started", {"task_id": task.id})
    client = await resolve_provider_client(db, project.owner_id, AiProvider.claude)
    # Prefer a different model when possible
    if isinstance(client, MockProvider):
        client = MockProvider()

    context = build_smart_context(
        f"Review code for: {task.prompt}",
        files,
        [],
        [task.result[:1500]],
    )
    review_prompt = (
        "You are a strict code reviewer. Score the solution from 0.0 to 1.0.\n"
        "Reply with first line: SCORE: 0.xx\nThen 3 short bullets of feedback.\n"
        f"Task: {task.prompt}"
    )
    try:
        resp = await client.send_prompt(review_prompt, context)
        text = resp.content
    except Exception as exc:  # noqa: BLE001
        text = f"SCORE: 0.55\n- critic unavailable: {exc}"

    match = re.search(r"SCORE:\s*([01](?:\.\d+)?)", text)
    score = float(match.group(1)) if match else 0.6
    await memory.add_message(
        db,
        project.id,
        "critic",
        text[:2000],
        provider=getattr(client, "name", "critic"),
        task_id=task.id,
    )
    await _emit(project.id, "critic_finished", {"task_id": task.id, "score": score})
    return score


async def decompose_and_run(
    db: AsyncSession,
    project: Project,
    prompt: str,
    *,
    require_approval: bool = False,
    auto_improve: bool = True,
) -> list[Task]:
    """Advanced pipeline: plan → parallel code/UI → tests → critic-aware improve."""
    parent = await create_and_run_task(
        db,
        project,
        prompt=f"Create a concise implementation plan (bullets only) for: {prompt}",
        title="Plan",
        category=TaskCategory.architecture,
        auto_run=True,
        require_approval=False,
        use_tools=False,
        auto_improve=False,
    )

    # Parallelizable stage: code + UI conceptually; run sequentially in one process
    # but emit parallel intent, then run code then UI quickly.
    code_task = await create_and_run_task(
        db,
        project,
        prompt=f"Implement the core Node.js logic for: {prompt}",
        title="Code Generation",
        category=TaskCategory.code_generation,
        target_path="index.js",
        parent_id=parent.id,
        auto_run=True,
        require_approval=require_approval,
        use_tools=True,
        auto_improve=False,
    )
    ui_task = await create_and_run_task(
        db,
        project,
        prompt=f"Improve the HTML/CSS UI for: {prompt}",
        title="UI Generation",
        category=TaskCategory.ui_generation,
        target_path="index.js",
        parent_id=parent.id,
        auto_run=True,
        require_approval=require_approval,
        use_tools=True,
        auto_improve=False,
    )
    test_task = await create_and_run_task(
        db,
        project,
        prompt=f"Add a simple Node.js test script validating: {prompt}",
        title="Testing",
        category=TaskCategory.testing,
        target_path="test.js",
        parent_id=parent.id,
        auto_run=True,
        require_approval=require_approval,
        use_tools=True,
        auto_improve=auto_improve,
    )

    # Optional sandbox verification stage
    verify = await create_and_run_task(
        db,
        project,
        prompt=(
            "Verify the project runs. Use tools if needed. "
            f"Goal under test: {prompt}"
        ),
        title="Verify",
        category=TaskCategory.testing,
        parent_id=parent.id,
        auto_run=True,
        use_tools=True,
        auto_improve=False,
    )

    # Kick a real sandbox run for telemetry
    try:
        files = await vfs.export_tree(db, project.id)
        result = await run_in_sandbox(
            project_id=project.id,
            files=files,
            command="FORGELINK_ONCE=1 node index.js",
            timeout_seconds=20,
        )
        await _emit(
            project.id,
            "sandbox_verified",
            {
                "exit_code": result.get("exit_code"),
                "duration_ms": result.get("duration_ms"),
            },
        )
    except Exception as exc:  # noqa: BLE001
        await _emit(project.id, "sandbox_verified", {"error": str(exc)})

    return [parent, code_task, ui_task, test_task, verify]


async def apply_pending_change(db: AsyncSession, change_id: int) -> PendingChange:
    change = await db.get(PendingChange, change_id)
    if not change or change.status != "pending":
        raise ValueError("Pending change not found")
    await vfs.upsert_file(db, change.project_id, change.path, change.after_content)
    change.status = "applied"
    await db.commit()
    await db.refresh(change)
    await _emit(
        change.project_id,
        "diff_applied",
        {"change_id": change.id, "path": change.path},
    )
    return change


async def reject_pending_change(db: AsyncSession, change_id: int) -> PendingChange:
    change = await db.get(PendingChange, change_id)
    if not change or change.status != "pending":
        raise ValueError("Pending change not found")
    change.status = "rejected"
    await db.commit()
    await db.refresh(change)
    await _emit(
        change.project_id,
        "diff_rejected",
        {"change_id": change.id, "path": change.path},
    )
    return change
