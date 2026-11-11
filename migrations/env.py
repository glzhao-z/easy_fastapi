"""从环境配置读取连接地址，执行异步数据库迁移。"""

import asyncio

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.infrastructure.models import Base

# 新业务模型在此显式导入，让自动迁移发现对应的表。
settings = Settings()
if settings.database_url is None:
    raise RuntimeError("执行迁移必须配置 EASY_FASTAPI_DATABASE_URL")
url = settings.database_url.get_secret_value()


def migrate(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def migrate_online() -> None:
    engine = create_async_engine(url, poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(migrate)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(migrate_online())
