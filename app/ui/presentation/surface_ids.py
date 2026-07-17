# app/ui/presentation/surface_ids.py
# EPIC-07 Data Model §3.4 — closed surface_id catalog.

from __future__ import annotations

from typing import Final, FrozenSet

SURFACE_IDS: Final[FrozenSet[str]] = frozenset(
    {
        "setup",
        "question",
        "feedback",
        "report",
        "replay",
        "progress",
        "history",
    }
)

DETERMINISTIC_SURFACE_IDS: Final[FrozenSet[str]] = frozenset(
    {"report", "replay", "progress"}
)
