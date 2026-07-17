# app/process_edge/asgi.py
#
# EPIC-08 P4/C10 — process-edge ASGI app: GET /health/ready + Gradio UI mount.
# EPIC-08 P5/C12 — SIGTERM drain middleware + Settings-driven graceful timeout.
# Readiness evaluation is delegated entirely to infrastructure.health (C9).

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from gradio import Blocks, mount_gradio_app

from app.process_edge.shutdown import (
    DrainMiddleware,
    ShutdownDrainController,
    get_shutdown_drain,
    process_edge_lifespan,
)
from infrastructure.config.settings import Settings, settings as default_settings
from infrastructure.health.http import (
    READINESS_PATH,
    readiness_response_body,
    readiness_status_code,
)
from infrastructure.health.probes import LLMConnectivityCheck
from infrastructure.health.readiness import evaluate_readiness


def register_readiness_route(
    api: FastAPI,
    *,
    settings: Settings | None = None,
    llm_connectivity_check: LLMConnectivityCheck | None = None,
) -> None:
    """Attach GET /health/ready; thin HTTP adapter over evaluate_readiness."""

    @api.get(READINESS_PATH)
    def health_ready() -> JSONResponse:
        report = evaluate_readiness(
            settings,
            llm_connectivity_check=llm_connectivity_check,
        )
        return JSONResponse(
            content=readiness_response_body(report),
            status_code=readiness_status_code(report),
        )


def build_process_asgi_app(
    gradio_blocks: Blocks,
    *,
    settings: Settings | None = None,
    llm_connectivity_check: LLMConnectivityCheck | None = None,
    drain_controller: ShutdownDrainController | None = None,
) -> Any:
    """Compose process-edge FastAPI with readiness, Gradio, and drain middleware."""
    resolved = settings if settings is not None else default_settings
    controller = drain_controller or ShutdownDrainController(
        resolved.shutdown_drain_timeout_s
    )
    api = FastAPI(lifespan=process_edge_lifespan)
    api.state.shutdown_drain = controller
    register_readiness_route(
        api,
        settings=settings,
        llm_connectivity_check=llm_connectivity_check,
    )
    mounted = mount_gradio_app(api, gradio_blocks, path="/")
    return DrainMiddleware(mounted, controller)


def run_process_app(
    asgi_app: Any,
    *,
    host: str | None = None,
    port: int | None = None,
    settings: Settings | None = None,
    uvicorn_run: Callable[..., Any] | None = None,
) -> None:
    """Run the process-edge ASGI app (Settings-driven host/port/drain timeout)."""
    resolved = settings if settings is not None else default_settings
    server_host = host if host is not None else resolved.server_host
    server_port = port if port is not None else resolved.server_port
    controller = get_shutdown_drain(asgi_app)
    if controller is None:
        controller = ShutdownDrainController(resolved.shutdown_drain_timeout_s)
        asgi_app = DrainMiddleware(asgi_app, controller)

    drain_timeout = int(controller.drain_timeout_s)
    runner = uvicorn_run
    if runner is None:
        import uvicorn

        runner = uvicorn.run
    runner(
        asgi_app,
        host=server_host,
        port=server_port,
        timeout_graceful_shutdown=drain_timeout,
    )
