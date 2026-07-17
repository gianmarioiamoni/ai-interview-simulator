# app/ui/presentation/execution_error_kind.py
# EPIC-07 Data Model §3.3 — closed ExecutionErrorKind enum.

from __future__ import annotations

from enum import Enum


class ExecutionErrorKind(str, Enum):
    """Closed set of candidate-safe execution error kinds (EC-EX-01)."""

    SYNTAX = "SYNTAX"
    RUNTIME = "RUNTIME"
    SQL = "SQL"
    TEST_FAILURE = "TEST_FAILURE"
    UNKNOWN_SAFE = "UNKNOWN_SAFE"
