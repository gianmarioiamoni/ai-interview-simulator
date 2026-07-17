# app/ui/presentation/empty_copy_catalog.py
# EPIC-07 Data Model §5.2 — empty-state copy keys (frozen).

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class EmptyCopyCatalogEntry:
    empty_copy_key: str
    surface_id: str
    message_text: str


_ENTRIES: tuple[EmptyCopyCatalogEntry, ...] = (
    EmptyCopyCatalogEntry(
        empty_copy_key="empty.report.unavailable",
        surface_id="report",
        message_text="Your report is not available for this session.",
    ),
    EmptyCopyCatalogEntry(
        empty_copy_key="empty.replay.no_questions",
        surface_id="replay",
        message_text="This replay has no questions to show.",
    ),
    EmptyCopyCatalogEntry(
        empty_copy_key="empty.progress.insufficient",
        surface_id="progress",
        message_text="Complete more sessions to see your progress trend.",
    ),
    EmptyCopyCatalogEntry(
        empty_copy_key="empty.history.none",
        surface_id="history",
        message_text="No previous sessions yet.",
    ),
    EmptyCopyCatalogEntry(
        empty_copy_key="empty.feedback.none",
        surface_id="feedback",
        message_text="No feedback is available for this answer yet.",
    ),
    EmptyCopyCatalogEntry(
        empty_copy_key="empty.question.none",
        surface_id="question",
        message_text="No question is available right now.",
    ),
)

EMPTY_COPY_CATALOG: Mapping[str, EmptyCopyCatalogEntry] = {
    entry.empty_copy_key: entry for entry in _ENTRIES
}


def get_empty_copy_entry(empty_copy_key: str) -> EmptyCopyCatalogEntry:
    """Return empty-copy catalog entry; fail-fast if missing (SM-06)."""
    try:
        return EMPTY_COPY_CATALOG[empty_copy_key]
    except KeyError as exc:
        raise ValueError(
            f"Unknown empty_copy_key={empty_copy_key!r} (SM-06)."
        ) from exc
