# app/ui/presentation/execution_error_presentation.py
# EPIC-07 EC-EX-01 / Data Model §4.3 — ExecutionErrorPresentation projector.

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.ui.presentation.execution_error_catalog import get_execution_error_entry
from app.ui.presentation.execution_error_kind import ExecutionErrorKind

_TRACEBACK_MARKER = "Traceback"
_PY_PATH_SEGMENT = re.compile(r"(?:^|[/\\])[^/\\]+\.py(?:$|[/\\:])")
_ABSOLUTE_PATH = re.compile(r"(?:^|[\s\"'`])(?:/[^\s\"'`]+|[A-Za-z]:\\[^\s\"'`]+)")
_EXCEPTION_TYPE_NAME = re.compile(
    r"\b[A-Z][A-Za-z0-9_]*Error\b|\b[A-Z][A-Za-z0-9_]*Exception\b"
)


def _is_unsafe_candidate_text(text: str) -> bool:
    return bool(
        _TRACEBACK_MARKER in text
        or _PY_PATH_SEGMENT.search(text)
        or _ABSOLUTE_PATH.search(text)
        or _EXCEPTION_TYPE_NAME.search(text)
    )


def classify_execution_error_kind(
    *,
    raw_error: str | None = None,
    has_test_failures: bool = False,
    structured_kind: ExecutionErrorKind | None = None,
) -> ExecutionErrorKind:
    """Map available execution signals to a closed kind (I-EX-03/04; no LLM)."""
    if structured_kind is not None:
        return structured_kind
    if has_test_failures:
        return ExecutionErrorKind.TEST_FAILURE

    text = (raw_error or "").strip()
    if not text:
        return ExecutionErrorKind.UNKNOWN_SAFE

    lowered = text.lower()
    if "syntaxerror" in lowered or "syntax error" in lowered:
        return ExecutionErrorKind.SYNTAX
    if (
        "operationalerror" in lowered
        or "programmingerror" in lowered
        or "sql syntax" in lowered
        or "sqlite" in lowered
    ):
        return ExecutionErrorKind.SQL
    if any(
        marker in text
        for marker in (
            "NameError",
            "TypeError",
            "ValueError",
            "IndexError",
            "KeyError",
            "AttributeError",
            "ZeroDivisionError",
            "RuntimeError",
            "RecursionError",
        )
    ) or "runtime error" in lowered:
        return ExecutionErrorKind.RUNTIME
    return ExecutionErrorKind.UNKNOWN_SAFE


class ExecutionErrorPresentation(BaseModel):
    """Ephemeral candidate-safe execution error projection (EC-EX-01)."""

    kind: ExecutionErrorKind
    candidate_message: str = Field(..., min_length=1)
    detail_lines: tuple[str, ...] = ()
    shows_traceback: Literal[False] = False

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_kind(
        cls,
        kind: ExecutionErrorKind,
        *,
        detail_lines: tuple[str, ...] = (),
    ) -> ExecutionErrorPresentation:
        """Build from §5.3 catalog (DM-V-EX-02/03); traceback always False."""
        entry = get_execution_error_entry(kind)
        return cls(
            kind=kind,
            candidate_message=entry.candidate_message,
            detail_lines=detail_lines,
            shows_traceback=False,
        )

    @model_validator(mode="after")
    def _validate_dm_v_ex(self) -> ExecutionErrorPresentation:
        if self.shows_traceback is not False:
            raise ValueError("DM-V-EX-01: shows_traceback must be False.")

        entry = get_execution_error_entry(self.kind)
        if self.candidate_message != entry.candidate_message:
            raise ValueError(
                f"DM-V-EX-02/03: candidate_message must equal §5.3 catalog text "
                f"for kind={self.kind!r}."
            )

        if _is_unsafe_candidate_text(self.candidate_message):
            raise ValueError(
                "I-EX-01: candidate_message must not include traceback, paths, "
                "or exception class names."
            )
        for line in self.detail_lines:
            if not line or not str(line).strip():
                raise ValueError("detail_lines entries must be non-empty.")
            if _is_unsafe_candidate_text(line):
                raise ValueError(
                    "I-EX-01: detail_lines must not include traceback, paths, "
                    "or exception class names."
                )

        return self


def project_execution_error(
    *,
    structured_kind: ExecutionErrorKind | None = None,
    raw_error: str | None = None,
    has_test_failures: bool = False,
    detail_lines: tuple[str, ...] = (),
) -> ExecutionErrorPresentation:
    """
    Project execution/feedback signals into ExecutionErrorPresentation.

    Presentation-only (I-EX-03): does not write FeedbackBundle; does not call LLM.
    Raw error text is never emitted as candidate_message (I-EX-04).
    """
    kind = classify_execution_error_kind(
        raw_error=raw_error,
        has_test_failures=has_test_failures,
        structured_kind=structured_kind,
    )
    safe_details = detail_lines if kind is ExecutionErrorKind.TEST_FAILURE else ()
    return ExecutionErrorPresentation.from_kind(kind, detail_lines=safe_details)
