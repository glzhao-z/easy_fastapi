"""Dependencies for application-scoped configuration."""

from fastapi import Request

from app.core.config import Settings


def get_app_settings(request: Request) -> Settings:
    """Read settings from the current app instead of a module-level singleton."""
    settings: Settings = request.app.state.settings
    return settings
