"""Schemas used by the standardized error handlers."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    location: list[str]
    message: str
    type: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str
    details: Any | None = Field(default=None)
