from __future__ import annotations

import asyncio
import shutil
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

    sandbox_root: str = str(ROOT / "data" / "sandboxes")
    sandbox_timeout_seconds: int = 30
    e2b_api_key: str = ""
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000"


settings = Settings()
app = FastAPI(title="AI Orchestrator Sandbox", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecuteRequest(BaseModel):
    project_id: int
    files: dict[str, str] = Field(default_factory=dict)
    command: str = "node index.js"
    timeout_seconds: int | None = None


class ExecuteResponse(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    command: str
    duration_ms: int
    backend: str


def _materialize(project_id: int, files: dict[str, str]) -> Path:
    root = Path(settings.sandbox_root) / str(project_id)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        cleaned = path.replace("\\", "/").lstrip("/")
        if ".." in cleaned.split("/"):
            raise HTTPException(400, f"Invalid path: {path}")
        target = root / cleaned
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


async def _run_local(cwd: Path, command: str, timeout: int) -> ExecuteResponse:
    started = time.perf_counter()
    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={
            "PATH": str(Path("/home/ubuntu/.nvm/versions/node/v22.22.2/bin"))
            + ":/usr/local/bin:/usr/bin:/bin",
            "HOME": str(cwd),
            "NODE_ENV": "development",
            "PORT": "3456",
        },
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        code = proc.returncode or 0
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return ExecuteResponse(
            exit_code=124,
            stdout="",
            stderr=f"Timed out after {timeout}s",
            command=command,
            duration_ms=int((time.perf_counter() - started) * 1000),
            backend="local-subprocess",
        )
    return ExecuteResponse(
        exit_code=code,
        stdout=stdout_b.decode("utf-8", errors="replace")[-20_000:],
        stderr=stderr_b.decode("utf-8", errors="replace")[-20_000:],
        command=command,
        duration_ms=int((time.perf_counter() - started) * 1000),
        backend="local-subprocess",
    )


async def _run_e2b(files: dict[str, str], command: str, timeout: int) -> ExecuteResponse | None:
    """Optional E2B backend when E2B_API_KEY is configured."""
    if not settings.e2b_api_key:
        return None
    try:
        from e2b_code_interpreter import Sandbox  # type: ignore
    except Exception:
        return None

    started = time.perf_counter()
    sbx = Sandbox(api_key=settings.e2b_api_key)
    try:
        for path, content in files.items():
            sbx.files.write(path, content)
        result = sbx.commands.run(command, timeout=timeout)
        return ExecuteResponse(
            exit_code=result.exit_code,
            stdout=result.stdout[-20_000:],
            stderr=result.stderr[-20_000:],
            command=command,
            duration_ms=int((time.perf_counter() - started) * 1000),
            backend="e2b",
        )
    finally:
        sbx.kill()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "sandbox",
        "backend": "e2b" if settings.e2b_api_key else "local-subprocess",
    }


@app.post("/execute", response_model=ExecuteResponse)
async def execute(body: ExecuteRequest):
    timeout = body.timeout_seconds or settings.sandbox_timeout_seconds
    e2b = await _run_e2b(body.files, body.command, timeout)
    if e2b is not None:
        return e2b
    cwd = _materialize(body.project_id, body.files)
    return await _run_local(cwd, body.command, timeout)
