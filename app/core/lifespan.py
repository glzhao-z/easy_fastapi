"""Application startup and shutdown lifecycle."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own process-wide resources and release them in reverse order on shutdown."""
    settings = app.state.settings
    logger.info(
        "Application started",
        extra={"app_name": settings.app_name, "environment": settings.environment},
    )
    try:
        # Database and cache clients will be created here in Phase 2.
        yield
    finally:
        logger.info("Application stopped", extra={"app_name": settings.app_name})
