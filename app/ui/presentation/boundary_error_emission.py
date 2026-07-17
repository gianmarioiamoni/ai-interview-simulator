# app/ui/presentation/boundary_error_emission.py
# EPIC-07 P2/C3 — emit CandidateFacingError + ERROR SurfaceState for async boundaries.

from __future__ import annotations

from typing import Mapping

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.surface_phase import SurfacePhase
from app.ui.presentation.surface_state import SurfaceState
from app.ui.ui_response import UIResponse

BOUNDARY_MESSAGE_KEYS: Mapping[AsyncBoundary, str] = {
    AsyncBoundary.SESSION_START: "err.session_start.failed",
    AsyncBoundary.ANSWER_SUBMIT: "err.answer_submit.failed",
    AsyncBoundary.NEXT_OR_REPORT: "err.next_or_report.failed",
    AsyncBoundary.REPORT_EXPORT: "err.report_export.failed",
    AsyncBoundary.REPLAY_ENTER: "err.replay_enter.failed",
    AsyncBoundary.SESSION_HISTORY_LOAD: "err.session_history_load.failed",
}


def emit_boundary_error(
    boundary: AsyncBoundary,
    *,
    correlation_token: str | None = None,
) -> CandidateFacingError:
    """Emit catalog-backed CandidateFacingError for a failed async boundary (AR-08)."""
    try:
        message_key = BOUNDARY_MESSAGE_KEYS[boundary]
    except KeyError as exc:
        raise ValueError(f"Unsupported AsyncBoundary={boundary!r}") from exc
    return CandidateFacingError.from_catalog(
        message_key,
        correlation_token=correlation_token,
    )


def build_error_surface_state(
    surface_id: str,
    error: CandidateFacingError,
    *,
    allows_loader: bool,
) -> SurfaceState:
    """Assemble SurfaceState.phase=ERROR for a candidate-facing boundary failure."""
    return SurfaceState(
        surface_id=surface_id,
        phase=SurfacePhase.ERROR,
        error=error,
        allows_loader=allows_loader,
    )


def present_boundary_failure(
    response: UIResponse,
    boundary: AsyncBoundary,
    *,
    surface_id: str,
    allows_loader: bool,
    correlation_token: str | None = None,
) -> tuple[UIResponse, CandidateFacingError, SurfaceState]:
    """Attach ERROR surface + catalog message_text to a UIResponse (no silent recovery)."""
    error = emit_boundary_error(boundary, correlation_token=correlation_token)
    surface_state = build_error_surface_state(
        surface_id,
        error,
        allows_loader=allows_loader,
    )
    response.feedback_markdown = error.message_text
    response.candidate_facing_error = error
    response.surface_state = surface_state
    return response, error, surface_state
