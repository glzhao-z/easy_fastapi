"""应用异常与标准化错误响应。"""

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.error import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """可以安全返回给 API 调用方的预期应用异常。"""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = dict(headers) if headers else None


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    response_headers = dict(headers) if headers else {}
    response_headers.setdefault("X-Request-ID", request_id)
    body = ErrorResponse(
        code=code,
        message=message,
        request_id=request_id,
        details=details,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", exclude_none=True),
        headers=response_headers,
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
    details = None if isinstance(exc.detail, str) else exc.detail
    return _error_response(
        request,
        status_code=exc.status_code,
        code=f"http_{exc.status_code}",
        message=message,
        details=details,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    # 不回显无效输入值，仅向客户端返回错误位置与说明，避免泄露敏感数据。
    details = [
        ErrorDetail(
            location=[str(part) for part in error["loc"]],
            message=error["msg"],
            type=error["type"],
        ).model_dump(mode="json")
        for error in exc.errors()
    ]
    return _error_response(
        request,
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        details=details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application exception", exc_info=exc)
    return _error_response(
        request,
        status_code=500,
        code="internal_server_error",
        message="An unexpected error occurred",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册异常处理器，避免业务模块与 HTTP 响应细节耦合。"""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, AppException)
        return await app_exception_handler(request, exc)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, StarletteHTTPException)
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RequestValidationError)
        return await validation_exception_handler(request, exc)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        return await unhandled_exception_handler(request, exc)
