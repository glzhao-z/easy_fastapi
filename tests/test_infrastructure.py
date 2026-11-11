"""第二阶段的连接、事务和故障处理测试。"""

import asyncio
from pathlib import Path
from typing import Annotated
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Request
from httpx2 import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import Column, Integer, MetaData, Table, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.dependencies.services import get_cache, get_session
from app.infrastructure.cache import Cache
from app.infrastructure.database import Database
from app.main import create_app

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("component", ["database", "redis"])
def test_enabled_service_requires_url(component: str) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_enabled=component == "database",
            redis_enabled=component == "redis",
        )


async def test_database_commit_and_rollback(tmp_path: Path) -> None:
    database = Database("sqlite+aiosqlite:///" + (tmp_path / "test.db").as_posix())
    try:
        await database.ping()
        async with database.engine.begin() as connection:
            await connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY)"))
        async with database.sessions() as session:
            await session.execute(text("INSERT INTO items VALUES (1)"))
            await session.commit()
        async with database.sessions() as session:
            await session.execute(text("INSERT INTO items VALUES (2)"))
        async with database.sessions() as session:
            assert (await session.execute(text("SELECT id FROM items"))).scalars().all() == [1]
        # 验证请求依赖在异常后退出，未提交事务不会保留。
        app = create_app(Settings(_env_file=None))
        app.state.database = database
        request = Request({"type": "http", "app": app})
        dependency = get_session(request)
        session = await anext(dependency)
        await session.execute(text("INSERT INTO items VALUES (3)"))
        await dependency.aclose()
        async with database.sessions() as session:
            assert (await session.execute(text("SELECT COUNT(*) FROM items"))).scalar() == 1
    finally:
        await database.close()


async def test_disabled_dependencies(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/database-test")
    async def database_test(
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/cache-test")
    async def cache_test(cache: Annotated[Cache, Depends(get_cache)]) -> dict[str, bool]:
        return {"ok": True}

    assert (await client.get("/database-test")).status_code == 503
    assert (await client.get("/cache-test")).status_code == 503
    assert (await client.get("/health/ready")).json() == {
        "database": "disabled",
        "cache": "disabled",
    }


async def test_cache_interface() -> None:
    cache = Cache("redis://localhost:6379/0", "test:", 1)
    original_client = cache.client
    mock = AsyncMock()
    cache.client = mock
    mock.get.return_value = "hello"
    assert await cache.get("key") == "hello"
    await cache.set("key", "hello", ttl=10)
    mock.set.assert_awaited_once_with("test:key", "hello", ex=10)
    await cache.delete("key")
    mock.delete.assert_awaited_once_with("test:key")
    await cache.ping()
    with pytest.raises(ValueError):
        await cache.set("key", "bad", ttl=0)
    await cache.close()
    mock.aclose.assert_awaited_once()
    await original_client.aclose()


async def test_lifespan_and_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    database = AsyncMock()
    cache = AsyncMock()
    monkeypatch.setattr("app.infrastructure.database.Database", lambda *args: database)
    monkeypatch.setattr("app.infrastructure.cache.Cache", lambda *args: cache)
    settings = Settings(
        _env_file=None,
        database_enabled=True,
        redis_enabled=True,
        database_url="postgresql+asyncpg://user:password@localhost/test",
        redis_url="redis://localhost:6379/0",
        dependency_timeout=0.01,
    )
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        assert (await client.get("/health/ready")).status_code == 200
        assert await get_cache(Request({"type": "http", "app": app})) is cache
        cache.ping.side_effect = RuntimeError("secret")
        response = await client.get("/health/ready")
        assert response.status_code == 503
        assert "secret" not in response.text
        assert (await client.get("/health")).status_code == 200

        async def slow_ping() -> None:
            await asyncio.sleep(1)

        cache.ping.side_effect = slow_ping
        assert (await client.get("/health/ready")).status_code == 503
    database.close.assert_awaited_once()
    cache.close.assert_awaited_once()
    assert app.state.database is None
    assert app.state.cache is None


async def test_failed_startup_closes_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    database = AsyncMock()
    cache = AsyncMock()
    cache.ping.side_effect = ConnectionError("unavailable")
    monkeypatch.setattr("app.infrastructure.database.Database", lambda *args: database)
    monkeypatch.setattr("app.infrastructure.cache.Cache", lambda *args: cache)
    app = create_app(
        Settings(
            _env_file=None,
            database_enabled=True,
            redis_enabled=True,
            database_url="mysql+asyncmy://user:password@localhost/test",
            redis_url="redis://localhost:6379/0",
        )
    )
    with pytest.raises(ConnectionError):
        async with app.router.lifespan_context(app):
            pytest.fail("不应进入启动完成状态")
    database.close.assert_awaited_once()
    cache.close.assert_awaited_once()


@pytest.mark.integration
@pytest.mark.parametrize("variable", ["TEST_POSTGRES_URL", "TEST_MYSQL_URL"])
async def test_real_database(variable: str) -> None:
    import os

    url = os.environ.get(variable)
    if not url:
        pytest.skip(variable + " 未设置")
    database = Database(url)
    # 使用独立测试表，验证两种数据库真实的提交和回滚行为。
    metadata = MetaData()
    table = Table("test_" + uuid4().hex, metadata, Column("id", Integer, primary_key=True))
    created = False
    try:
        await database.ping()
        async with database.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        created = True
        async with database.sessions() as session:
            await session.execute(table.insert().values(id=1))
            await session.commit()
            await session.execute(table.insert().values(id=2))
            await session.rollback()
        async with database.sessions() as session:
            assert (await session.execute(select(table.c.id))).scalars().all() == [1]
    finally:
        try:
            if created:
                async with database.engine.begin() as connection:
                    await connection.run_sync(metadata.drop_all)
        finally:
            await database.close()


@pytest.mark.integration
async def test_real_redis() -> None:
    import os

    url = os.environ.get("TEST_REDIS_URL")
    if not url:
        pytest.skip("TEST_REDIS_URL 未设置")
    cache = Cache(url, "test:" + uuid4().hex + ":", 2)
    try:
        await cache.ping()
        await cache.set("key", "hello", ttl=1)
        assert await cache.get("key") == "hello"
        await asyncio.sleep(1.1)
        assert await cache.get("key") is None
        await cache.set("key", "bye")
        await cache.delete("key")
        assert await cache.get("key") is None
    finally:
        await cache.delete("key")
        await cache.close()
