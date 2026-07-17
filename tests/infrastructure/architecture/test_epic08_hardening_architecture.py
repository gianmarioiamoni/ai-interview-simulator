# tests/infrastructure/architecture/test_epic08_hardening_architecture.py
#
# EPIC-08 P7/C16 — architectural hardening (Freeze §13 structural items).
# Enforces: HF confinement (O-01), telemetry single path (AR-07 / IB-04),
# health side-effect-free (HLT-* / rejects AR-09), config ban (CFG-01–05).

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

OS_ENVIRON_ALLOWLIST_PREFIXES: frozenset[str] = frozenset({"tests/", "scripts/"})

FORBIDDEN_HF_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "huggingface_hub",
        "huggingface",
        "gradio",
    }
)

HF_ENV_ALIAS_NAMES: frozenset[str] = frozenset({"HF_TOKEN", "HUGGINGFACE_TOKEN"})

SETTINGS_RELATIVE = "infrastructure/config/settings.py"
SOLE_LLM_METRIC_WRITER = (
    "infrastructure/llm/observability/observing_llm_adapter.py"
)
LLM_LOG_BRIDGE = "infrastructure/llm/observability/llm_structured_log_bridge.py"
HEALTH_ROOT = REPO_ROOT / "infrastructure" / "health"

# O-01 surfaces: Domain, LangGraph, InterviewState, frozen contracts.
O01_ROOTS: tuple[str, ...] = (
    "domain",
    "domain/contracts",
    "domain/contracts/interview_state",
    "app/graph",
)

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
    }
)


def _is_allowlisted(relative_posix: str) -> bool:
    return any(
        relative_posix == prefix.rstrip("/") or relative_posix.startswith(prefix)
        for prefix in OS_ENVIRON_ALLOWLIST_PREFIXES
    )


def _iter_production_py_files() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*.py"):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if any(part in _SKIP_DIR_NAMES for part in path.relative_to(REPO_ROOT).parts):
            continue
        if _is_allowlisted(relative):
            continue
        files.append(path)
    return sorted(files)


def _iter_py_under(relative_root: str) -> list[Path]:
    root = REPO_ROOT / relative_root
    if not root.is_dir():
        return []
    return sorted(
        p
        for p in root.rglob("*.py")
        if not any(part in _SKIP_DIR_NAMES for part in p.relative_to(REPO_ROOT).parts)
    )


def _source_uses_os_environ_or_getenv(source: str) -> list[str]:
    tree = ast.parse(source)
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if not isinstance(node.value, ast.Name) or node.value.id != "os":
            continue
        if node.attr in {"environ", "getenv"}:
            hits.append(f"os.{node.attr}")
    return hits


