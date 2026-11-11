"""基于环境变量的应用配置。"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """从环境变量及可选的 .env 文件加载并校验配置。"""

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
    database_enabled: bool = False
    database_url: SecretStr | None = None
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    redis_enabled: bool = False
    redis_url: SecretStr | None = None
    redis_key_prefix: str = "easy_fastapi:"
    dependency_timeout: float = Field(default=5.0, gt=0, le=60)

    @model_validator(mode="after")
    def validate_services(self) -> "Settings":
        """启用组件时必须提供连接地址。"""
        if self.database_enabled:
            if not self.database_url:
                raise ValueError("启用数据库时必须配置 DATABASE_URL")
            if not self.database_url.get_secret_value().startswith(
                ("postgresql+asyncpg://", "mysql+asyncmy://")
            ):
                raise ValueError("数据库地址必须使用 postgresql+asyncpg 或 mysql+asyncmy")
        if self.redis_enabled:
            if not self.redis_url:
                raise ValueError("启用 Redis 时必须配置 REDIS_URL")
            if not self.redis_url.get_secret_value().startswith(("redis://", "rediss://")):
                raise ValueError("Redis 地址必须使用 redis 或 rediss")
        return self


@lru_cache
def get_settings() -> Settings:
    """复用进程级配置，同时允许测试显式传入独立配置。"""
    return Settings()
