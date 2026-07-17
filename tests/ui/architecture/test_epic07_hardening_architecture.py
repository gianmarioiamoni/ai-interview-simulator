# tests/ui/architecture/test_epic07_hardening_architecture.py
# EPIC-07 C15 — hardening: AsyncBoundary coverage, FeedbackBundle writer,
# DELETE_TARGET absent, language_mode ≠ locale (AR-04/08/11, R-07/14/15).

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.ui.bindings.validators.input_validator import InputValidator
from app.ui.layout.layout_builder import UILayoutBuilder
from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.boundary_error_emission import (
    BOUNDARY_MESSAGE_KEYS,
    emit_boundary_error,
)
from app.ui.presentation.candidate_facing_error_catalog import (
    CANDIDATE_FACING_ERROR_CATALOG,
)
from app.ui.presentation.session_config_validation import is_language_mode_complete

REPO_ROOT = Path(__file__).resolve().parents[3]

DELETE_TARGET_PATHS: frozenset[str] = frozenset(
    {
        "app/ui/views/setup_view.py",
        "app/ui/views/interview_written_view.py",
        "app/ui/views/interview_coding_view.py",
        "app/ui/views/interview_database_view.py",
        "app/ui/utils/loading_utils.py",
        "app/ui/response/sections/error_hint_builder.py",
        "app/ui/presenters/result_presenter.py",
    }
)

# Runtime sole writer of InterviewState.last_feedback_bundle (AR-11).
RUNTIME_FEEDBACK_WRITER = "app/graph/nodes/feedback_node.py"

# Presentation plane must remain read/projection only for FeedbackBundle.
PRESENTATION_ROOT = REPO_ROOT / "app" / "ui" / "presentation"

BOUNDARY_EMISSION_SITES: dict[AsyncBoundary, tuple[str, ...]] = {
    AsyncBoundary.SESSION_START: ("app/ui/state_handlers/start.py",),
    AsyncBoundary.ANSWER_SUBMIT: ("app/ui/state_handlers/submit.py",),
    AsyncBoundary.NEXT_OR_REPORT: ("app/ui/state_handlers/navigation.py",),
    AsyncBoundary.REPORT_EXPORT: ("app/ui/state_handlers/export_handlers.py",),
    AsyncBoundary.REPLAY_ENTER: (
        "app/ui/bindings/handlers/replay_layout_coordinator.py",
        "app/ui/replay/panels/replay_error_boundary.py",
    ),
    AsyncBoundary.SESSION_HISTORY_LOAD: (
        "app/ui/presentation/session_history_load.py",
    ),
}


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _assign_targets_named(source: str, name: str) -> list[str]:
    """Return assignment target attribute names matching ``name``."""
    tree = ast.parse(source)
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                hits.extend(_attr_names(target, name))
        elif isinstance(node, ast.AnnAssign) and node.target is not None:
            hits.extend(_attr_names(node.target, name))
        elif isinstance(node, ast.AugAssign):
            hits.extend(_attr_names(node.target, name))
        elif isinstance(node, ast.Call):
            # model_copy(update={"last_feedback_bundle": ...})
            for keyword in node.keywords:
                if keyword.arg == "update" and isinstance(keyword.value, ast.Dict):
                    for key in keyword.value.keys:
                        if (
                            isinstance(key, ast.Constant)
                            and key.value == name
                        ):
                            hits.append(name)
    return hits


def _attr_names(node: ast.AST, name: str) -> list[str]:
    if isinstance(node, ast.Name) and node.id == name:
        return [name]
    if isinstance(node, ast.Attribute) and node.attr == name:
        return [name]
    if isinstance(node, ast.Tuple):
        found: list[str] = []
        for elt in node.elts:
            found.extend(_attr_names(elt, name))
        return found
    return []


