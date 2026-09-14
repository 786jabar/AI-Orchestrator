from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import AiProvider, TaskCategory, TaskStatus


class UserCreate(BaseModel):
    email: str
    display_name: str = "Developer"


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str

    model_config = {"from_attributes": True}


class ApiKeyUpsert(BaseModel):
    provider: AiProvider
    api_key: str
    label: str = ""


class ApiKeyOut(BaseModel):
    id: int
    provider: AiProvider
    label: str
    masked_key: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    runtime: str = "nodejs"
    owner_email: str = "demo@orchestrator.local"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    entrypoint: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    runtime: str
    entrypoint: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileNode(BaseModel):
    path: str
    is_directory: bool
    updated_at: Optional[datetime] = None


class FileContent(BaseModel):
    path: str
    content: str
    is_directory: bool = False
    updated_at: Optional[datetime] = None


class FileUpsert(BaseModel):
    path: str
    content: str = ""
    is_directory: bool = False


class TaskCreate(BaseModel):
    prompt: str = Field(min_length=1)
    title: Optional[str] = None
    category: Optional[TaskCategory] = None
    provider_override: Optional[AiProvider] = None
    target_path: Optional[str] = None
    auto_run: bool = True
    require_approval: bool = False
    use_tools: bool = True
    auto_improve: bool = False


class TaskOut(BaseModel):
    id: int
    project_id: int
    parent_id: Optional[int]
    title: str
    prompt: str
    category: TaskCategory
    status: TaskStatus
    assigned_provider: AiProvider
    manual_override: bool
    result: str
    error: str
    target_path: Optional[str]
    quality_score: float = 0.0
    tool_trace: str = ""
    diff_summary: str = ""
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PipelineOut(BaseModel):
    project_id: int
    tasks: list[TaskOut]


class GenerateCodeRequest(BaseModel):
    prompt: str
    target_path: Optional[str] = None
    provider_override: Optional[AiProvider] = None
    category: TaskCategory = TaskCategory.code_generation


class RunProjectRequest(BaseModel):
    command: Optional[str] = None
    entrypoint: Optional[str] = None


class RunResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    command: str
    duration_ms: int


class SnapshotCreate(BaseModel):
    label: str = "manual snapshot"


class SnapshotOut(BaseModel):
    id: int
    project_id: int
    label: str
    source: str
    file_count: int
    created_at: datetime
    restored_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MemoryMessageOut(BaseModel):
    id: int
    project_id: int
    role: str
    content: str
    provider: Optional[str] = None
    task_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PendingChangeOut(BaseModel):
    id: int
    project_id: int
    task_id: Optional[int]
    path: str
    action: str
    before_content: str
    after_content: str
    diff_text: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdvancedTaskCreate(TaskCreate):
    mode: str = "single"  # single | pipeline
