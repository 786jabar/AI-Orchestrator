from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite+aiosqlite:///{ROOT / 'data' / 'orchestrator.db'}"
    sandbox_url: str = "http://127.0.0.1:8001"
    encryption_secret: str = "dev-secret-change-me-please-32chars"
    projects_root: str = str(ROOT / "data" / "projects")
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
