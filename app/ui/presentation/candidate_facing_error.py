# app/ui/presentation/candidate_facing_error.py
# EPIC-07 EC-CF-01 / Data Model §4.1 — CandidateFacingError (UI-layer; ephemeral).

from __future__ import annotations

import re

from pydantic import BaseModel, Field, model_validator

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.candidate_facing_error_catalog import (
    get_candidate_facing_error_entry,
)

_TRACEBACK_MARKER = "Traceback"
_PY_PATH_SEGMENT = re.compile(r"(?:^|[/\\])[^/\\]+\.py(?:$|[/\\:])")
_EXCEPTION_TYPE_NAME = re.compile(r"\b[A-Z][A-Za-z0-9_]*Error\b|\b[A-Z][A-Za-z0-9_]*Exception\b")


class CandidateFacingError(BaseModel):
    """Immutable candidate-safe failure message for one async boundary (EC-CF-01)."""

    boundary: AsyncBoundary
    message_key: str = Field(..., min_length=1)
    message_text: str = Field(..., min_length=1)
    is_retryable: bool = False
    correlation_token: str | None = None

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_catalog(
        cls,
        message_key: str,
        *,
        correlation_token: str | None = None,
    ) -> CandidateFacingError:
        """Build from §5.1 catalog (sole copy source; DM-V-CF-01)."""
        entry = get_candidate_facing_error_entry(message_key)
        return cls(
            boundary=entry.boundary,
            message_key=entry.message_key,
            message_text=entry.message_text,
            is_retryable=entry.is_retryable,
            correlation_token=correlation_token,
        )

    @model_validator(mode="after")
    def _validate_catalog_and_safety(self) -> CandidateFacingError:
        entry = get_candidate_facing_error_entry(self.message_key)

        if self.boundary != entry.boundary:
            raise ValueError(
                f"DM-V-CF-01: boundary={self.boundary!r} does not match "
                f"catalog boundary={entry.boundary!r} for message_key={self.message_key!r}."
            )
        if self.message_text != entry.message_text:
            raise ValueError(
                f"DM-V-CF-01: message_text must equal catalog text for "
                f"message_key={self.message_key!r}."
            )
        if self.is_retryable != entry.is_retryable:
            raise ValueError(
                f"DM-V-CF-01: is_retryable must equal catalog value for "
                f"message_key={self.message_key!r}."
            )

        if _TRACEBACK_MARKER in self.message_text or _PY_PATH_SEGMENT.search(self.message_text):
            raise ValueError("I-CF-01: message_text must not contain traceback markers or file paths.")
        if _EXCEPTION_TYPE_NAME.search(self.message_text):
            raise ValueError("I-CF-01: message_text must not contain exception type names.")

        token = self.correlation_token
        if token is not None:
            if not token:
                raise ValueError("correlation_token, when set, must be non-empty.")
            if _TRACEBACK_MARKER in token or ".py" in token:
                raise ValueError(
                    "correlation_token must not embed Traceback markers or .py path segments."
                )

        return self
