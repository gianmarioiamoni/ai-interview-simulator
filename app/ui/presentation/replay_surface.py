# app/ui/presentation/replay_surface.py
# EPIC-07 P5/C10 — replay SurfaceState EMPTY/READY/ERROR + empty.replay.no_questions.

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

REPLAY_EMPTY_KEY = "empty.replay.no_questions"
_REPLAY_SURFACE_ID = "replay"


def present_replay_surface(
    *,
    has_questions: bool,
    error: CandidateFacingError | None = None,
) -> SurfaceState:
    """Assemble replay SurfaceState: ERROR / EMPTY / READY (EC-SS-01).

    I-SS-02 / DM-V-SS-03: successful ReplaySession with questions ⇒ phase ≠ LOADING.
    """
    if error is not None:
        return SurfaceState(
            surface_id=_REPLAY_SURFACE_ID,
            phase=SurfacePhase.ERROR,
            error=error,
            allows_loader=False,
        )

    if has_questions:
        phase = SurfacePhase.READY
        validate_deterministic_surface_not_loading(
            _REPLAY_SURFACE_ID,
            phase,
            data_ready=True,
        )
        return SurfaceState(
            surface_id=_REPLAY_SURFACE_ID,
            phase=phase,
            allows_loader=False,
        )

    state = SurfaceState(
        surface_id=_REPLAY_SURFACE_ID,
        phase=SurfacePhase.EMPTY,
        allows_loader=False,
        empty_copy_key=REPLAY_EMPTY_KEY,
    )
    assert_no_placeholder_chrome(empty_copy_text(REPLAY_EMPTY_KEY))
    return state
