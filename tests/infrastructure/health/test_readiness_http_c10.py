# tests/infrastructure/health/test_readiness_http_c10.py
#
# EPIC-08 P4/C10 — GET /health/ready process-edge exposure.

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.process_edge.asgi import register_readiness_route
from infrastructure.config.settings import Settings
from infrastructure.health.http import (
    READINESS_PATH,
    readiness_response_body,
    readiness_status_code,
)
from infrastructure.health.readiness import evaluate_readiness
from infrastructure.health.types import ProbeResult, ReadinessReport


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "openai_api_key": "sk-test-key",
        "health_probe_timeout_ms": 1000,
        "health_llm_probe_enabled": True,
        "health_db_probe_enabled": True,
        "health_sandbox_probe_enabled": True,
        "sqlite_db_path": "data/questions.db",
    }
    base.update(overrides)
    return Settings(**base)


def _client(
    *,
    settings: Settings,
    llm_connectivity_check=None,
) -> TestClient:
    api = FastAPI()
    register_readiness_route(
        api,
        settings=settings,
        llm_connectivity_check=llm_connectivity_check,
    )
    return TestClient(api)


class TestHttpHelpers:
    def test_status_codes(self) -> None:
        ready = ReadinessReport(ready=True, probes=())
        not_ready = ReadinessReport(ready=False, probes=())
        assert readiness_status_code(ready) == 200
        assert readiness_status_code(not_ready) == 503

    def test_payload_shape(self) -> None:
        report = ReadinessReport(
            ready=False,
            probes=(
                ProbeResult(
                    name="database",
                    status="failure",
                    detail="missing",
                    error_type="FileNotFoundError",
                    duration_ms=1.5,
                ),
            ),
        )
        body = readiness_response_body(report)
        assert body["ready"] is False
        assert body["probes"][0]["name"] == "database"
        assert body["probes"][0]["status"] == "failure"
        assert body["probes"][0]["error_type"] == "FileNotFoundError"


class TestHealthReadyEndpoint:
    def test_ready_returns_200_and_payload(self, tmp_path: Path) -> None:
        db_path = tmp_path / "ok.db"
        sqlite3.connect(db_path).close()
        client = _client(
            settings=_settings(sqlite_db_path=str(db_path)),
            llm_connectivity_check=lambda _s: None,
        )
        response = client.get(READINESS_PATH)
        assert response.status_code == 200
        payload = response.json()
        assert payload["ready"] is True
        assert {p["name"] for p in payload["probes"]} == {
            "llm",
            "database",
            "sandbox",
        }
        assert all(p["status"] == "success" for p in payload["probes"])

    def test_not_ready_returns_503(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.db"
        client = _client(
            settings=_settings(sqlite_db_path=str(missing)),
            llm_connectivity_check=lambda _s: None,
        )
        response = client.get(READINESS_PATH)
        assert response.status_code == 503
        payload = response.json()
        assert payload["ready"] is False
        db_probe = next(p for p in payload["probes"] if p["name"] == "database")
        assert db_probe["status"] == "failure"

    def test_delegates_to_evaluate_readiness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "ok.db"
        sqlite3.connect(db_path).close()
        settings = _settings(sqlite_db_path=str(db_path))
        api = FastAPI()
        register_readiness_route(
            api,
            settings=settings,
            llm_connectivity_check=lambda _s: None,
        )
        with patch(
            "app.process_edge.asgi.evaluate_readiness",
            wraps=evaluate_readiness,
        ) as mocked:
            client = TestClient(api)
            client.get(READINESS_PATH)
        mocked.assert_called_once()

    def test_path_is_health_ready(self) -> None:
        assert READINESS_PATH == "/health/ready"


class TestNoDuplicatedLogic:
    def test_http_module_does_not_reimplement_probes(self) -> None:
        source = Path(
            "infrastructure/health/http.py"
        ).read_text(encoding="utf-8")
        assert "sqlite3" not in source
        assert "OpenAI" not in source
        assert "evaluate_readiness" not in source
