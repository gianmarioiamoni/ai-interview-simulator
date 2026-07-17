# tests/infrastructure/config/test_epic08_config_architecture.py
#
# EPIC-08 P1/C3 — architectural enforcement for Settings-exclusive runtime config.
# Freeze: CFG-01–CFG-05, IB-01, IB-02; OI-01 allowlist finalized here.

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# Approved non-production allowlist for direct os.environ / os.getenv (OI-01).
# Prefixes are relative to repo root. Do not expand without Freeze revision.
OS_ENVIRON_ALLOWLIST_PREFIXES: frozenset[str] = frozenset(
    {
        "tests/",
        "scripts/",
    }
)

# Sole production module permitted to bind HF platform env aliases (CFG-03/05).
HF_ENV_ALIAS_ALLOWED_RELATIVE = "infrastructure/config/settings.py"

HF_ENV_ALIAS_NAMES: frozenset[str] = frozenset(
    {
        "HF_TOKEN",
        "HUGGINGFACE_TOKEN",
    }
)

FORBIDDEN_HF_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "huggingface_hub",
        "huggingface",
        "gradio",
    }
)

DOMAIN_ROOT = REPO_ROOT / "domain"
LANGGRAPH_ROOT = REPO_ROOT / "app" / "graph"

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


def _iter_py_under(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        p
        for p in root.rglob("*.py")
        if not any(part in _SKIP_DIR_NAMES for part in p.relative_to(REPO_ROOT).parts)
    )


def _source_uses_os_environ_or_getenv(source: str) -> list[str]:
    """Return human-readable hits for os.environ / os.getenv usage."""
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


def _string_constants(source: str) -> set[str]:
    tree = ast.parse(source)
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.add(node.value)
    return values


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


class TestOsEnvironAllowlist:
    def test_allowlist_contains_only_tests_and_scripts(self) -> None:
        assert OS_ENVIRON_ALLOWLIST_PREFIXES == frozenset({"tests/", "scripts/"})

    def test_known_residual_reads_are_allowlisted(self) -> None:
        """Document intentional residuals (tooling / test harness only)."""
        known = (
            "tests/conftest.py",
            "scripts/upload_chroma_artifact.py",
            "scripts/question_intelligence/audit_question_reuse.py",
        )
        for relative in known:
            assert _is_allowlisted(relative), relative
            assert (REPO_ROOT / relative).is_file(), relative


class TestProductionOsEnvironBan:
    def test_no_unauthorized_production_os_environ_access(self) -> None:
        violations: list[str] = []
        for path in _iter_production_py_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            hits = _source_uses_os_environ_or_getenv(path.read_text(encoding="utf-8"))
            for hit in hits:
                violations.append(f"{relative}: {hit}")
        assert violations == [], (
            "CFG-02: production code must not access os.environ/getenv directly; "
            f"use Settings. Violations: {violations}"
        )

    def test_settings_module_does_not_use_os_environ(self) -> None:
        settings_path = REPO_ROOT / HF_ENV_ALIAS_ALLOWED_RELATIVE
        hits = _source_uses_os_environ_or_getenv(
            settings_path.read_text(encoding="utf-8")
        )
        assert hits == [], (
            "Settings must load env via pydantic-settings, not os.environ: "
            f"{hits}"
        )


class TestHfEnvAliasConfinement:
    def test_hf_env_aliases_only_in_settings(self) -> None:
        """CFG-03/05: HF token env aliases are Settings-only in production."""
        violations: list[str] = []
        for path in _iter_production_py_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative == HF_ENV_ALIAS_ALLOWED_RELATIVE:
                continue
            constants = _string_constants(path.read_text(encoding="utf-8"))
            leaked = sorted(HF_ENV_ALIAS_NAMES & constants)
            if leaked:
                violations.append(f"{relative}: {leaked}")
        assert violations == [], (
            "HF env aliases must remain confined to Settings: "
            f"{violations}"
        )

    def test_settings_declares_hf_env_aliases(self) -> None:
        settings_path = REPO_ROOT / HF_ENV_ALIAS_ALLOWED_RELATIVE
        constants = _string_constants(settings_path.read_text(encoding="utf-8"))
        missing = sorted(HF_ENV_ALIAS_NAMES - constants)
        assert missing == [], f"Settings missing HF env aliases: {missing}"


class TestHfImportConfinement:
    @pytest.mark.parametrize(
        "path",
        _iter_py_under(DOMAIN_ROOT),
        ids=lambda p: p.relative_to(REPO_ROOT).as_posix(),
    )
    def test_domain_has_no_hf_platform_imports(self, path: Path) -> None:
        roots = _imported_module_roots(path.read_text(encoding="utf-8"))
        forbidden = sorted(FORBIDDEN_HF_IMPORT_ROOTS & roots)
        assert forbidden == [], (
            f"IB-02: Domain must not import HF/deploy platform modules: "
            f"{path.relative_to(REPO_ROOT).as_posix()}: {forbidden}"
        )

    @pytest.mark.parametrize(
        "path",
        _iter_py_under(LANGGRAPH_ROOT),
        ids=lambda p: p.relative_to(REPO_ROOT).as_posix(),
    )
    def test_langgraph_has_no_hf_platform_imports(self, path: Path) -> None:
        roots = _imported_module_roots(path.read_text(encoding="utf-8"))
        forbidden = sorted(FORBIDDEN_HF_IMPORT_ROOTS & roots)
        assert forbidden == [], (
            f"IB-02: LangGraph must not import HF/deploy platform modules: "
            f"{path.relative_to(REPO_ROOT).as_posix()}: {forbidden}"
        )
