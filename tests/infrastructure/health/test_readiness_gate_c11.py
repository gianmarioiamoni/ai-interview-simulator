# tests/infrastructure/health/test_readiness_gate_c11.py
#
# EPIC-08 P4/C11 — CI/deploy readiness gate consumes GET /health/ready only.

from __future__ import annotations

import io
import json
from pathlib import Path
from infrastructure.config.settings import Settings
from infrastructure.health.http import READINESS_PATH
from infrastructure.health.readiness_gate import (
    build_readiness_gate_url,
    check_readiness_gate,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
GATE_MODULE = REPO_ROOT / "infrastructure" / "health" / "readiness_gate.py"
GATE_SCRIPT = REPO_ROOT / "scripts" / "ci" / "check_readiness_gate.py"


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "openai_api_key": "sk-test-key",
        "readiness_gate_base_url": "http://127.0.0.1:7860",
        "readiness_gate_timeout_s": 2.0,
    }
    base.update(overrides)
    return Settings(**base)


class _FakeResponse:
    def __init__(self, status: int, payload: dict[str, object]) -> None:
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class TestReadinessGateUrl:
    def test_uses_central_readiness_path(self) -> None:
        url = build_readiness_gate_url(_settings())
        assert url.endswith(READINESS_PATH)
        assert url == "http://127.0.0.1:7860/health/ready"

    def test_strips_trailing_slash_on_base(self) -> None:
        url = build_readiness_gate_url(
            _settings(readiness_gate_base_url="http://example.test:9000/")
        )
        assert url == "http://example.test:9000/health/ready"


class TestCheckReadinessGate:
    def test_exit_0_when_http_200_and_ready_true(self) -> None:
        seen: dict[str, object] = {}

        def _urlopen(request: object, timeout: float = 0) -> _FakeResponse:
            seen["timeout"] = timeout
            seen["url"] = getattr(request, "full_url", None)
            return _FakeResponse(200, {"ready": True, "probes": []})

        code = check_readiness_gate(_settings(), urlopen=_urlopen)
        assert code == 0
        assert seen["timeout"] == 2.0
        assert seen["url"] == "http://127.0.0.1:7860/health/ready"

    def test_exit_1_when_ready_false_on_200(self) -> None:
        def _urlopen(request: object, timeout: float = 0) -> _FakeResponse:
            return _FakeResponse(200, {"ready": False, "probes": []})

        assert check_readiness_gate(_settings(), urlopen=_urlopen) == 1

    def test_exit_1_on_http_503(self) -> None:
        import urllib.error

        def _urlopen(request: object, timeout: float = 0) -> _FakeResponse:
            raise urllib.error.HTTPError(
                url="http://127.0.0.1:7860/health/ready",
                code=503,
                msg="Service Unavailable",
                hdrs=None,
                fp=io.BytesIO(
                    json.dumps({"ready": False, "probes": []}).encode("utf-8")
                ),
            )

        assert check_readiness_gate(_settings(), urlopen=_urlopen) == 1

    def test_exit_1_on_transport_error(self) -> None:
        def _urlopen(request: object, timeout: float = 0) -> _FakeResponse:
            raise TimeoutError("connection timed out")

        assert check_readiness_gate(_settings(), urlopen=_urlopen) == 1


class TestGateDoesNotReimplementProbes:
    def test_gate_module_has_no_probe_imports(self) -> None:
        source = GATE_MODULE.read_text(encoding="utf-8")
        assert "probe_llm" not in source
        assert "probe_database" not in source
        assert "probe_sandbox" not in source
        assert "evaluate_readiness" not in source
        assert "sqlite3" not in source
        assert "OpenAI" not in source
        assert "READINESS_PATH" in source

    def test_cli_script_delegates_to_gate_module(self) -> None:
        source = GATE_SCRIPT.read_text(encoding="utf-8")
        assert "from infrastructure.health.readiness_gate import main" in source
        assert "probe_" not in source
