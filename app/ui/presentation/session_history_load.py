# app/ui/presentation/session_history_load.py
# EPIC-07 P3/C6 — SessionHistoryListPresentation READY/EMPTY/ERROR (I-SH-01…03).

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.boundary_error_emission import (
    build_error_surface_state,
    emit_boundary_error,
)
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.session_history_list_presentation import (
    SessionHistoryItem,
    SessionHistoryListPresentation,
)
from app.ui.presentation.surface_phase import SurfacePhase
from app.ui.presentation.surface_state import SurfaceState

_HISTORY_EMPTY_KEY = "empty.history.none"


@dataclass(frozen=True)
class SessionHistoryLoadResult:
    """Compatibility wrapper over SessionHistoryListPresentation (C4 callers)."""

    session_ids: tuple[str, ...]
    error: CandidateFacingError | None
    surface_state: SurfaceState | None
    presentation: SessionHistoryListPresentation


def present_session_history_list(
    fetch: Callable[[], Sequence[SessionHistoryItem] | None],
) -> SessionHistoryListPresentation:
    """Load history items into READY/EMPTY/ERROR; silent None is forbidden (I-SH-01)."""
    try:
        raw = fetch()
    except Exception:
        return _error_presentation()

    if raw is None:
        # I-SH-01: stub returning silent None without EMPTY/ERROR is forbidden.
        return _error_presentation()

    items = tuple(raw)
    if not items:
        return SessionHistoryListPresentation(
            items=(),
            phase=SurfacePhase.EMPTY,
            error=None,
            empty_copy_key=_HISTORY_EMPTY_KEY,
        )
    return SessionHistoryListPresentation(
        items=items,
        phase=SurfacePhase.READY,
        error=None,
        empty_copy_key=None,
    )


def load_session_history_list(
    fetch: Callable[[], Sequence[str] | None],
) -> SessionHistoryLoadResult:
    """Fetch session ids and project to SessionHistoryListPresentation (+ C4 result)."""

    def _as_items() -> Sequence[SessionHistoryItem] | None:
        raw = fetch()
        if raw is None:
            return None
        return tuple(SessionHistoryItem.from_session_ref(session_id) for session_id in raw)

    presentation = present_session_history_list(_as_items)
    if presentation.phase is SurfacePhase.ERROR:
        error = presentation.error
        assert error is not None
        surface_state = build_error_surface_state(
            "history",
            error,
            allows_loader=True,
        )
        return SessionHistoryLoadResult(
            session_ids=(),
            error=error,
            surface_state=surface_state,
            presentation=presentation,
        )
    return SessionHistoryLoadResult(
        session_ids=tuple(item.session_id for item in presentation.items),
        error=None,
        surface_state=None,
        presentation=presentation,
    )


def _error_presentation() -> SessionHistoryListPresentation:
    error = emit_boundary_error(AsyncBoundary.SESSION_HISTORY_LOAD)
    return SessionHistoryListPresentation(
        items=(),
        phase=SurfacePhase.ERROR,
        error=error,
        empty_copy_key=None,
    )
