from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routers import files, keys, projects, tasks
from .services.sandbox_client import sandbox_health


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    Path(settings.projects_root).mkdir(parents=True, exist_ok=True)
    if ":///" in settings.database_url:
        Path(settings.database_url.split(":///", 1)[1]).parent.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="ForgeLink AI Orchestrator", version="0.2.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(files.router)
app.include_router(tasks.router)
app.include_router(keys.router)


@app.get("/health")
async def health():
    sandbox = await sandbox_health()
    return {"status": "ok", "service": "orchestrator", "sandbox": sandbox}
