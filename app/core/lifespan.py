"""应用启动与关闭时管理可选连接。"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from app.core.config import Settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    app.state.database = None
    app.state.cache = None
    try:
        # 先注册清理再检查连接，后续初始化失败也会释放已有资源。
        async with AsyncExitStack() as resources:
            if settings.database_enabled:
                try:
                    from app.infrastructure.database import Database
                except ImportError as exc:
                    raise RuntimeError("请先安装 postgres 或 mysql 可选依赖") from exc
                assert settings.database_url is not None
                database = Database(
                    settings.database_url.get_secret_value(),
                    settings.database_pool_size,
                    settings.database_max_overflow,
                )
                resources.push_async_callback(database.close)
                await asyncio.wait_for(database.ping(), settings.dependency_timeout)
                app.state.database = database

            if settings.redis_enabled:
                try:
                    from app.infrastructure.cache import Cache
                except ImportError as exc:
                    raise RuntimeError("请先安装 redis 可选依赖") from exc
                assert settings.redis_url is not None
                cache = Cache(
                    settings.redis_url.get_secret_value(),
                    settings.redis_key_prefix,
                    settings.dependency_timeout,
                )
                resources.push_async_callback(cache.close)
                await asyncio.wait_for(cache.ping(), settings.dependency_timeout)
                app.state.cache = cache

            logger.info("Application started")
            yield
    finally:
        app.state.database = None
        app.state.cache = None
        logger.info("Application stopped")
