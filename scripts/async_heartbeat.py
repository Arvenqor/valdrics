"""Shared async runner utilities for script-driven app and DB probes."""

from __future__ import annotations

import asyncio
import asyncio.runners as asyncio_runners
import threading
import warnings
from collections.abc import Awaitable
from typing import Any


_HEARTBEAT_INTERVAL_SECONDS = 0.01
_SHUTDOWN_TIMEOUT_SECONDS = 5.0


async def heartbeat_loop(
    stop: asyncio.Event,
    *,
    interval_seconds: float = _HEARTBEAT_INTERVAL_SECONDS,
) -> None:
    while not stop.is_set():
        await asyncio.sleep(interval_seconds)


async def await_with_heartbeat(
    awaitable: Awaitable[Any],
    *,
    interval_seconds: float = _HEARTBEAT_INTERVAL_SECONDS,
) -> Any:
    stop = asyncio.Event()
    heartbeat = asyncio.create_task(
        heartbeat_loop(stop, interval_seconds=interval_seconds)
    )
    try:
        return await awaitable
    finally:
        stop.set()
        await heartbeat


def _start_loop_waker(
    loop: asyncio.AbstractEventLoop,
    *,
    interval_seconds: float,
) -> tuple[threading.Event, threading.Thread]:
    stop = threading.Event()

    def _wake_loop() -> None:
        while not stop.wait(interval_seconds):
            try:
                loop.call_soon_threadsafe(lambda: None)
            except RuntimeError:
                break

    wake_thread = threading.Thread(
        target=_wake_loop,
        name="script-event-loop-waker",
        daemon=True,
    )
    wake_thread.start()
    return stop, wake_thread


def _cancel_all_tasks_with_timeout(loop: asyncio.AbstractEventLoop) -> None:
    to_cancel = asyncio.all_tasks(loop)
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    try:
        loop.run_until_complete(
            asyncio.wait_for(
                asyncio.gather(*to_cancel, return_exceptions=True),
                timeout=_SHUTDOWN_TIMEOUT_SECONDS,
            )
        )
    except TimeoutError:
        warnings.warn(
            "script async runner teardown timed out during cancel_all_tasks",
            RuntimeWarning,
            stacklevel=2,
        )


def _run_shutdown_step_with_timeout(
    loop: asyncio.AbstractEventLoop,
    *,
    step: str,
    awaitable: Awaitable[Any],
) -> None:
    try:
        loop.run_until_complete(
            asyncio.wait_for(awaitable, timeout=_SHUTDOWN_TIMEOUT_SECONDS)
        )
    except TimeoutError:
        warnings.warn(
            f"script async runner teardown timed out during {step}",
            RuntimeWarning,
            stacklevel=2,
        )


def run_async_with_heartbeat(
    awaitable: Awaitable[Any],
    *,
    interval_seconds: float = _HEARTBEAT_INTERVAL_SECONDS,
) -> Any:
    loop = asyncio.new_event_loop()
    asyncio_runners.events.set_event_loop(loop)
    stop, wake_thread = _start_loop_waker(loop, interval_seconds=interval_seconds)
    try:
        return loop.run_until_complete(
            await_with_heartbeat(awaitable, interval_seconds=interval_seconds)
        )
    finally:
        try:
            _cancel_all_tasks_with_timeout(loop)
            _run_shutdown_step_with_timeout(
                loop,
                step="shutdown_asyncgens",
                awaitable=loop.shutdown_asyncgens(),
            )
            _run_shutdown_step_with_timeout(
                loop,
                step="shutdown_default_executor",
                awaitable=loop.shutdown_default_executor(
                    asyncio_runners.constants.THREAD_JOIN_TIMEOUT
                ),
            )
        finally:
            asyncio_runners.events.set_event_loop(None)
            loop.close()
            stop.set()
            wake_thread.join(timeout=1)
