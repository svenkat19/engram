from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_db_path() -> Path:
    return Path.home() / ".engram" / "engram.db"


class EngramSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ENGRAM_", env_file=".env")

    db_path: Path = Field(default_factory=_default_db_path)

    host: str = "127.0.0.1"
    port: int = 8741

    embedding_provider: str = "local"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    openai_api_key: str | None = None

    dedup_threshold: float = 0.92
    compaction_interval_hours: int = 6

    encryption_enabled: bool = False
    encryption_key: str | None = None

    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> EngramSettings:
    return EngramSettings()


def ensure_data_dir() -> Path:
    data_dir = get_settings().db_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
