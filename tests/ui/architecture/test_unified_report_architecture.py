# tests/ui/architecture/test_unified_report_architecture.py
# EPIC-V13-05 Phase 6 — architectural enforcement for Unified Report frozen invariants.

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.ui.bindings.handlers.replay_layout_coordinator import (
    resolve_session_id_from_report,
)
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report.sections.progress_trend_panel import (
    _UI_TREND_SESSION_THRESHOLD,
    render_progress_trend_panel,
)
from domain.contracts.progress.learning_progress import LearningProgress
from tests.domain.contracts.report.conftest import make_report

REPO_ROOT = Path(__file__).resolve().parents[3]

# Report presentation path (Plane A + Plane B bind/render). Must not dual-read SessionHistory
# for Report-owned fields (R-01 / R-05).
REPORT_PRESENTATION_MODULES = (
    "app/ui/dto/final_report_dto.py",
    "app/ui/views/report_view.py",
    "app/ui/views/report/report_renderer.py",
    "app/ui/views/report/report_view_model_builder.py",
    "app/ui/views/report/learning_progress_binder.py",
    "app/ui/views/report/sections/study_recommendations_section.py",
    "app/ui/views/report/sections/progress_trend_panel.py",
    "app/ui/views/report/sections/overall_section.py",
    "app/ui/views/report/sections/executive_section.py",
    "app/ui/views/report/sections/went_well_section.py",
    "app/ui/views/report/sections/held_you_back_section.py",
    "app/ui/views/report/sections/knowledge_gap_section.py",
    "app/ui/views/report/sections/next_strategy_section.py",
    "app/ui/views/report/sections/performance_section.py",
    "app/ui/views/report/sections/dimension_section.py",
    "app/ui/views/report/sections/question_section.py",
    "app/ui/views/report/sections/market_section.py",
    "app/ui/views/report/sections/decision_section.py",
    "app/ui/views/report/sections/signal_section.py",
    "app/ui/views/report/sections/roadmap_section.py",
    "app/ui/views/report/sections/narrative_section.py",
    "app/ui/views/report/sections/coaching_section.py",
    "app/ui/mappers/interview_state_mapper.py",
)

FORBIDDEN_PROGRESS_DTO_FIELDS = (
    "learning_progress",
    "behavioral_trend",
    "session_entries",
    "session_count",
    "has_sufficient_data",
    "longitudinal_profile",
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
                if alias.asname:
                    names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
            for alias in node.names:
                names.add(alias.name)
                if alias.asname:
                    names.add(alias.asname)
    return names


class TestSoleFinalReportDtoFactory:
    def test_from_components_absent(self) -> None:
        assert not hasattr(FinalReportDTO, "from_components")

    def test_from_report_is_sole_factory(self) -> None:
        assert hasattr(FinalReportDTO, "from_report")
        assert callable(FinalReportDTO.from_report)

    def test_from_report_accepts_only_report(self) -> None:
        signature = inspect.signature(FinalReportDTO.from_report)
        params = [
            name
            for name in signature.parameters
            if name not in {"cls", "self"}
        ]
        assert params == ["report"]

    def test_audit_script_has_no_from_components(self) -> None:
        source = _read("scripts/audit_report_quality.py")
        tree = ast.parse(source)
        called_attrs: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                called_attrs.add(node.attr)
        assert "from_components" not in called_attrs
        assert "from_components" not in source
        assert "FinalReportDTO.from_report" in source


class TestNoSessionHistoryDualReadOnPresentationPath:
    @pytest.mark.parametrize("relative_path", REPORT_PRESENTATION_MODULES)
    def test_module_does_not_import_session_history(self, relative_path: str) -> None:
        source = _read(relative_path)
        imported = _imported_names(source)
        assert "SessionHistory" not in imported
        assert not any("session_history" in name for name in imported)


class TestStudyRecommendationsSoleSource:
    def test_vm_builder_study_recommendations_has_no_coaching_snapshot_fallback(
        self,
    ) -> None:
        source = _read("app/ui/views/report/report_view_model_builder.py")
        # Study recommendations block must not fall through to coaching_snapshot.
        study_block_start = source.index("study_recommendations = list(")
        study_block = source[study_block_start : study_block_start + 200]
        assert "coaching_snapshot" not in study_block
        assert 'getattr(report, "study_recommendations"' in study_block


class TestReplaySessionIdSoleSource:
    def test_resolver_source_uses_report_session_id_only(self) -> None:
        source = _read("app/ui/bindings/handlers/replay_layout_coordinator.py")
        tree = ast.parse(source)
        resolver = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "resolve_session_id_from_report"
        )
        # Executable return must be Report.session_id (docstring may name forbidden sources).
        returns = [
            node.value
            for node in ast.walk(resolver)
            if isinstance(node, ast.Return) and node.value is not None
        ]
        assert len(returns) == 1
        returned = returns[0]
        assert isinstance(returned, ast.Attribute)
        assert returned.attr == "session_id"
        assert isinstance(returned.value, ast.Attribute)
        assert returned.value.attr == "report"

        body_nodes = resolver.body
        if (
            body_nodes
            and isinstance(body_nodes[0], ast.Expr)
            and isinstance(body_nodes[0].value, ast.Constant)
        ):
            body_nodes = body_nodes[1:]
        body_source = ast.unparse(ast.Module(body=body_nodes, type_ignores=[]))
        assert "session_history" not in body_source
        assert "interview_id" not in body_source

    def test_resolver_returns_report_session_id(self) -> None:
        report = make_report(session_id="arch-session-001")
        state = type("State", (), {"report": report})()
        assert resolve_session_id_from_report(state) == "arch-session-001"


