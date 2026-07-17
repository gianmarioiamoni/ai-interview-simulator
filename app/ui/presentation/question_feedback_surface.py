# app/ui/presentation/question_feedback_surface.py
# EPIC-07 P4/C8 — question/feedback SurfaceState EMPTY/READY/ERROR wiring.

from __future__ import annotations

import re
from typing import Sequence

from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.empty_copy_catalog import get_empty_copy_entry
from app.ui.presentation.execution_error_presentation import ExecutionErrorPresentation
from app.ui.presentation.surface_phase import SurfacePhase
from app.ui.presentation.surface_state import SurfaceState

QUESTION_EMPTY_KEY = "empty.question.none"
FEEDBACK_EMPTY_KEY = "empty.feedback.none"

_QUESTION_SURFACE_ID = "question"
_FEEDBACK_SURFACE_ID = "feedback"

# I-SS-03 / OF-01 — unfinished developer chrome forbidden on EMPTY/READY copy.
_PLACEHOLDER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\bWIP\b"),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bcoming soon\b", re.IGNORECASE),
    re.compile(r"\blorem ipsum\b", re.IGNORECASE),
    re.compile(r"<i\b", re.IGNORECASE),
    re.compile(r"\bstub\b", re.IGNORECASE),
)


def assert_no_placeholder_chrome(text: str) -> None:
    """Fail-fast when candidate-facing copy contains forbidden placeholder patterns (I-SS-03)."""
    if not text or not text.strip():
        raise ValueError("I-SS-03: candidate-facing copy must be non-empty finished text.")
    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            raise ValueError(
                f"I-SS-03: forbidden placeholder pattern in candidate copy: {pattern.pattern!r}."
            )


def empty_copy_text(empty_copy_key: str) -> str:
    """Return §5.2 catalog text and enforce I-SS-03."""
    text = get_empty_copy_entry(empty_copy_key).message_text
    assert_no_placeholder_chrome(text)
    return text


def present_question_surface(
    *,
    has_question: bool,
    error: CandidateFacingError | None = None,
    allows_loader: bool = False,
) -> SurfaceState:
    """Assemble question SurfaceState: ERROR / EMPTY / READY (EC-SS-01)."""
    if error is not None:
        return SurfaceState(
            surface_id=_QUESTION_SURFACE_ID,
            phase=SurfacePhase.ERROR,
            error=error,
            allows_loader=allows_loader,
        )
    if not has_question:
        state = SurfaceState(
            surface_id=_QUESTION_SURFACE_ID,
            phase=SurfacePhase.EMPTY,
            allows_loader=allows_loader,
            empty_copy_key=QUESTION_EMPTY_KEY,
        )
        assert_no_placeholder_chrome(empty_copy_text(QUESTION_EMPTY_KEY))
        return state
    return SurfaceState(
        surface_id=_QUESTION_SURFACE_ID,
        phase=SurfacePhase.READY,
        allows_loader=allows_loader,
    )


def present_feedback_surface(
    *,
    has_feedback: bool,
    error: CandidateFacingError | None = None,
    allows_loader: bool = False,
) -> SurfaceState:
    """Assemble feedback SurfaceState: ERROR / EMPTY / READY (EC-SS-01)."""
    if error is not None:
        return SurfaceState(
            surface_id=_FEEDBACK_SURFACE_ID,
            phase=SurfacePhase.ERROR,
            error=error,
            allows_loader=allows_loader,
        )
    if not has_feedback:
        state = SurfaceState(
            surface_id=_FEEDBACK_SURFACE_ID,
            phase=SurfacePhase.EMPTY,
            allows_loader=allows_loader,
            empty_copy_key=FEEDBACK_EMPTY_KEY,
        )
        assert_no_placeholder_chrome(empty_copy_text(FEEDBACK_EMPTY_KEY))
        return state
    return SurfaceState(
        surface_id=_FEEDBACK_SURFACE_ID,
        phase=SurfacePhase.READY,
        allows_loader=allows_loader,
    )


def format_execution_error_markdown(
    presentation: ExecutionErrorPresentation,
) -> str:
    """Render EC-EX-01 presentation as candidate-safe markdown (no traceback)."""
    assert presentation.shows_traceback is False
    assert_no_placeholder_chrome(presentation.candidate_message)
    parts: list[str] = [presentation.candidate_message]
    for line in presentation.detail_lines:
        assert_no_placeholder_chrome(line)
        parts.append(f"- {line}")
    return "\n".join(parts)


def surface_status_message(surface: SurfaceState) -> str:
    """Candidate-facing status copy for EMPTY/ERROR; empty string when READY/LOADING."""
    if surface.phase is SurfacePhase.EMPTY:
        return empty_copy_text(surface.empty_copy_key or "")
    if surface.phase is SurfacePhase.ERROR:
        if surface.error is None:
            raise ValueError("DM-V-SS-01: ERROR surface requires error.")
        assert_no_placeholder_chrome(surface.error.message_text)
        return surface.error.message_text
    return ""


def assert_texts_have_no_placeholder_chrome(texts: Sequence[str]) -> None:
    """Batch I-SS-03 check for READY/EMPTY candidate-facing strings."""
    for text in texts:
        if text and text.strip():
            assert_no_placeholder_chrome(text)
