"""Structured application logging with request correlation."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")

_STANDARD_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {
    "asctime",
    "message",
}


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line so logs remain machine-readable."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_context.get()),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_LOG_RECORD_FIELDS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class _EasyFastAPIStreamHandler(logging.StreamHandler[Any]):
    """Marker type used to keep logging configuration idempotent."""


def configure_logging(level: str) -> None:
    """Configure a single idempotent handler for the root logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = next(
        (
            existing
            for existing in root_logger.handlers
            if isinstance(existing, _EasyFastAPIStreamHandler)
        ),
        None,
    )
    if handler is None:
        handler = _EasyFastAPIStreamHandler(sys.stdout)
        root_logger.addHandler(handler)
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())
