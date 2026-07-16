# tests/ui/architecture/test_export_explainability_architecture.py
# EPIC-06 M3 / C8 — AT-01 / X-08: export explainability uses sole FinalReportDTO factory path.

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPORT_MODULES = (
    "services/report_export_service.py",
    "app/ui/state_handlers/export_handlers.py",
)

FORBIDDEN_DUAL_READ_IMPORTS = {
    "SessionHistory",
    "ObservationStore",
    "Observation",
    "ObservationSnapshot",
}

FORBIDDEN_DUAL_READ_MODULE_FRAGMENTS = (
    "session_history",
    "observation_store",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _imported_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
                names.add(alias.name.split(".")[0])
                if alias.asname:
                    names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
                names.add(node.module.split(".")[0])
            for alias in node.names:
                names.add(alias.name)
                if alias.asname:
                    names.add(alias.asname)
    return names


class TestExportExplainabilitySoleFactory:
    """AT-01 — report HTML and export explainability share FinalReportDTO factory path."""

    def test_export_service_consumes_final_report_dto_and_shared_renderer(self) -> None:
        source = _read("services/report_export_service.py")
        imported = _imported_names(source)
        assert "FinalReportDTO" in imported
        assert "build_report_markdown" in imported
        assert "from_components" not in source
        assert "build_report_markdown(report)" in source

    def test_export_handlers_use_dto_mapper_not_domain_bypass(self) -> None:
        source = _read("app/ui/state_handlers/export_handlers.py")
        assert "to_final_report_dto" in source
        assert "ReportExportService" in source
        assert "from_components" not in source
        # Must not pass domain Report into export service directly.
        assert "state.report)" not in source.replace(" ", "")

    @pytest.mark.parametrize("relative_path", EXPORT_MODULES)
    def test_export_modules_do_not_dual_read_session_history_or_observation(
        self, relative_path: str
    ) -> None:
        source = _read(relative_path)
        imported = _imported_names(source)
        for name in FORBIDDEN_DUAL_READ_IMPORTS:
            assert name not in imported, (
                f"Forbidden dual-read import {name!r} in {relative_path}"
            )
        for fragment in FORBIDDEN_DUAL_READ_MODULE_FRAGMENTS:
            assert not any(fragment in name for name in imported), (
                f"Forbidden dual-read module fragment {fragment!r} in {relative_path}"
            )
