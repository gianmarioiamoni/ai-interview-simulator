# app/ui/presentation/report_surface.py
# EPIC-07 P5/C9 — report SurfaceState I-SS-02 + empty catalog wiring.

from __future__ import annotations

from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.question_feedback_surface import (
    assert_no_placeholder_chrome,
    empty_copy_text,
)
from app.ui.presentation.surface_phase import SurfacePhase
from app.ui.presentation.surface_state import SurfaceState
from app.ui.presentation.surface_state_validation import (
    validate_deterministic_surface_not_loading,
)

REPORT_EMPTY_KEY = "empty.report.unavailable"
_REPORT_SURFACE_ID = "report"


def present_report_surface(
    *,
    dto_ready: bool,
    error: CandidateFacingError | None = None,
    is_processing: bool = False,
) -> SurfaceState:
    """Assemble report SurfaceState: ERROR / EMPTY / READY / LOADING (EC-SS-01).

    I-SS-02 / DM-V-SS-03: when FinalReportDTO is ready, phase must not be LOADING.
    """
    if error is not None:
        return SurfaceState(
            surface_id=_REPORT_SURFACE_ID,
            phase=SurfacePhase.ERROR,
            error=error,
            allows_loader=bool(is_processing),
        )

    if dto_ready:
        phase = SurfacePhase.READY
        validate_deterministic_surface_not_loading(
            _REPORT_SURFACE_ID,
            phase,
            data_ready=True,
        )
        return SurfaceState(
            surface_id=_REPORT_SURFACE_ID,
            phase=phase,
            allows_loader=False,
        )

    if is_processing:
        return SurfaceState(
            surface_id=_REPORT_SURFACE_ID,
            phase=SurfacePhase.LOADING,
            allows_loader=True,
        )

    state = SurfaceState(
        surface_id=_REPORT_SURFACE_ID,
        phase=SurfacePhase.EMPTY,
        allows_loader=False,
        empty_copy_key=REPORT_EMPTY_KEY,
    )
    assert_no_placeholder_chrome(empty_copy_text(REPORT_EMPTY_KEY))
    return state


def report_loader_visible(surface: SurfaceState) -> bool:
    """Loader chrome only while report surface is LOADING (I-SS-01/I-SS-02)."""
    return surface.phase is SurfacePhase.LOADING
