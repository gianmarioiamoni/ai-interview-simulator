# tests/infrastructure/architecture/test_domain_layer_isolation.py
#
# TD-DL-001 remediation gate: domain must not import outer layers.

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_ROOT = REPO_ROOT / "domain"

FORBIDDEN_ROOTS: frozenset[str] = frozenset({"services", "app", "infrastructure"})


def _iter_domain_py_files() -> list[Path]:
    return sorted(
        path
        for path in DOMAIN_ROOT.rglob("*.py")
        if path.is_file() and path.name != "__pycache__"
    )


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


class TestDomainLayerIsolation:
    """Domain layer must not depend on services/, app/, or infrastructure/."""

    def test_domain_has_no_outer_layer_imports(self) -> None:
        violations: list[str] = []
        for path in _iter_domain_py_files():
            bad = sorted(FORBIDDEN_ROOTS & _imported_roots(path))
            if bad:
                rel = path.relative_to(REPO_ROOT).as_posix()
                violations.append(f"{rel}: {', '.join(bad)}")
        assert violations == [], (
            "TD-DL-001: domain → outer-layer imports forbidden:\n"
            + "\n".join(violations)
        )
