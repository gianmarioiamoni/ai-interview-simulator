# tests/ui/presentation/test_progress_surface.py
# EPIC-07 P5/C10 — progress SurfaceState + empty.progress.insufficient.

from __future__ import annotations

from app.ui.presentation import (
    PROGRESS_EMPTY_KEY,
    AsyncBoundary,
    SurfacePhase,
    assert_no_placeholder_chrome,
    emit_boundary_error,
    get_empty_copy_entry,
    present_progress_surface,
    surface_status_message,
    validate_deterministic_surface_not_loading,
)


class TestPresentProgressSurface:
    def test_sufficient_sessions_ready_not_loading(self) -> None:
        surface = present_progress_surface(has_sufficient_sessions=True)
        assert surface.surface_id == "progress"
        assert surface.phase is SurfacePhase.READY
        assert surface.phase is not SurfacePhase.LOADING
        validate_deterministic_surface_not_loading(
            "progress",
            surface.phase,
            data_ready=True,
        )

    def test_insufficient_uses_frozen_catalog_key(self) -> None:
        surface = present_progress_surface(has_sufficient_sessions=False)
        assert surface.phase is SurfacePhase.EMPTY
        assert surface.empty_copy_key == PROGRESS_EMPTY_KEY
        assert surface.empty_copy_key == "empty.progress.insufficient"
        text = surface_status_message(surface)
        assert text == get_empty_copy_entry(PROGRESS_EMPTY_KEY).message_text
        assert_no_placeholder_chrome(text)

    def test_error_surface(self) -> None:
        error = emit_boundary_error(AsyncBoundary.REPORT_EXPORT)
        surface = present_progress_surface(
            has_sufficient_sessions=False,
            error=error,
        )
        assert surface.phase is SurfacePhase.ERROR
        assert surface.error is error
