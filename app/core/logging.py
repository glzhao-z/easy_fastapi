"""支持请求关联的结构化应用日志。"""

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
    """每行输出一个 JSON 对象，便于日志系统解析。"""

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
    """用于保证日志配置幂等的标记类型。"""


def configure_logging(level: str) -> None:
    """为根日志记录器配置唯一且可重复调用的处理器。"""
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
