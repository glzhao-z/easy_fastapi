"""错误响应契约测试。"""

import pytest
from fastapi import FastAPI
from httpx2 import AsyncClient

from app.core.exceptions import AppException

pytestmark = pytest.mark.anyio


async def test_not_found_uses_standard_error_contract(client: AsyncClient) -> None:
    response = await client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "code": "http_404",
        "message": "Not Found",
        "request_id": response.headers["X-Request-ID"],
    }


async def test_expected_application_error_is_safe(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    @app.get("/expected-error")
    async def expected_error() -> None:
        raise AppException(
            status_code=409,
            code="resource_conflict",
            message="Resource already exists",
            details={"field": "name"},
        )

    response = await client.get("/expected-error")

    assert response.status_code == 409
    assert response.json()["code"] == "resource_conflict"
    assert response.json()["details"] == {"field": "name"}


async def test_unhandled_exception_does_not_leak_details(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    @app.get("/unexpected-error")
    async def unexpected_error() -> None:
        raise RuntimeError("sensitive implementation detail")

    response = await client.get("/unexpected-error")

    assert response.status_code == 500
    assert response.json()["code"] == "internal_server_error"
    assert "sensitive" not in response.text
