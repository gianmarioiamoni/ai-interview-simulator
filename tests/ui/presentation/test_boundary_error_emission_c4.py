# tests/ui/presentation/test_boundary_error_emission_c4.py
# EPIC-07 P2/C4 — REPORT_EXPORT / REPLAY_ENTER / SESSION_HISTORY_LOAD.

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.ui.presentation import (
    AsyncBoundary,
    SurfacePhase,
    emit_boundary_error,
    get_candidate_facing_error_entry,
    load_session_history_list,
)
from app.ui.state_handlers import export_handlers as export_handlers_module
from app.ui.state_handlers.export_handlers import _emit_report_export_failure
from app.ui.bindings.handlers.replay_layout_coordinator import ReplayLayoutCoordinator


class TestEmitC4Boundaries:
    @pytest.mark.parametrize(
        ("boundary", "message_key"),
        [
            (AsyncBoundary.REPORT_EXPORT, "err.report_export.failed"),
            (AsyncBoundary.REPLAY_ENTER, "err.replay_enter.failed"),
            (AsyncBoundary.SESSION_HISTORY_LOAD, "err.session_history_load.failed"),
        ],
    )
    def test_emit_yields_catalog_message(
        self,
        boundary: AsyncBoundary,
        message_key: str,
    ) -> None:
        entry = get_candidate_facing_error_entry(message_key)
        error = emit_boundary_error(boundary)
        assert error.boundary is boundary
        assert error.message_text == entry.message_text


class TestReportExportBoundary:
    def test_emit_report_export_failure_uses_catalog(self) -> None:
        entry = get_candidate_facing_error_entry("err.report_export.failed")
        error = _emit_report_export_failure()
        assert error.boundary is AsyncBoundary.REPORT_EXPORT
        assert error.message_text == entry.message_text

    def test_export_handlers_call_emit_on_failure_path(self) -> None:
        source = open(export_handlers_module.__file__, encoding="utf-8").read()
        assert "_emit_report_export_failure()" in source
        assert source.count("_emit_report_export_failure()") >= 2
        assert "REPORT_EXPORT" in source
        assert "err.report_export.failed" not in source  # catalog via emit helper only


class TestReplayEnterBoundary:
    def test_enter_load_failure_emits_catalog_error_surface(self) -> None:
        entry = get_candidate_facing_error_entry("err.replay_enter.failed")
        coordinator = ReplayLayoutCoordinator(session_loader=MagicMock())

        with patch.object(
            coordinator._entry,
            "load",
            side_effect=RuntimeError("graph boom"),
        ):
            snapshot = coordinator.enter("session-1")

        assert snapshot.error_visible is True
        assert snapshot.runtime is not None
        assert snapshot.runtime.error_boundary is not None
        error = snapshot.runtime.error_boundary.candidate_facing_error
        assert error.boundary is AsyncBoundary.REPLAY_ENTER
        assert error.message_text == entry.message_text
        assert entry.message_text in snapshot.error_html


class TestSessionHistoryLoadBoundary:
    def test_load_failure_emits_catalog_error(self) -> None:
        entry = get_candidate_facing_error_entry("err.session_history_load.failed")

        def _fail() -> list[str]:
            raise RuntimeError("repo boom")

        result = load_session_history_list(_fail)
        assert result.session_ids == ()
        assert result.error is not None
        assert result.error.boundary is AsyncBoundary.SESSION_HISTORY_LOAD
        assert result.error.message_text == entry.message_text
        assert result.surface_state is not None
        assert result.surface_state.phase is SurfacePhase.ERROR
        assert result.surface_state.surface_id == "history"

    def test_load_success_has_no_error(self) -> None:
        result = load_session_history_list(lambda: ["s1", "s2"])
        assert result.session_ids == ("s1", "s2")
        assert result.error is None
        assert result.surface_state is None
