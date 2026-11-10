"""Application metadata and health endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.dependencies.settings import get_app_settings
from app.schemas.system import AppInfo, HealthResponse

router = APIRouter(tags=["system"])
AppSettings = Annotated[Settings, Depends(get_app_settings)]


@router.get("/", response_model=AppInfo)
async def application_info(settings: AppSettings) -> AppInfo:
    """Return a small discovery document without wrapping the successful response."""
    return AppInfo(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        docs_url="/docs" if settings.docs_enabled else None,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: AppSettings) -> HealthResponse:
    """Report process health; dependency checks will be added with Phase 2 resources."""
    return HealthResponse(
        status="ok",
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
