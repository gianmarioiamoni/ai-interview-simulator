# tests/ui/presentation/test_replay_surface.py
# EPIC-07 P5/C10 — replay SurfaceState EMPTY/READY/ERROR catalogs.

from __future__ import annotations

from app.ui.presentation import (
    REPLAY_EMPTY_KEY,
    AsyncBoundary,
    SurfacePhase,
    assert_no_placeholder_chrome,
    emit_boundary_error,
    get_empty_copy_entry,
    present_replay_surface,
    surface_status_message,
    validate_deterministic_surface_not_loading,
)


class TestPresentReplaySurface:
    def test_has_questions_ready_not_loading(self) -> None:
        surface = present_replay_surface(has_questions=True)
        assert surface.surface_id == "replay"
        assert surface.phase is SurfacePhase.READY
        assert surface.phase is not SurfacePhase.LOADING
        validate_deterministic_surface_not_loading(
            "replay",
            surface.phase,
            data_ready=True,
        )

    def test_empty_uses_frozen_catalog_key(self) -> None:
        surface = present_replay_surface(has_questions=False)
        assert surface.phase is SurfacePhase.EMPTY
        assert surface.empty_copy_key == REPLAY_EMPTY_KEY
        assert surface.empty_copy_key == "empty.replay.no_questions"
        text = surface_status_message(surface)
        assert text == get_empty_copy_entry(REPLAY_EMPTY_KEY).message_text
        assert_no_placeholder_chrome(text)

    def test_error_uses_replay_enter_catalog(self) -> None:
        error = emit_boundary_error(AsyncBoundary.REPLAY_ENTER)
        surface = present_replay_surface(has_questions=False, error=error)
        assert surface.phase is SurfacePhase.ERROR
        assert surface.error is error
        assert surface.error.boundary is AsyncBoundary.REPLAY_ENTER
        assert surface_status_message(surface) == error.message_text
        assert_no_placeholder_chrome(error.message_text)
