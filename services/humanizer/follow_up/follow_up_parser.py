# services/humanizer/follow_up/follow_up_parser.py
#
# ADR-019: STRICT parser.
# Rules:
#   - Unknown fields           → FollowUpParseError (contract violation)
#   - Missing required fields  → FollowUpParseError
#   - Wrong types              → FollowUpParseError
#   - Invalid JSON             → FollowUpParseError
#   - Markdown fences          → FollowUpParseError
#   - Extra surrounding text   → FollowUpParseError
#   - No silent fallbacks      → caller is responsible for retry/fallback

import json
import re

from pydantic import ValidationError

from services.humanizer.follow_up.follow_up_output import FollowUpOutput
from services.humanizer.follow_up.follow_up_parse_error import FollowUpParseError
from services.humanizer.guards.follow_up_guard import FollowUpGuard
from services.humanizer.guards.follow_up_guard_result import FollowUpGuardResult
from infrastructure.config.settings import Settings

# Required top-level keys — exact set, no more, no less
_REQUIRED_KEYS: frozenset[str] = frozenset({
    "follow_up_question",
    "reasoning",
    "topic_anchor",
    "confidence",
})

_MARKDOWN_FENCE_RE = re.compile(r"```")


class FollowUpParser:
    """STRICT parser: LLM response → FollowUpOutput + FollowUpGuardResult.

    Parsing and guard validation are two distinct responsibilities;
    this class owns ONLY parsing. Guard is injected.
    """

    def __init__(self, guard: FollowUpGuard | None = None) -> None:
        self._guard = guard or FollowUpGuard()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(
        self,
        raw_response: str,
        *,
        previous_answer: str,
        question_prompt: str,
        question_area: str,
        settings: Settings,
    ) -> tuple[FollowUpOutput, FollowUpGuardResult]:
        """Parse raw LLM response into (FollowUpOutput, FollowUpGuardResult).

        Raises:
            FollowUpParseError: on any structural, schema, or contract violation.
        """
        output = self._strict_parse(raw_response)
        guard_result = self._guard.validate(
            follow_up_text=output.follow_up_question,
            previous_answer=previous_answer,
            question_prompt=question_prompt,
            question_area=question_area,
            settings=settings,
        )
        return output, guard_result

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _strict_parse(self, raw: str) -> FollowUpOutput:
        self._reject_if_markdown_fence(raw)
        self._reject_if_extra_text(raw)
        payload = self._parse_json(raw)
        self._validate_exact_keys(payload, raw)
        return self._validate_schema(payload, raw)

    def _reject_if_markdown_fence(self, raw: str) -> None:
        if _MARKDOWN_FENCE_RE.search(raw):
            raise FollowUpParseError(
                "STRICT:markdown_fence — response contains ``` fences", raw
            )

    def _reject_if_extra_text(self, raw: str) -> None:
        stripped = raw.strip()
        if not stripped.startswith("{"):
            raise FollowUpParseError(
                "STRICT:extra_text — response does not start with '{'", raw
            )
        if not stripped.endswith("}"):
            raise FollowUpParseError(
                "STRICT:extra_text — response does not end with '}'", raw
            )

    def _parse_json(self, raw: str) -> dict:  # type: ignore[type-arg]
        try:
            payload = json.loads(raw.strip())
        except json.JSONDecodeError as exc:
            raise FollowUpParseError(
                f"STRICT:invalid_json — {exc.msg}", raw
            ) from exc
        if not isinstance(payload, dict):
            raise FollowUpParseError(
                "STRICT:not_object — JSON root must be an object", raw
            )
        return payload

    def _validate_exact_keys(self, payload: dict, raw: str) -> None:  # type: ignore[type-arg]
        present = frozenset(payload.keys())
        missing = _REQUIRED_KEYS - present
        unknown = present - _REQUIRED_KEYS
        if missing:
            raise FollowUpParseError(
                f"STRICT:missing_fields — {sorted(missing)}", raw
            )
        if unknown:
            raise FollowUpParseError(
                f"STRICT:unknown_fields — {sorted(unknown)}", raw
            )

    def _validate_schema(self, payload: dict, raw: str) -> FollowUpOutput:  # type: ignore[type-arg]
        try:
            return FollowUpOutput.model_validate(payload)
        except ValidationError as exc:
            raise FollowUpParseError(
                f"STRICT:schema_violation — {exc}", raw
            ) from exc
