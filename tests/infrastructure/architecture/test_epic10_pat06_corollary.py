# tests/infrastructure/architecture/test_epic10_pat06_corollary.py
#
# EPIC-10 Macro D / P5 — AT-03 PAT-06 corollary allowlist + forbidden-pattern scan.
# Governing: Freeze AR-05, AR-10 / AT-03; Discovery §6.

from __future__ import annotations

import re
from pathlib import Path

from tests.infrastructure.architecture.epic10_pat06_allowlist import (
    PAT06_COROLLARY_ALLOWLIST,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_ROOT = REPO_ROOT / "services"

_SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)

# Forbidden workflow-routing indicators inside services/ (AR-05 Violation class).
FORBIDDEN_WORKFLOW_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ActionType.NEXT|RETRY|GENERATE_REPORT",
        re.compile(r"\bActionType\.(NEXT|RETRY|GENERATE_REPORT)\b"),
    ),
    (
        "langgraph import/usage",
        re.compile(r"\blanggraph\b"),
    ),
    (
        "StateGraph",
        re.compile(r"\bStateGraph\b"),
    ),
    (
        "add_conditional_edges",
        re.compile(r"\badd_conditional_edges\b"),
    ),
)


def _iter_services_py_files() -> list[Path]:
    files: list[Path] = []
    for path in SERVICES_ROOT.rglob("*.py"):
        if any(part in _SKIP_DIR_NAMES for part in path.relative_to(REPO_ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


class TestAT03Pat06Corollary:
    """AT-03 — services must not implement interview workflow routing."""

    def test_allowlist_modules_exist(self) -> None:
        missing = [
            relative
            for relative in sorted(PAT06_COROLLARY_ALLOWLIST)
            if not (REPO_ROOT / relative).is_file()
        ]
        assert missing == [], f"AR-05 allowlist modules missing: {missing}"

    def test_services_have_no_forbidden_workflow_routing(self) -> None:
        violations: list[str] = []
        for path in _iter_services_py_files():
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative in PAT06_COROLLARY_ALLOWLIST:
                continue
            source = path.read_text(encoding="utf-8")
            for label, pattern in FORBIDDEN_WORKFLOW_PATTERNS:
                if pattern.search(source):
                    violations.append(f"{relative}: {label}")
        assert violations == [], (
            "PAT-06 corollary (AR-05): services must not select workflow "
            f"branch/lifecycle — {violations}"
        )
