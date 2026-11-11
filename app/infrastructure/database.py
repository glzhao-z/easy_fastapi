"""异步数据库连接与会话工厂。"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class Database:
    """应用共用连接池，每个请求创建独立会话。"""

    def __init__(self, url: str, pool_size: int = 5, max_overflow: int = 10) -> None:
        self.engine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            hide_parameters=True,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def ping(self) -> None:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self.engine.dispose()
