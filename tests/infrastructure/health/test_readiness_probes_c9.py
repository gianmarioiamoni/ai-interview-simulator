# tests/infrastructure/health/test_readiness_probes_c9.py
#
# EPIC-08 P4/C9 — side-effect-free readiness probes (HLT-01–HLT-05).

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from infrastructure.config.settings import Settings
from infrastructure.health.probes import probe_database, probe_llm, probe_sandbox
from infrastructure.health.readiness import evaluate_readiness

REPO_ROOT = Path(__file__).resolve().parents[3]
HEALTH_ROOT = REPO_ROOT / "infrastructure" / "health"


def _settings(**overrides: object) -> Settings:
    base = {
        "openai_api_key": "sk-test-key",
        "health_probe_timeout_ms": 1000,
        "health_llm_probe_enabled": True,
        "health_db_probe_enabled": True,
        "health_sandbox_probe_enabled": True,
        "sqlite_db_path": "data/questions.db",
    }
    base.update(overrides)
    return Settings(**base)


class TestProbeDatabase:
    def test_success_read_only(self, tmp_path: Path) -> None:
        db_path = tmp_path / "ready.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        conn.close()

        result = probe_database(_settings(sqlite_db_path=str(db_path)))
        assert result.name == "database"
        assert result.status == "success"
        assert result.duration_ms >= 0

    def test_failure_when_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "absent" / "missing.db"
        result = probe_database(_settings(sqlite_db_path=str(missing)))
        assert result.status == "failure"
        assert result.error_type == "FileNotFoundError"
        assert not missing.exists()
        assert not missing.parent.exists()

    def test_does_not_mutate_database(self, tmp_path: Path) -> None:
        db_path = tmp_path / "immutable.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO t(id) VALUES (1)")
        conn.commit()
        conn.close()

        before = db_path.read_bytes()
        probe_database(_settings(sqlite_db_path=str(db_path)))
        after = db_path.read_bytes()
        assert after == before

        verify = sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)
        try:
            rows = verify.execute("SELECT id FROM t").fetchall()
        finally:
            verify.close()
        assert rows == [(1,)]

    def test_skipped_when_disabled(self) -> None:
        result = probe_database(_settings(health_db_probe_enabled=False))
        assert result.status == "skipped"


class TestProbeLlm:
    def test_success_uses_injected_connectivity_check(self) -> None:
        called: list[str] = []

        def _check(settings: Settings) -> None:
            called.append(settings.openai_api_key)

        result = probe_llm(_settings(), connectivity_check=_check)
        assert result.status == "success"
        assert called == ["sk-test-key"]

    def test_failure_surfaces_error_type(self) -> None:
        def _check(_settings: Settings) -> None:
            raise TimeoutError("llm unreachable")

        result = probe_llm(_settings(), connectivity_check=_check)
        assert result.status == "failure"
        assert result.error_type == "TimeoutError"

    def test_default_check_does_not_call_chat_completions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        models = MagicMock()
        models.list.return_value = iter([MagicMock(id="gpt-4o-mini")])
        client = MagicMock()
        client.models = models
        client.chat = MagicMock()

        openai_mod = MagicMock()
        openai_mod.OpenAI.return_value = client
        monkeypatch.setitem(__import__("sys").modules, "openai", openai_mod)

        from infrastructure.health import probes as probes_module

        probes_module._default_llm_connectivity_check(_settings())
        models.list.assert_called_once()
        client.chat.completions.create.assert_not_called()

    def test_skipped_when_disabled(self) -> None:
        result = probe_llm(
            _settings(health_llm_probe_enabled=False),
            connectivity_check=lambda _s: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert result.status == "skipped"


class TestProbeSandbox:
    def test_success(self) -> None:
        result = probe_sandbox(_settings())
        assert result.status == "success"
        assert result.duration_ms >= 0

    def test_failure_when_python_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "infrastructure.health.probes.sys.executable",
            "/nonexistent/python-binary",
        )
        result = probe_sandbox(_settings())
        assert result.status == "failure"
        assert result.error_type == "RuntimeError"

    def test_skipped_when_disabled(self) -> None:
        result = probe_sandbox(_settings(health_sandbox_probe_enabled=False))
        assert result.status == "skipped"


class TestEvaluateReadiness:
    def test_ready_when_all_enabled_probes_succeed(self, tmp_path: Path) -> None:
        db_path = tmp_path / "ok.db"
        sqlite3.connect(db_path).close()
        report = evaluate_readiness(
            _settings(sqlite_db_path=str(db_path)),
            llm_connectivity_check=lambda _s: None,
        )
        assert report.ready is True
        assert {p.name for p in report.probes} == {"llm", "database", "sandbox"}
        assert all(p.status == "success" for p in report.probes)

    def test_not_ready_when_any_enabled_probe_fails(self, tmp_path: Path) -> None:
        missing = tmp_path / "gone.db"
        report = evaluate_readiness(
            _settings(sqlite_db_path=str(missing)),
            llm_connectivity_check=lambda _s: None,
        )
        assert report.ready is False
        assert report.probe_by_name("database") is not None
        assert report.probe_by_name("database").status == "failure"

    def test_skipped_probes_do_not_fail_aggregate(self) -> None:
        report = evaluate_readiness(
            _settings(
                health_llm_probe_enabled=False,
                health_db_probe_enabled=False,
                health_sandbox_probe_enabled=False,
            )
        )
        assert report.ready is True
        assert all(p.status == "skipped" for p in report.probes)


class TestSideEffectArchitecture:
    def test_health_modules_do_not_import_langgraph_or_interview_state(self) -> None:
        forbidden_roots = {"langgraph", "InterviewState"}
        for path in HEALTH_ROOT.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] not in {"langgraph"}
                if isinstance(node, ast.ImportFrom) and node.module:
                    root = node.module.split(".")[0]
                    assert root != "langgraph"
                    for alias in node.names:
                        assert alias.name not in forbidden_roots

    def test_health_modules_do_not_import_observing_llm_adapter(self) -> None:
        for path in HEALTH_ROOT.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "ObservingLLMAdapter" not in source
            assert "interview_graph" not in source
