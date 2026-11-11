"""测试应用共享夹具。"""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx2 import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        debug=False,
        log_level="WARNING",
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def anyio_backend() -> str:
    """测试仅使用生产环境采用的 asyncio 后端。"""
    return "asyncio"


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    # ASGITransport 不负责管理生命周期，因此由测试夹具显式进入生命周期上下文。
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=transport, base_url="http://testserver") as test_client,
    ):
        yield test_client
