"""应用元数据与健康检查接口。"""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.config import Settings
from app.dependencies.settings import get_app_settings
from app.schemas.system import AppInfo, HealthResponse

router = APIRouter(tags=["system"])
AppSettings = Annotated[Settings, Depends(get_app_settings)]


@router.get("/", response_model=AppInfo)
async def application_info(settings: AppSettings) -> AppInfo:
    """返回精简的应用发现信息，不包装成功响应。"""
    return AppInfo(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        docs_url="/docs" if settings.docs_enabled else None,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: AppSettings) -> HealthResponse:
    """仅检查进程存活，外部依赖故障不应触发进程反复重启。"""
    return HealthResponse(
        status="ok",
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/health/ready")
async def readiness(request: Request, response: Response, settings: AppSettings) -> dict[str, str]:
    """检查启用的组件，任何连接不可用时返回 503。"""
    result = {}
    for name, enabled in (
        ("database", settings.database_enabled),
        ("cache", settings.redis_enabled),
    ):
        if not enabled:
            result[name] = "disabled"
            continue
        service = getattr(request.app.state, name, None)
        try:
            if service is None:
                raise RuntimeError("组件未初始化")
            await asyncio.wait_for(service.ping(), settings.dependency_timeout)
            result[name] = "ok"
        except Exception:
            # 不向客户端暴露连接地址或密码。
            result[name] = "unavailable"
            response.status_code = 503
    return result