def _imported_module_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _string_constants(source: str) -> set[str]:
    tree = ast.parse(source)
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _calls_named(source: str, name: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == name:
            return True
        if isinstance(func, ast.Attribute) and func.attr == name:
            return True
    return False


class TestConfigBanHardening:
    """Freeze §13 / CFG-01–05: Settings exclusive; no production os.environ."""

    def test_no_unauthorized_production_os_environ_access(self) -> None:
        violations: list[str] = []
        for path in _iter_production_py_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            hits = _source_uses_os_environ_or_getenv(path.read_text(encoding="utf-8"))
            for hit in hits:
                violations.append(f"{relative}: {hit}")
        assert violations == [], (
            "CFG-02: production must use Settings, not os.environ/getenv: "
            f"{violations}"
        )

    def test_settings_remains_exclusive_env_entry(self) -> None:
        settings_path = REPO_ROOT / SETTINGS_RELATIVE
        assert settings_path.is_file()
        hits = _source_uses_os_environ_or_getenv(
            settings_path.read_text(encoding="utf-8")
        )
        assert hits == [], f"Settings must not use os.environ/getenv: {hits}"


class TestHfConfinementHardening:
    """Freeze §13 / IB-02 / O-01: zero HF leakage into Domain/graph/state/contracts."""

    @pytest.mark.parametrize("root_rel", O01_ROOTS)
    def test_o01_surfaces_have_no_hf_platform_imports(self, root_rel: str) -> None:
        violations: list[str] = []
        for path in _iter_py_under(root_rel):
            relative = path.relative_to(REPO_ROOT).as_posix()
            forbidden = sorted(
                FORBIDDEN_HF_IMPORT_ROOTS
                & _imported_module_roots(path.read_text(encoding="utf-8"))
            )
            if forbidden:
                violations.append(f"{relative}: {forbidden}")
        assert violations == [], (
            "O-01 / IB-02: HF/deploy platform imports forbidden: "
            f"{violations}"
        )

    @pytest.mark.parametrize("root_rel", O01_ROOTS)
    def test_o01_surfaces_have_no_hf_env_aliases(self, root_rel: str) -> None:
        violations: list[str] = []
        for path in _iter_py_under(root_rel):
            relative = path.relative_to(REPO_ROOT).as_posix()
            leaked = sorted(
                HF_ENV_ALIAS_NAMES & _string_constants(path.read_text(encoding="utf-8"))
            )
            if leaked:
                violations.append(f"{relative}: {leaked}")
        assert violations == [], (
            "O-01: HF env aliases must not appear outside Settings: "
            f"{violations}"
        )


class TestTelemetrySinglePathHardening:
    """AR-07 / IB-04 / rejects AR-06: sole LLM metric + structured-log bridge path."""

    def test_sole_production_llm_call_metric_constructor(self) -> None:
        violations: list[str] = []
        for path in _iter_production_py_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative == SOLE_LLM_METRIC_WRITER:
                continue
            if _calls_named(path.read_text(encoding="utf-8"), "LLMCallMetric"):
                violations.append(relative)
        assert violations == [], (
            "AR-07: only ObservingLLMAdapter may construct LLMCallMetric: "
            f"{violations}"
        )

    def test_sole_production_emit_llm_call_structured_log_caller(self) -> None:
        allowed = {SOLE_LLM_METRIC_WRITER, LLM_LOG_BRIDGE}
        violations: list[str] = []
        for path in _iter_production_py_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative in allowed:
                continue
            if "emit_llm_call_structured_log" in path.read_text(encoding="utf-8"):
                violations.append(relative)
        assert violations == [], (
            "AR-07 / IB-04: dual LLM structured-log path forbidden: "
            f"{violations}"
        )

    def test_domain_and_graph_do_not_import_llm_observability(self) -> None:
        forbidden_tokens = (
            "ObservingLLMAdapter",
            "emit_llm_call_structured_log",
            "InterviewMetricsCollector",
        )
        violations: list[str] = []
        for root_rel in ("domain", "app/graph"):
            for path in _iter_py_under(root_rel):
                relative = path.relative_to(REPO_ROOT).as_posix()
                source = path.read_text(encoding="utf-8")
                hits = [token for token in forbidden_tokens if token in source]
                if hits:
                    violations.append(f"{relative}: {hits}")
        assert violations == [], (
            "IB-04: Domain/LangGraph must not own LLM telemetry: "
            f"{violations}"
        )


class TestHealthSideEffectFreeHardening:
    """HLT-* / rejects AR-09: readiness probes stay side-effect-free."""

    def test_health_modules_avoid_graph_session_and_observing_llm(self) -> None:
        forbidden_tokens = (
            "langgraph",
            "InterviewState",
            "ObservingLLMAdapter",
            "interview_graph",
            "build_interview_graph",
            "session_repository",
        )
        violations: list[str] = []
        for path in HEALTH_ROOT.rglob("*.py"):
            relative = path.relative_to(REPO_ROOT).as_posix()
            source = path.read_text(encoding="utf-8")
            hits = [token for token in forbidden_tokens if token in source]
            if hits:
                violations.append(f"{relative}: {hits}")
        assert violations == [], (
            "HLT / AR-09: health must not invoke graph/session LLM cycles: "
            f"{violations}"
        )

    def test_database_probe_is_read_only_uri(self) -> None:
        probes = (HEALTH_ROOT / "probes.py").read_text(encoding="utf-8")
        assert "mode=ro" in probes
        assert "CREATE TABLE" not in probes
        assert "INSERT INTO" not in probes
        assert "UPDATE " not in probes.upper()
        assert "DELETE " not in probes.upper()

    def test_health_does_not_import_forbidden_roots(self) -> None:
        forbidden_roots = {"langgraph", "gradio", "huggingface_hub", "huggingface"}
        violations: list[str] = []
        for path in HEALTH_ROOT.rglob("*.py"):
            relative = path.relative_to(REPO_ROOT).as_posix()
            roots = _imported_module_roots(path.read_text(encoding="utf-8"))
            leaked = sorted(forbidden_roots & roots)
            if leaked:
                violations.append(f"{relative}: {leaked}")
        assert violations == [], f"Health import confinement failed: {violations}"
