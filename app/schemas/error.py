"""标准化异常处理器使用的数据模型。"""

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
