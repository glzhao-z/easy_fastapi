"""Environment-backed application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Validated settings loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EASY_FASTAPI_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "easy_fastapi"
    app_version: str = "0.1.0"
    environment: Environment = "development"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: LogLevel = "INFO"
    docs_enabled: bool = True
    api_v1_prefix: str = Field(default="/api/v1", pattern=r"^/[a-zA-Z0-9/_-]+$")
    request_id_header: str = "X-Request-ID"


@lru_cache
def get_settings() -> Settings:
    """Reuse immutable process configuration while allowing explicit settings in tests."""
    return Settings()
