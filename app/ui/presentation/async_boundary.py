# app/ui/presentation/async_boundary.py
# EPIC-07 EC-CF-02 / Data Model §3.1 — closed AsyncBoundary enum.

from __future__ import annotations

from enum import Enum


class AsyncBoundary(str, Enum):
    """Closed set of async candidate boundaries that require a fallback (I-CF-04)."""

    SESSION_START = "SESSION_START"
    ANSWER_SUBMIT = "ANSWER_SUBMIT"
    NEXT_OR_REPORT = "NEXT_OR_REPORT"
    REPORT_EXPORT = "REPORT_EXPORT"
    REPLAY_ENTER = "REPLAY_ENTER"
    SESSION_HISTORY_LOAD = "SESSION_HISTORY_LOAD"
