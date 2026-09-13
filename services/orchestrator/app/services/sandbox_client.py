from __future__ import annotations

import httpx

from ..config import get_settings


async def run_in_sandbox(
    *,
    project_id: int,
    files: dict[str, str],
    command: str,
    timeout_seconds: int = 30,
) -> dict:
    settings = get_settings()
    payload = {
        "project_id": project_id,
        "files": files,
        "command": command,
        "timeout_seconds": timeout_seconds,
    }
    async with httpx.AsyncClient(timeout=timeout_seconds + 15) as client:
        resp = await client.post(f"{settings.sandbox_url.rstrip('/')}/execute", json=payload)
        resp.raise_for_status()
        return resp.json()


async def sandbox_health() -> dict:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.sandbox_url.rstrip('/')}/health")
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "error": str(exc)}
