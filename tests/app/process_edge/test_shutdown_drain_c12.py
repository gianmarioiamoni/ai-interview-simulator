# tests/app/process_edge/test_shutdown_drain_c12.py
#
# EPIC-08 P5/C12 — process-edge SIGTERM drain (SDN-01, SDN-02).

from __future__ import annotations

import signal
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.process_edge.asgi import build_process_asgi_app, run_process_app
from app.process_edge.shutdown import (
    DrainMiddleware,
    DrainOutcome,
    ShutdownDrainController,
    get_shutdown_drain,
    install_sigterm_drain_handler,
)
from infrastructure.config.settings import Settings

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GRAPH_DIR = _REPO_ROOT / "app" / "graph"


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "openai_api_key": "sk-test-key",
        "shutdown_drain_timeout_s": 2,
    }
    base.update(overrides)
    return Settings(**base)


def _draining_app(controller: ShutdownDrainController) -> TestClient:
    api = FastAPI()

    @api.get("/work")
    def work() -> dict[str, str]:
        return {"status": "ok"}

    wrapped = DrainMiddleware(api, controller)
    return TestClient(wrapped)


class TestShutdownDrainController:
    def test_begin_drain_stops_admit(self) -> None:
        ctl = ShutdownDrainController(drain_timeout_s=1)
        assert ctl.try_admit() is True
        ctl.release()
        ctl.begin_drain()
        assert ctl.is_draining is True
        assert ctl.try_admit() is False

    def test_in_flight_completes_during_drain(self) -> None:
        ctl = ShutdownDrainController(drain_timeout_s=2)
        assert ctl.try_admit() is True
        ctl.begin_drain()
        assert ctl.in_flight == 1
        assert ctl.try_admit() is False

        def _finish() -> None:
            time.sleep(0.05)
            ctl.release()

        threading.Thread(target=_finish, daemon=True).start()
        outcome = ctl.wait_for_idle()
        assert outcome is DrainOutcome.CLEAN
        assert ctl.last_outcome is DrainOutcome.CLEAN
        assert ctl.in_flight == 0

    def test_drain_timeout_is_observable(self) -> None:
        ctl = ShutdownDrainController(drain_timeout_s=0.05)
        assert ctl.try_admit() is True
        ctl.begin_drain()
        outcome = ctl.wait_for_idle()
        assert outcome is DrainOutcome.TIMEOUT
        assert ctl.last_outcome is DrainOutcome.TIMEOUT
        assert ctl.in_flight == 1
        ctl.release()

    def test_settings_timeout_used(self) -> None:
        settings = _settings(shutdown_drain_timeout_s=45)
        ctl = ShutdownDrainController(settings.shutdown_drain_timeout_s)
        assert ctl.drain_timeout_s == 45.0


class TestDrainMiddlewareHttp:
    def test_normal_execution_admits_requests(self) -> None:
        ctl = ShutdownDrainController(drain_timeout_s=1)
        client = _draining_app(ctl)
        response = client.get("/work")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert ctl.in_flight == 0
        assert ctl.is_draining is False

    def test_sigterm_drain_rejects_new_requests(self) -> None:
        ctl = ShutdownDrainController(drain_timeout_s=1)
        client = _draining_app(ctl)
        ctl.begin_drain()
        response = client.get("/work")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "draining"
        assert ctl.in_flight == 0

    def test_in_flight_survives_drain_start_until_release(self) -> None:
        ctl = ShutdownDrainController(drain_timeout_s=2)
        client = _draining_app(ctl)
        assert ctl.try_admit() is True
        ctl.begin_drain()
        rejected = client.get("/work")
        assert rejected.status_code == 503
        assert ctl.in_flight == 1
        ctl.release()
        assert ctl.wait_for_idle(timeout_s=0.5) is DrainOutcome.CLEAN


class TestSigtermHandler:
    def test_sigterm_handler_starts_drain(self) -> None:
        ctl = ShutdownDrainController(drain_timeout_s=1)
        restore = install_sigterm_drain_handler(ctl)
        try:
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
            assert ctl.is_draining is True
        finally:
            restore()


class TestProcessEdgeWiring:
    def test_build_attaches_drain_from_settings(self) -> None:
        settings = _settings(shutdown_drain_timeout_s=17)
        blocks = MagicMock()
        import app.process_edge.asgi as asgi_module

        original = asgi_module.mount_gradio_app

        def _fake_mount(api: FastAPI, _blocks: object, path: str = "/") -> FastAPI:
            assert path == "/"
            return api

        asgi_module.mount_gradio_app = _fake_mount  # type: ignore[assignment]
        try:
            app = build_process_asgi_app(blocks, settings=settings)
        finally:
            asgi_module.mount_gradio_app = original  # type: ignore[assignment]

        assert isinstance(app, DrainMiddleware)
        ctl = get_shutdown_drain(app)
        assert ctl is not None
        assert ctl.drain_timeout_s == 17.0

    def test_run_process_app_passes_graceful_timeout(self) -> None:
        settings = _settings(shutdown_drain_timeout_s=12)
        ctl = ShutdownDrainController(settings.shutdown_drain_timeout_s)
        api = FastAPI()
        app = DrainMiddleware(api, ctl)
        captured: dict[str, object] = {}

        def _fake_run(asgi_app: object, **kwargs: object) -> None:
            captured["app"] = asgi_app
            captured.update(kwargs)

        run_process_app(
            app,
            host="127.0.0.1",
            port=9,
            settings=settings,
            uvicorn_run=_fake_run,
        )
        assert captured["timeout_graceful_shutdown"] == 12
        assert captured["host"] == "127.0.0.1"
        assert captured["port"] == 9

    def test_c12_adds_no_graph_modules(self) -> None:
        """C12 must not introduce LangGraph topology modules (SDN-03 light gate)."""
        shutdown_paths = list((_REPO_ROOT / "app" / "process_edge").glob("*.py"))
        assert any(p.name == "shutdown.py" for p in shutdown_paths)
        graph_py = sorted(p.name for p in _GRAPH_DIR.rglob("*.py") if p.is_file())
        assert "shutdown.py" not in graph_py
        assert "drain.py" not in graph_py