class TestProgressTrendPanelGate:
    def test_ui_gate_threshold_is_three(self) -> None:
        assert _UI_TREND_SESSION_THRESHOLD == 3

    def test_gate_uses_session_count_not_has_sufficient_data(self) -> None:
        source = _read("app/ui/views/report/sections/progress_trend_panel.py")
        tree = ast.parse(source)
        render_fn = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "render_progress_trend_panel"
        )
        # Executable body only (exclude docstring Constant at body[0] when present).
        body_nodes = render_fn.body
        if (
            body_nodes
            and isinstance(body_nodes[0], ast.Expr)
            and isinstance(body_nodes[0].value, ast.Constant)
        ):
            body_nodes = body_nodes[1:]
        body_source = ast.unparse(ast.Module(body=body_nodes, type_ignores=[]))
        assert "session_count" in body_source
        assert "has_sufficient_data" not in body_source
        assert "_UI_TREND_SESSION_THRESHOLD" in body_source

    def test_panel_consumes_learning_progress_only(self) -> None:
        signature = inspect.signature(render_progress_trend_panel)
        params = list(signature.parameters.values())
        assert len(params) == 1
        annotation = params[0].annotation
        assert annotation is LearningProgress or annotation == "LearningProgress"


class TestFinalReportDtoHasNoProgressFields:
    def test_dto_model_fields_exclude_progress(self) -> None:
        fields = set(FinalReportDTO.model_fields)
        for forbidden in FORBIDDEN_PROGRESS_DTO_FIELDS:
            assert forbidden not in fields

    def test_from_report_result_has_no_progress_attributes(self) -> None:
        dto = FinalReportDTO.from_report(make_report())
        for forbidden in FORBIDDEN_PROGRESS_DTO_FIELDS:
            assert not hasattr(dto, forbidden)


class TestProgressBindPathContract:
    def test_binder_imports_progress_tracker_not_session_history(self) -> None:
        source = _read("app/ui/views/report/learning_progress_binder.py")
        imported = _imported_names(source)
        assert "ProgressTracker" in imported or any(
            "progress_tracker" in name for name in imported
        )
        assert "SessionHistory" not in imported
        assert not any("session_history" in name for name in imported)

    def test_ui_response_builder_binds_via_binder(self) -> None:
        source = _read("app/ui/builders/ui_response_builder.py")
        assert "bind_learning_progress" in source
        assert "FinalReportDTO.from_report" in source
        assert "from_components" not in source
