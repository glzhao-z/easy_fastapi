"""Schemas for the reference business module."""

from pydantic import BaseModel


class PingResponse(BaseModel):
    message: str
