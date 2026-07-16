# app/ui/presentation/candidate_facing_error_catalog.py
# EPIC-07 Data Model §5.1 — CandidateFacingError.message_key catalog (frozen).

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.ui.presentation.async_boundary import AsyncBoundary


@dataclass(frozen=True)
class CandidateFacingErrorCatalogEntry:
    message_key: str
    boundary: AsyncBoundary
    is_retryable: bool
    message_text: str


_ENTRIES: tuple[CandidateFacingErrorCatalogEntry, ...] = (
    CandidateFacingErrorCatalogEntry(
        message_key="err.session_start.failed",
        boundary=AsyncBoundary.SESSION_START,
        is_retryable=True,
        message_text="We could not start your interview. Please try again.",
    ),
    CandidateFacingErrorCatalogEntry(
        message_key="err.answer_submit.failed",
        boundary=AsyncBoundary.ANSWER_SUBMIT,
        is_retryable=True,
        message_text="We could not submit your answer. Please try again.",
    ),
    CandidateFacingErrorCatalogEntry(
        message_key="err.next_or_report.failed",
        boundary=AsyncBoundary.NEXT_OR_REPORT,
        is_retryable=True,
        message_text="Something went wrong loading the next step. Please try again.",
    ),
    CandidateFacingErrorCatalogEntry(
        message_key="err.report_export.failed",
        boundary=AsyncBoundary.REPORT_EXPORT,
        is_retryable=True,
        message_text="Export failed. Please try again.",
    ),
    CandidateFacingErrorCatalogEntry(
        message_key="err.replay_enter.failed",
        boundary=AsyncBoundary.REPLAY_ENTER,
        is_retryable=True,
        message_text=(
            "We could not open this replay. Please try again or choose another session."
        ),
    ),
    CandidateFacingErrorCatalogEntry(
        message_key="err.session_history_load.failed",
        boundary=AsyncBoundary.SESSION_HISTORY_LOAD,
        is_retryable=True,
        message_text="We could not load your session history. Please try again.",
    ),
)

CANDIDATE_FACING_ERROR_CATALOG: Mapping[str, CandidateFacingErrorCatalogEntry] = {
    entry.message_key: entry for entry in _ENTRIES
}


def get_candidate_facing_error_entry(message_key: str) -> CandidateFacingErrorCatalogEntry:
    """Return catalog entry for ``message_key``; fail-fast if missing (SM-06)."""
    try:
        return CANDIDATE_FACING_ERROR_CATALOG[message_key]
    except KeyError as exc:
        raise ValueError(
            f"Unknown CandidateFacingError message_key={message_key!r} (SM-06)."
        ) from exc
