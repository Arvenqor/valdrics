import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.shared.core.timeout import TimeoutMiddleware


@pytest.mark.asyncio
async def test_timeout_middleware_returns_504_on_timeout():
    app = FastAPI()
    middleware = TimeoutMiddleware(app, timeout_seconds=0.001)

    async def call_next(_request: Request) -> Response:
        await asyncio.sleep(0.01)
        return Response("ok")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/slow",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "server": ("testserver", 80),
    }
    request = Request(scope)
    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 504


@pytest.mark.asyncio
async def test_timeout_middleware_uses_live_request_timeout_when_not_overridden():
    app = FastAPI()
    middleware = TimeoutMiddleware(app)

    observed: list[float] = []

    async def fake_wait_for(awaitable, *, timeout):
        observed.append(timeout)
        return await awaitable

    async def call_next(_request: Request) -> Response:
        return Response("ok")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/ok",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "server": ("testserver", 80),
    }
    request = Request(scope)

    first_settings = SimpleNamespace(REQUEST_TIMEOUT=3)
    second_settings = SimpleNamespace(REQUEST_TIMEOUT=9)
    with (
        patch(
            "app.shared.core.timeout.get_settings",
            side_effect=[first_settings, second_settings],
        ),
        patch("app.shared.core.timeout.asyncio.wait_for", side_effect=fake_wait_for),
    ):
        first = await middleware.dispatch(request, call_next)
        second = await middleware.dispatch(request, call_next)

    assert first.status_code == 200
    assert second.status_code == 200
    assert observed == [3.0, 9.0]
