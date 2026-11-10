"""Request context and routing tests."""

import re

import pytest
from httpx2 import AsyncClient

pytestmark = pytest.mark.anyio


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "name": "easy_fastapi",
        "version": "0.1.0",
        "environment": "test",
    }


async def test_versioned_example_route(client: AsyncClient) -> None:
    response = await client.get("/api/v1/examples/ping")

    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


async def test_request_id_is_preserved(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "client-request-42"})

    assert response.headers["X-Request-ID"] == "client-request-42"


async def test_unsafe_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "unsafe value"})

    request_id = response.headers["X-Request-ID"]
    assert request_id != "unsafe value"
    assert re.fullmatch(r"[0-9a-f]{32}", request_id)
