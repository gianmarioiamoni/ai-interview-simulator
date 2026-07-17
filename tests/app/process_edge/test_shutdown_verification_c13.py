# tests/app/process_edge/test_shutdown_verification_c13.py
#
# EPIC-08 P5/C13 — shutdown verification + ops-edge regression (SDN-01–SDN-04).
# Proves drain behaviour at process edge; no new production shutdown features.

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.process_edge.asgi import register_readiness_route
from app.process_edge.shutdown import (
    DrainMiddleware,
    DrainOutcome,
    ShutdownDrainController,
    get_shutdown_drain,
    process_edge_lifespan,
)
from infrastructure.config.settings import Settings
from infrastructure.health.http import READINESS_PATH

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESS_EDGE_ROOT = REPO_ROOT / "app" / "process_edge"
DOMAIN_ROOT = REPO_ROOT / "domain"
GRAPH_ROOT = REPO_ROOT / "app" / "graph"

_SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "node_modules",
        ".ruff_cache",
        "tests",
        "scripts",
        "docs",
    }
)

_LIFECYCLE_SYMBOLS: frozenset[str] = frozenset(
    {
        "ShutdownDrainController",
        "DrainMiddleware",
        "install_sigterm_drain_handler",
        "process_edge_lifespan",
    }
)


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "openai_api_key": "sk-test-key",
        "shutdown_drain_timeout_s": 1,
        "health_llm_probe_enabled": False,
        "health_db_probe_enabled": False,
        "health_sandbox_probe_enabled": True,
    }
    base.update(overrides)
    return Settings(**base)


def _iter_production_py() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*.py"):
        parts = path.relative_to(REPO_ROOT).parts
        if any(part in _SKIP_DIR_NAMES for part in parts):
            continue
        files.append(path)
    return sorted(files)


def _imported_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


class TestOpsEdgeDrainRegression:
    def test_readiness_admitted_when_not_draining(self) -> None:
        settings = _settings()
        ctl = ShutdownDrainController(settings.shutdown_drain_timeout_s)
        api = FastAPI()
        register_readiness_route(
            api,
            settings=settings,
            llm_connectivity_check=lambda _s: None,
        )
        client = TestClient(DrainMiddleware(api, ctl))
        response = client.get(READINESS_PATH)
        assert response.status_code == 200
        assert response.json()["ready"] is True
        assert ctl.is_draining is False

    def test_drain_rejects_readiness_and_keeps_in_flight_path(self) -> None:
        settings = _settings()
        ctl = ShutdownDrainController(settings.shutdown_drain_timeout_s)
        api = FastAPI()
        register_readiness_route(
            api,
            settings=settings,
            llm_connectivity_check=lambda _s: None,
        )
        client = TestClient(DrainMiddleware(api, ctl))
        assert ctl.try_admit() is True
        ctl.begin_drain()
        rejected = client.get(READINESS_PATH)
        assert rejected.status_code == 503
        assert rejected.json()["status"] == "draining"
        assert ctl.in_flight == 1
        ctl.release()
        assert ctl.wait_for_idle(timeout_s=0.5) is DrainOutcome.CLEAN

    def test_lifespan_waits_and_records_clean_outcome(self) -> None:
        settings = _settings(shutdown_drain_timeout_s=1)
        ctl = ShutdownDrainController(settings.shutdown_drain_timeout_s)
        api = FastAPI(lifespan=process_edge_lifespan)
        api.state.shutdown_drain = ctl

        async def _run() -> DrainOutcome | None:
            async with process_edge_lifespan(api):
                assert ctl.is_draining is False
            assert ctl.is_draining is True
            return ctl.last_outcome

        outcome = asyncio.run(_run())
        assert outcome is DrainOutcome.CLEAN
        assert get_shutdown_drain(api) is ctl


class TestShutdownConfinement:
    def test_lifecycle_symbols_only_under_process_edge(self) -> None:
        allowed_prefix = "app/process_edge/"
        violators: list[str] = []
        for path in _iter_production_py():
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel.startswith(allowed_prefix):
                continue
            imported = _imported_names(path.read_text(encoding="utf-8"))
            hits = sorted(_LIFECYCLE_SYMBOLS & imported)
            if hits:
                violators.append(f"{rel}: {', '.join(hits)}")
        assert violators == []

    def test_domain_and_graph_do_not_import_process_edge_shutdown(self) -> None:
        violators: list[str] = []
        for root in (DOMAIN_ROOT, GRAPH_ROOT):
            for path in root.rglob("*.py"):
                source = path.read_text(encoding="utf-8")
                if "app.process_edge" in source or "process_edge.shutdown" in source:
                    violators.append(path.relative_to(REPO_ROOT).as_posix())
        assert violators == []

    def test_process_edge_owns_shutdown_module(self) -> None:
        assert (PROCESS_EDGE_ROOT / "shutdown.py").is_file()
        source = (PROCESS_EDGE_ROOT / "shutdown.py").read_text(encoding="utf-8")
        assert "ShutdownDrainController" in source
        assert "SIGTERM" in source
