# 第二阶段：数据访问

## 安装

基础应用不需要数据库或 Redis，可直接使用 `uv sync` 启动。
开发和测试请运行：

```bash
uv sync --all-extras
uv run --all-extras pytest
```

按需安装运行依赖：

```bash
uv sync --extra postgres --extra redis
# 或
uv sync --extra mysql --extra redis
```

SQLAlchemy 固定使用 2.0 系列，PostgreSQL 使用 asyncpg，MySQL 使用 asyncmy。
MySQL 可选依赖包含 cryptography，支持 MySQL 8 默认的 caching_sha2_password 认证。
启用组件后缺少驱动、连接失败或超时都会让启动失败；关闭组件则不会导入对应依赖。

## 配置与连接

在 .env 中设置：

```dotenv
EASY_FASTAPI_DATABASE_ENABLED=true
EASY_FASTAPI_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/easy_fastapi
EASY_FASTAPI_REDIS_ENABLED=true
EASY_FASTAPI_REDIS_URL=redis://localhost:16379/0
```

MySQL 示例地址为 `mysql+asyncmy://root:mysql@localhost:13306/easy_fastapi`。
上述端口对应项目的 `compose.test.yml`；通常安装的服务端口为 5432、3306、6379。
密码含特殊字符时需 URL 编码。配置使用 SecretStr，常规配置打印不会显示密码。

连接池默认大小 5，最多额外创建 10 个连接；每个工作进程拥有自己的池。
连接池在取连接时执行存活检测。启动和就绪检查的默认超时为 5 秒，可配置
`EASY_FASTAPI_DEPENDENCY_TIMEOUT`；这不是业务 SQL 的执行超时。

## 使用数据库

在业务路由中通过依赖获取会话：

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import get_session

router = APIRouter()


@router.get("/database-ping")
async def database_ping(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, int]:
    result = await session.execute(text("SELECT 1"))
    return {"value": result.scalar_one()}
```

写入时由业务代码执行 `await session.commit()`，异常处理后需要继续使用同一个
会话时先执行 `await session.rollback()`。请求退出自动关闭会话并回滚未提交事务。
不要在并发任务间共享会话，也不要把请求会话传入后台任务。

## 使用缓存

路由通过 `Depends(get_cache)` 获得 Cache，支持：

```python
await cache.set("greeting", "hello", ttl=300)
value = await cache.get("greeting")
await cache.delete("greeting")
```

值使用字符串；未命中返回 None。键自动加上配置前缀，默认 `easy_fastapi:`。
过期时间必须为正整数。未启用组件却调用依赖时返回 503。
连接由应用生命周期创建并在退出时释放。

## 数据库迁移

先安装 postgres 或 mysql extra，并配置数据库地址，然后执行：

```bash
uv run --extra postgres alembic upgrade head
uv run --extra postgres alembic current
uv run --extra postgres alembic check
```

MySQL 将上述 `--extra postgres` 换成 `--extra mysql`。

当前 0001 是空基线，只建立版本记录，不预置业务表。添加业务模型时：
1. 继承 `app.infrastructure.models.Base`。
2. 在 `migrations/env.py` 中导入模型。
3. 执行 `alembic revision --autogenerate -m "描述变更"`。
4. 人工检查迁移文件，再执行 `alembic upgrade head`。

迁移是独立部署步骤，应用启动不会自动建表或迁移。
回退命令是 `alembic downgrade -1`，回退可能删除数据，执行前应审查迁移并备份。
MySQL 的 DDL 不保证事务回滚，失败后需检查实际表结构。

## 健康检查

- `GET /health`：检查应用进程。
- `GET /health/ready`：检查已启用的数据库与 Redis。
- 未启用组件显示 disabled；连接成功显示 ok；不可用显示 unavailable 并返回 HTTP 503。
- 不返回原始异常和连接地址。检查超时有上限，两个组件按顺序检查。

## 测试

本地默认测试使用临时 SQLite 文件验证事务和迁移，使用模拟客户端验证生命周期和故障处理。
SQLite 仅用于测试，不作为生产配置支持范围。真实服务测试需要专用空数据库，
迁移测试会升降级该库，不要指向业务数据库。

```powershell
docker compose -p easy-fastapi-phase2 -f compose.test.yml up -d --wait
$env:TEST_POSTGRES_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:15432/easy_fastapi"
$env:TEST_MYSQL_URL = "mysql+asyncmy://root:mysql@127.0.0.1:13306/easy_fastapi"
$env:TEST_REDIS_URL = "redis://127.0.0.1:16379/0"
uv run --all-extras pytest
docker compose -p easy-fastapi-phase2 -f compose.test.yml down -v
```

最后一条命令会删除这组临时测试容器及其数据。CI 使用相同测试方式。
本地验收使用 PostgreSQL 17 Alpine、MySQL 8.4 和 Redis 7 容器，22 项测试全部通过，
无跳过项，应用覆盖率 94.24%。包含两种数据库的真实提交与回滚、三种数据库的
迁移升降级与差异检查，以及 Redis 读写、过期和删除测试。
