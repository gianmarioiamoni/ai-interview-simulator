# app/process_edge/shutdown.py
#
# EPIC-08 P5/C12 — process-edge SIGTERM drain (SDN-01, SDN-02; rejects AR-12).
# Lifecycle only: admit/reject HTTP, track in-flight, wait within Settings timeout.
# No Domain, LangGraph, or InterviewState participation.

from __future__ import annotations

import asyncio
import logging
import signal
import threading
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

_DRAIN_REJECT_BODY = b'{"status":"draining","detail":"process is shutting down"}'
_DRAIN_REJECT_HEADERS = [(b"content-type", b"application/json")]


class DrainOutcome(str, Enum):
    CLEAN = "clean"
    TIMEOUT = "timeout"


class ShutdownDrainController:
    """Process-edge drain gate: stop admit, finish in-flight, timeout observably."""

    def __init__(self, drain_timeout_s: float) -> None:
        if drain_timeout_s < 0:
            raise ValueError("drain_timeout_s must be >= 0")
        self._drain_timeout_s = float(drain_timeout_s)
        self._draining = False
        self._in_flight = 0
        self._lock = threading.Lock()
        self._idle = threading.Event()
        self._idle.set()
        self._last_outcome: DrainOutcome | None = None

    @property
    def drain_timeout_s(self) -> float:
        return self._drain_timeout_s

    @property
    def is_draining(self) -> bool:
        with self._lock:
            return self._draining

    @property
    def in_flight(self) -> int:
        with self._lock:
            return self._in_flight

    @property
    def last_outcome(self) -> DrainOutcome | None:
        return self._last_outcome

    def begin_drain(self) -> None:
        with self._lock:
            if not self._draining:
                self._draining = True

    def try_admit(self) -> bool:
        """Admit one unit of work. False when draining (caller must reject)."""
        with self._lock:
            if self._draining:
                return False
            self._in_flight += 1
            self._idle.clear()
            return True

    def release(self) -> None:
        with self._lock:
            if self._in_flight > 0:
                self._in_flight -= 1
            if self._in_flight == 0:
                self._idle.set()

    def wait_for_idle(self, timeout_s: float | None = None) -> DrainOutcome:
        """Block until in-flight reaches zero or timeout. Records last_outcome."""
        timeout = self._drain_timeout_s if timeout_s is None else float(timeout_s)
        outcome = (
            DrainOutcome.CLEAN
            if self._idle.wait(timeout=timeout)
            else DrainOutcome.TIMEOUT
        )
        self._last_outcome = outcome
        return outcome


class DrainMiddleware:
    """ASGI middleware: reject new HTTP/WebSocket during drain; track in-flight."""

    def __init__(self, app: ASGIApp, controller: ShutdownDrainController) -> None:
        self.app = app
        self.controller = controller

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type = scope["type"]
        if scope_type not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        if not self.controller.try_admit():
            if scope_type == "http":
                await send(
                    {
                        "type": "http.response.start",
                        "status": 503,
                        "headers": _DRAIN_REJECT_HEADERS,
                    }
                )
                await send({"type": "http.response.body", "body": _DRAIN_REJECT_BODY})
            return
        try:
            await self.app(scope, receive, send)
        finally:
            self.controller.release()


def install_sigterm_drain_handler(
    controller: ShutdownDrainController,
) -> Callable[[], None]:
    """Begin drain on SIGTERM, then chain to the previous handler. Returns restore."""
    try:
        previous = signal.getsignal(signal.SIGTERM)
    except (OSError, ValueError):
        return lambda: None

    def _handler(signum: int, frame: Any) -> None:
        controller.begin_drain()
        if callable(previous) and previous not in (signal.SIG_DFL, signal.SIG_IGN):
            previous(signum, frame)

    try:
        signal.signal(signal.SIGTERM, _handler)
    except ValueError:
        return lambda: None

    def _restore() -> None:
        try:
            signal.signal(signal.SIGTERM, previous)
        except ValueError:
            return

    return _restore


def get_shutdown_drain(app: Any) -> ShutdownDrainController | None:
    """Resolve the drain controller from a process-edge ASGI app or wrapper."""
    if isinstance(app, DrainMiddleware):
        return app.controller
    state = getattr(app, "state", None)
    if state is not None:
        found = getattr(state, "shutdown_drain", None)
        if found is not None:
            return found
    inner = getattr(app, "app", None)
    if inner is not None and inner is not app:
        return get_shutdown_drain(inner)
    return None


@asynccontextmanager
async def process_edge_lifespan(app: Any) -> AsyncIterator[None]:
    """Install SIGTERM drain at startup; wait for in-flight on shutdown."""
    controller = get_shutdown_drain(app)
    if controller is None:
        yield
        return
    restore = install_sigterm_drain_handler(controller)
    try:
        yield
    finally:
        controller.begin_drain()
        outcome = await asyncio.to_thread(controller.wait_for_idle)
        logger.info(
            "process_edge_shutdown_drain outcome=%s in_flight=%s timeout_s=%s",
            outcome.value,
            controller.in_flight,
            controller.drain_timeout_s,
        )
        restore()
