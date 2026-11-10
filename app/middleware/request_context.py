"""Request correlation and access logging middleware."""

import logging
import re
import time
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import request_id_context

logger = logging.getLogger("easy_fastapi.access")
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class RequestContextMiddleware:
    """Attach a safe request ID and emit one access log for every HTTP request."""

    def __init__(self, app: ASGIApp, request_id_header: str = "X-Request-ID") -> None:
        self.app = app
        self.request_id_header = request_id_header

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied_request_id = Headers(scope=scope).get(self.request_id_header)
        request_id = (
            supplied_request_id
            if supplied_request_id and _SAFE_REQUEST_ID.fullmatch(supplied_request_id)
            else uuid4().hex
        )
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_context.set(request_id)
        started_at = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # Replace a handler-provided value instead of emitting duplicate headers.
                MutableHeaders(scope=message)[self.request_id_header] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
            logger.info(
                "Request completed",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_context.reset(token)
