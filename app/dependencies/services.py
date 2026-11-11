"""请求级数据库会话与缓存依赖。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from fastapi import Request

from app.core.exceptions import AppException

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.infrastructure.cache import Cache
    from app.infrastructure.database import Database


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    database: Database | None = getattr(request.app.state, "database", None)
    if database is None:
        raise AppException(status_code=503, code="database_disabled", message="数据库未启用")
    # 业务显式 commit，退出时未提交的事务自动回滚。
    async with database.sessions() as session:
        yield session


async def get_cache(request: Request) -> Cache:
    cache: Cache | None = getattr(request.app.state, "cache", None)
    if cache is None:
        raise AppException(status_code=503, code="cache_disabled", message="缓存未启用")
    return cache
