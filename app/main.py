"""ASGI application entry point."""

from fastapi import FastAPI

from app.api.router import api_v1_router, system_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an isolated application instance for production and tests."""
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url="/redoc" if resolved_settings.docs_enabled else None,
        openapi_url="/openapi.json" if resolved_settings.docs_enabled else None,
        lifespan=lifespan,
    )
    # Settings live on app.state so every application instance can be configured independently.
    app.state.settings = resolved_settings

    register_exception_handlers(app)
    app.add_middleware(
        RequestContextMiddleware,
        request_id_header=resolved_settings.request_id_header,
    )
    app.include_router(system_router)
    app.include_router(api_v1_router, prefix=resolved_settings.api_v1_prefix)
    return app


app = create_app()