class TestAsyncBoundaryCoverage:
    """R-07 / AR-08: every AsyncBoundary has catalog + emission coverage."""

    def test_enum_is_closed_six_members(self) -> None:
        members = {member.name for member in AsyncBoundary}
        assert members == {
            "SESSION_START",
            "ANSWER_SUBMIT",
            "NEXT_OR_REPORT",
            "REPORT_EXPORT",
            "REPLAY_ENTER",
            "SESSION_HISTORY_LOAD",
        }

    def test_boundary_message_keys_cover_all_members(self) -> None:
        assert set(BOUNDARY_MESSAGE_KEYS) == set(AsyncBoundary)

    def test_catalog_covers_all_boundaries(self) -> None:
        catalog_boundaries = {
            entry.boundary for entry in CANDIDATE_FACING_ERROR_CATALOG.values()
        }
        assert catalog_boundaries == set(AsyncBoundary)

    @pytest.mark.parametrize("boundary", list(AsyncBoundary))
    def test_emit_yields_catalog_backed_error(self, boundary: AsyncBoundary) -> None:
        error = emit_boundary_error(boundary)
        assert error.boundary is boundary
        assert error.message_key == BOUNDARY_MESSAGE_KEYS[boundary]
        assert error.message_text.strip() != ""

    @pytest.mark.parametrize("boundary", list(AsyncBoundary))
    def test_emission_site_references_boundary(self, boundary: AsyncBoundary) -> None:
        sites = BOUNDARY_EMISSION_SITES[boundary]
        needle = f"AsyncBoundary.{boundary.name}"
        assert any(needle in _read(path) for path in sites), (
            f"No emission site references {needle} in {sites}"
        )


class TestFeedbackBundleWriterInvariant:
    """R-15 / AR-11: runtime feedback path remains sole InterviewState writer."""

    def test_runtime_feedback_node_assigns_last_feedback_bundle(self) -> None:
        source = _read(RUNTIME_FEEDBACK_WRITER)
        assert _assign_targets_named(source, "last_feedback_bundle"), (
            "feedback_node must remain the InterviewState FeedbackBundle writer"
        )

    def test_presentation_modules_do_not_assign_last_feedback_bundle(self) -> None:
        violators: list[str] = []
        for path in PRESENTATION_ROOT.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            if _assign_targets_named(source, "last_feedback_bundle"):
                violators.append(str(path.relative_to(REPO_ROOT)))
        assert violators == [], (
            "Presentation path must not assign last_feedback_bundle: "
            f"{violators}"
        )

    def test_execution_error_presentation_does_not_construct_feedback_bundle(
        self,
    ) -> None:
        source = _read("app/ui/presentation/execution_error_presentation.py")
        tree = ast.parse(source)
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
        assert "FeedbackBundle" not in names
        assert "FeedbackBundleFactory" not in names
        assert "last_feedback_bundle" not in source


class TestDeleteTargetAbsent:
    """R-14 / EC-UH-01: DELETE_TARGET modules removed after C14."""

    @pytest.mark.parametrize("relative_path", sorted(DELETE_TARGET_PATHS))
    def test_delete_target_file_absent(self, relative_path: str) -> None:
        assert not (REPO_ROOT / relative_path).exists(), (
            f"DELETE_TARGET still present: {relative_path}"
        )

    def test_no_production_import_of_delete_target_modules(self) -> None:
        forbidden = {
            path.replace("/", ".").removesuffix(".py") for path in DELETE_TARGET_PATHS
        }
        violators: list[str] = []
        for path in (REPO_ROOT / "app").rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
            if imported & forbidden:
                violators.append(str(path.relative_to(REPO_ROOT)))
        assert violators == [], (
            f"Production imports of DELETE_TARGET remain: {violators}"
        )


class TestLanguageModeNotLocaleAlone:
    """AR-04 / I-SC-03/04: language mode ≠ UI locale; locale alone insufficient."""

    def test_live_layout_exposes_distinct_locale_and_language_mode_controls(
        self,
    ) -> None:
        source = inspect.getsource(UILayoutBuilder.build)
        assert 'label="UI locale"' in source
        assert 'label="Coding languages (session mode)"' in source
        assert "enabled_languages_input" in source
        assert "language_input" in source

    def test_input_validator_requires_language_mode_not_locale_alone(self) -> None:
        source = inspect.getsource(InputValidator.validate)
        assert "is_language_mode_complete" in source
        assert "enabled_languages" in source

    def test_locale_alone_is_architecturally_incomplete(self) -> None:
        assert is_language_mode_complete(None, "en") is False
        assert is_language_mode_complete([], "it") is False
        assert is_language_mode_complete(("python",), None) is True
