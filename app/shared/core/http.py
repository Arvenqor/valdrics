"""
Async HTTP Client Shared Infrastructure (2026 Standards)

Ensures singleton httpx.AsyncClient usage across both FastAPI lifespan
and background workers to prevent socket exhaustion and optimize latency.
"""

import asyncio
from collections.abc import Awaitable, Coroutine
import inspect
from typing import Optional
import httpx
import structlog

from app.shared.core.outbound_tls import resolve_outbound_tls_verification

logger = structlog.get_logger()
_DEFAULT_HTTP_TIMEOUT = 20.0

# Singleton instances
_client: Optional[httpx.AsyncClient] = None
_insecure_client: Optional[httpx.AsyncClient] = None
_configured_clients: dict[tuple[bool, float], httpx.AsyncClient] = {}


def _current_loop_marker() -> int | None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return None
    if loop.is_closed():
        return None
    return id(loop)


def _build_http_client(
    *,
    verify: bool,
    timeout: Optional[float],
    limits: httpx.Limits | None = None,
    user_agent: str | None = None,
) -> httpx.AsyncClient:
    resolved_timeout = float(timeout or _DEFAULT_HTTP_TIMEOUT)
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(resolved_timeout, connect=10.0),
        limits=limits or httpx.Limits(max_connections=100, max_keepalive_connections=20),
        http2=True,
        verify=verify,
        headers={"User-Agent": user_agent} if user_agent else None,
    )
    setattr(client, "_valdrics_loop_marker", _current_loop_marker())
    setattr(client, "_valdrics_timeout", resolved_timeout)
    setattr(client, "_valdrics_verify", verify)
    return client


def _normalize_timeout(timeout: Optional[float]) -> float:
    return float(timeout or _DEFAULT_HTTP_TIMEOUT)


def _client_key(*, verify: bool, timeout: Optional[float]) -> tuple[bool, float]:
    return (verify, _normalize_timeout(timeout))


def _is_default_client_key(key: tuple[bool, float]) -> bool:
    return key[1] == _DEFAULT_HTTP_TIMEOUT


def _set_cached_client(
    key: tuple[bool, float], client: httpx.AsyncClient | None
) -> None:
    global _client, _insecure_client
    if client is None:
        _configured_clients.pop(key, None)
    else:
        _configured_clients[key] = client

    if _is_default_client_key(key):
        if key[0]:
            _client = client
        else:
            _insecure_client = client


def _get_cached_client(key: tuple[bool, float]) -> httpx.AsyncClient | None:
    client = _configured_clients.get(key)
    if client is not None:
        return client
    if not _is_default_client_key(key):
        return None
    alias = _client if key[0] else _insecure_client
    if alias is not None:
        _configured_clients[key] = alias
    return alias


def _drop_cached_client_reference(client: httpx.AsyncClient) -> None:
    global _client, _insecure_client
    for key, cached in list(_configured_clients.items()):
        if cached is client:
            _configured_clients.pop(key, None)
    if _client is client:
        _client = None
    if _insecure_client is client:
        _insecure_client = None


def _schedule_client_close(client: httpx.AsyncClient) -> None:
    aclose = getattr(client, "aclose", None)
    if not callable(aclose):
        return

    close_result = aclose()
    if inspect.isawaitable(close_result):
        close_awaitable = close_result
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            close = getattr(close_awaitable, "close", None)
            if callable(close):
                close()
            return
        if isinstance(close_awaitable, Coroutine):
            loop.create_task(close_awaitable)
            return

        async def _await_close_result(result: Awaitable[object]) -> None:
            await result

        loop.create_task(_await_close_result(close_awaitable))


def _client_needs_reinitialization(client: httpx.AsyncClient) -> bool:
    if getattr(client, "is_closed", False):
        return True

    current_loop_marker = _current_loop_marker()
    client_loop_marker = getattr(client, "_valdrics_loop_marker", None)
    return bool(
        current_loop_marker is not None
        and client_loop_marker is not None
        and current_loop_marker != client_loop_marker
    )


def get_http_client(
    verify: bool = True, timeout: Optional[float] = None
) -> httpx.AsyncClient:
    """
    Returns a global shared httpx.AsyncClient.
    Maintains separate pools for secure and explicitly authorized insecure connections.
    """
    global _client, _insecure_client
    verify = resolve_outbound_tls_verification(verify)
    key = _client_key(verify=verify, timeout=timeout)
    target = _get_cached_client(key)

    if target is not None and _client_needs_reinitialization(target):
        logger.warning(
            "http_client_reinitialized",
            verify=verify,
            timeout_seconds=key[1],
            reason="closed_or_event_loop_changed",
        )
        _schedule_client_close(target)
        _drop_cached_client_reference(target)
        target = None

    if target is None:
        logger.warning(
            "http_client_lazy_initialized",
            verify=verify,
            timeout_seconds=key[1],
            msg="Client was not pre-initialized",
        )
        new_client = _build_http_client(verify=verify, timeout=key[1])
        _set_cached_client(key, new_client)
        return new_client

    return target


async def init_http_client() -> None:
    """
    Initializes the global httpx.AsyncClient with 2026 production settings.
    """
    key = _client_key(verify=True, timeout=_DEFAULT_HTTP_TIMEOUT)
    if _get_cached_client(key) is not None:
        logger.warning("http_client_already_initialized")
        return

    secure_client = _build_http_client(
        verify=True,
        timeout=_DEFAULT_HTTP_TIMEOUT,
        limits=httpx.Limits(
            max_connections=500,
            max_keepalive_connections=50,
            keepalive_expiry=30.0,
        ),
        user_agent="Valdrics/2026.02",
    )
    _set_cached_client(key, secure_client)
    logger.info("http_client_initialized", http2=True, max_connections=500)


async def close_http_client() -> None:
    """
    Gracefully shuts down the global client, flushing all connection pools.
    """
    global _client, _insecure_client

    async def _close_one(client: object | None, label: str) -> None:
        if not client:
            return

        close_result = None
        aclose = getattr(client, "aclose", None)
        if callable(aclose):
            close_result = aclose()
        else:
            close = getattr(client, "close", None)
            if callable(close):
                close_result = close()

        if inspect.isawaitable(close_result):
            await close_result

        logger.info("http_client_closed", verify=label == "secure")

    clients_to_close: list[tuple[object, str]] = []
    seen: set[int] = set()
    for client, label in [
        *(
            (configured, "secure" if key[0] else "insecure")
            for key, configured in _configured_clients.items()
        ),
        (_client, "secure"),
        (_insecure_client, "insecure"),
    ]:
        if client is None:
            continue
        client_id = id(client)
        if client_id in seen:
            continue
        seen.add(client_id)
        clients_to_close.append((client, label))

    for client, label in clients_to_close:
        await _close_one(client, label)

    _client = None
    _insecure_client = None
    _configured_clients.clear()
