# app/ui/presentation/progress_surface.py
# EPIC-07 P5/C10 — progress SurfaceState + empty.progress.insufficient (report-hosted).

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

PROGRESS_EMPTY_KEY = "empty.progress.insufficient"
_PROGRESS_SURFACE_ID = "progress"


def present_progress_surface(
    *,
    has_sufficient_sessions: bool,
    error: CandidateFacingError | None = None,
) -> SurfaceState:
    """Assemble progress SurfaceState: ERROR / EMPTY / READY (EC-SS-01, I-SS-05).

    I-SS-02 / DM-V-SS-03: binder result ready ⇒ phase ≠ LOADING.
    """
    if error is not None:
        return SurfaceState(
            surface_id=_PROGRESS_SURFACE_ID,
            phase=SurfacePhase.ERROR,
            error=error,
            allows_loader=False,
        )

    if has_sufficient_sessions:
        phase = SurfacePhase.READY
        validate_deterministic_surface_not_loading(
            _PROGRESS_SURFACE_ID,
            phase,
            data_ready=True,
        )
        return SurfaceState(
            surface_id=_PROGRESS_SURFACE_ID,
            phase=phase,
            allows_loader=False,
        )

    state = SurfaceState(
        surface_id=_PROGRESS_SURFACE_ID,
        phase=SurfacePhase.EMPTY,
        allows_loader=False,
        empty_copy_key=PROGRESS_EMPTY_KEY,
    )
    assert_no_placeholder_chrome(empty_copy_text(PROGRESS_EMPTY_KEY))
    return state
