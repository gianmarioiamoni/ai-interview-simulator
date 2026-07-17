# app/ui/presentation/session_history_load.py
# EPIC-07 P2/C4 — SESSION_HISTORY_LOAD error emission (list completeness → C6).

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.boundary_error_emission import (
    build_error_surface_state,
    emit_boundary_error,
)
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.surface_state import SurfaceState


@dataclass(frozen=True)
class SessionHistoryLoadResult:
    """Outcome of a history-list load attempt (error path covered in C4)."""

    session_ids: tuple[str, ...]
    error: CandidateFacingError | None
    surface_state: SurfaceState | None


def load_session_history_list(
    fetch: Callable[[], Sequence[str]],
) -> SessionHistoryLoadResult:
    """Load session history ids; on failure emit SESSION_HISTORY_LOAD (AR-08 / I-SH-03)."""
    try:
        session_ids = tuple(fetch())
    except Exception:
        error = emit_boundary_error(AsyncBoundary.SESSION_HISTORY_LOAD)
        surface_state = build_error_surface_state(
            "history",
            error,
            allows_loader=True,
        )
        return SessionHistoryLoadResult(
            session_ids=(),
            error=error,
            surface_state=surface_state,
        )
    return SessionHistoryLoadResult(
        session_ids=session_ids,
        error=None,
        surface_state=None,
    )
