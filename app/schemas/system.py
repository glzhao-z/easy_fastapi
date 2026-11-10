"""System endpoint schemas."""

from pydantic import BaseModel

from app.core.config import Environment


class AppInfo(BaseModel):
    name: str
    version: str
    environment: Environment
    docs_url: str | None


class HealthResponse(BaseModel):
    status: str
    name: str
    version: str
    environment: Environment
