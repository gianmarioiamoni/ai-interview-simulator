# services/question_intelligence/coding_response_parser.py

import json
from typing import List

from pydantic import ValidationError

from app.ports.llm_port import LLMPort
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import QUESTION_GENERATION
from infrastructure.config.settings import settings

from services.question_intelligence.coding_llm_json_repair import repair_llm_json_text

from app.core.logger import get_logger

logger = get_logger(__name__)

MAX_INVALID_JSON_ATTEMPTS = settings.coding_json_retry_attempts
INVALID_JSON_PREFIX = "Invalid JSON from LLM:"


def _is_invalid_json_error(exc: ValueError) -> bool:
    return str(exc).startswith(INVALID_JSON_PREFIX)


class CodingResponseParser:
    """
    Invokes the LLM, parses its JSON response, and validates each
    GeneratedCodingQuestion structure.

    Retry logic is self-contained: invalid-JSON responses are retried
    up to MAX_INVALID_JSON_ATTEMPTS times.
    """

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def invoke_and_parse(
        self,
        prompt: str,
        log_prefix: str,
    ) -> list:
        """
        Call the LLM with *prompt*, parse the response, and return a list
        of GeneratedCodingQuestion objects.  Retries on invalid-JSON errors.
        """
        # Import here to avoid circular dependency at module load time.
        from services.question_intelligence.coding_question_generator import (
            GeneratedCodingQuestion,
        )

        for attempt in range(1, MAX_INVALID_JSON_ATTEMPTS + 1):

            with LLMOperationContext.scope(QUESTION_GENERATION):
                response = self._llm.invoke(prompt)

            try:
                return self._parse(response.content, GeneratedCodingQuestion)

            except ValueError as exc:

                if _is_invalid_json_error(exc):

                    if attempt < MAX_INVALID_JSON_ATTEMPTS:
                        logger.warning(
                            "%s Invalid JSON (attempt %d/%d), retrying: %s",
                            log_prefix,
                            attempt,
                            MAX_INVALID_JSON_ATTEMPTS,
                            exc,
                        )
                        continue

                    logger.warning(
                        "%s Invalid JSON after %d attempts: %s",
                        log_prefix,
                        MAX_INVALID_JSON_ATTEMPTS,
                        exc,
                    )
                    return []

                logger.warning(
                    "%s Parse/validation failed (no retry): %s",
                    log_prefix,
                    exc,
                )
                return []

        return []

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    def _parse(self, content: str, model_class) -> list:

        repaired = repair_llm_json_text(content)

        try:
            raw_data = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{INVALID_JSON_PREFIX} {exc}") from exc

        if not isinstance(raw_data, list):
            raise ValueError("LLM response must be a JSON array")

        validated_items = []

        for item in raw_data:
            try:
                validated = model_class.model_validate(item)

                if not validated.visible_tests:
                    raise ValueError(
                        "Coding question must include at least one test case"
                    )

                validated_items.append(validated)

            except (ValidationError, ValueError) as exc:
                raise ValueError(
                    f"Invalid coding question structure: {exc}"
                ) from exc

        return validated_items
