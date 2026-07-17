# app/ui/presentation/execution_error_catalog.py
# EPIC-07 Data Model §5.3 — execution error base messages (frozen).

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.ui.presentation.execution_error_kind import ExecutionErrorKind


@dataclass(frozen=True)
class ExecutionErrorCatalogEntry:
    kind: ExecutionErrorKind
    candidate_message: str


_ENTRIES: tuple[ExecutionErrorCatalogEntry, ...] = (
    ExecutionErrorCatalogEntry(
        kind=ExecutionErrorKind.SYNTAX,
        candidate_message="There is a syntax error in your code.",
    ),
    ExecutionErrorCatalogEntry(
        kind=ExecutionErrorKind.RUNTIME,
        candidate_message="Your code hit a runtime error.",
    ),
    ExecutionErrorCatalogEntry(
        kind=ExecutionErrorKind.SQL,
        candidate_message="There is a problem with your SQL.",
    ),
    ExecutionErrorCatalogEntry(
        kind=ExecutionErrorKind.TEST_FAILURE,
        candidate_message="Some tests did not pass.",
    ),
    ExecutionErrorCatalogEntry(
        kind=ExecutionErrorKind.UNKNOWN_SAFE,
        candidate_message="We could not run your code successfully.",
    ),
)

EXECUTION_ERROR_CATALOG: Mapping[ExecutionErrorKind, ExecutionErrorCatalogEntry] = {
    entry.kind: entry for entry in _ENTRIES
}


def get_execution_error_entry(kind: ExecutionErrorKind) -> ExecutionErrorCatalogEntry:
    """Return §5.3 catalog entry for ``kind``; fail-fast if missing (SM-06)."""
    try:
        return EXECUTION_ERROR_CATALOG[kind]
    except KeyError as exc:
        raise ValueError(
            f"Unknown ExecutionErrorKind={kind!r} (SM-06)."
        ) from exc
