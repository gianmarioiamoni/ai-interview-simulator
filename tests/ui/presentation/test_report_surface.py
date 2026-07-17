# tests/ui/presentation/test_report_surface.py
# EPIC-07 P5/C9 — report SurfaceState I-SS-02 + empty catalog.

from __future__ import annotations

from app.ui.presentation import (
    REPORT_EMPTY_KEY,
    AsyncBoundary,
    SurfacePhase,
    assert_no_placeholder_chrome,
    emit_boundary_error,
    get_empty_copy_entry,
    present_report_surface,
    report_loader_visible,
    surface_status_message,
    validate_deterministic_surface_not_loading,
)


class TestPresentReportSurface:
    def test_dto_ready_not_processing_is_ready_not_loading(self) -> None:
        surface = present_report_surface(dto_ready=True, is_processing=False)
        assert surface.surface_id == "report"
        assert surface.phase is SurfacePhase.READY
        assert surface.phase is not SurfacePhase.LOADING
        assert surface.empty_copy_key is None
        assert surface.allows_loader is False
        assert report_loader_visible(surface) is False
        validate_deterministic_surface_not_loading(
            "report",
            surface.phase,
            data_ready=True,
        )

    def test_dto_ready_while_processing_still_not_loading(self) -> None:
        """I-SS-02 / DM-V-SS-03: FinalReportDTO ready ⇒ phase ≠ LOADING."""
        surface = present_report_surface(dto_ready=True, is_processing=True)
        assert surface.phase is SurfacePhase.READY
        assert surface.phase is not SurfacePhase.LOADING
        assert report_loader_visible(surface) is False

    def test_empty_uses_frozen_catalog_key(self) -> None:
        surface = present_report_surface(dto_ready=False, is_processing=False)
        assert surface.phase is SurfacePhase.EMPTY
        assert surface.empty_copy_key == REPORT_EMPTY_KEY
        assert surface.empty_copy_key == "empty.report.unavailable"
        text = surface_status_message(surface)
        assert text == get_empty_copy_entry(REPORT_EMPTY_KEY).message_text
        assert_no_placeholder_chrome(text)
        assert "<i" not in text.lower()
        assert report_loader_visible(surface) is False

    def test_loading_only_when_not_ready_and_processing(self) -> None:
        surface = present_report_surface(dto_ready=False, is_processing=True)
        assert surface.phase is SurfacePhase.LOADING
        assert surface.allows_loader is True
        assert report_loader_visible(surface) is True

    def test_error_surface(self) -> None:
        error = emit_boundary_error(AsyncBoundary.REPORT_EXPORT)
        surface = present_report_surface(
            dto_ready=False,
            error=error,
            is_processing=False,
        )
        assert surface.phase is SurfacePhase.ERROR
        assert surface.error is error
        assert surface_status_message(surface) == error.message_text
