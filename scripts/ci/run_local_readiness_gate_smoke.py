#!/usr/bin/env python3
# scripts/ci/run_local_readiness_gate_smoke.py
#
# EPIC-08 P4/C11 — local smoke: serve readiness route, then run the deploy gate.
# Does not reimplement probes; uses register_readiness_route + check_readiness_gate.

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import uvicorn
from fastapi import FastAPI

from app.process_edge.asgi import register_readiness_route
from infrastructure.config.settings import Settings
from infrastructure.health.readiness_gate import check_readiness_gate


def _serve(settings: Settings) -> uvicorn.Server:
    api = FastAPI()
    register_readiness_route(
        api,
        settings=settings,
        llm_connectivity_check=lambda _s: None,
    )
    config = uvicorn.Config(
        api,
        host="127.0.0.1",
        port=8765,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10.0
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("local readiness server failed to start")
    return server


def main() -> int:
    settings = Settings(
        openai_api_key="sk-ci-sentinel",
        health_llm_probe_enabled=False,
        health_db_probe_enabled=False,
        health_sandbox_probe_enabled=True,
        readiness_gate_base_url="http://127.0.0.1:8765",
        readiness_gate_timeout_s=5.0,
    )
    server = _serve(settings)
    try:
        return check_readiness_gate(settings)
    finally:
        server.should_exit = True


if __name__ == "__main__":
    raise SystemExit(main())
