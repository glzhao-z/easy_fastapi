"""Redis 字符串缓存接口。"""

from redis.asyncio import Redis


class Cache:
    def __init__(self, url: str, prefix: str, timeout: float) -> None:
        self.prefix = prefix
        self.client = Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )

    async def get(self, key: str) -> str | None:
        value = await self.client.get(self.prefix + key)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        """默认五分钟过期。"""
        if ttl <= 0:
            raise ValueError("缓存过期时间必须大于零")
        await self.client.set(self.prefix + key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(self.prefix + key)

    async def ping(self) -> None:
        await self.client.ping()

    async def close(self) -> None:
        await self.client.aclose()
