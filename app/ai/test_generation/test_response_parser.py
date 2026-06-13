# app/ai/test_generation/test_response_parser.py

"""
Owns LLM invocation, JSON repair, schema validation, and CodingTestCase
construction for test generation.

Mirrors the role of CodingResponseParser / SQLResponseParser in the
question-intelligence subsystem.
"""

import json
from typing import List

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.execution.coding_test_case import CodingTestCase
from app.ports.llm_port import LLMPort
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import QUESTION_GENERATION
from app.core.logger import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# Internal DTO — stays here so AITestGenerator does not need to know
# about the intermediate representation.
# ------------------------------------------------------------------

class _GeneratedTestCase(BaseModel):
    args: list = Field(default_factory=list)
    expected: object


class TestResponseParser:
    """
    Invokes the LLM, repairs malformed JSON, validates the response
    schema, and returns a list of CodingTestCase domain objects.

    Mirrors CodingResponseParser.invoke_and_parse().
    """

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def invoke_and_parse(
        self,
        prompt: str,
        spec: CodingSpec,
        retry: bool = False,
    ) -> List[CodingTestCase]:
        """
        Call the LLM with *prompt* and return validated CodingTestCase objects.

        When *retry* is True, appends a JSON-only instruction to the prompt
        to harden the response on the last attempt.
        """
        full_prompt = prompt
        if retry:
            full_prompt += "\n\nIMPORTANT: Return ONLY valid JSON."

        with LLMOperationContext.scope(QUESTION_GENERATION):
            response = self._llm.invoke(full_prompt)

        content = response.content or ""
        raw_data = self._safe_json_parse(content)

        if not isinstance(raw_data, list):
            logger.warning("LLM output is not a list")
            return []

        tests: List[CodingTestCase] = []
        for item in raw_data:
            try:
                validated = _GeneratedTestCase.model_validate(item)
                tests.append(
                    CodingTestCase(
                        args=validated.args,
                        kwargs={},
                        expected=validated.expected,
                    )
                )
            except ValidationError:
                continue

        return self._validate_against_spec(tests, spec)

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_json_parse(content: str) -> object:
        try:
            return json.loads(content)
        except Exception:
            pass

        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(content[start: end + 1])
            except Exception:
                pass

        content = content.replace("```json", "").replace("```", "")
        try:
            return json.loads(content)
        except Exception:
            logger.warning("Failed to parse LLM JSON output")
            return []

    @staticmethod
    def _validate_against_spec(
        tests: List[CodingTestCase],
        spec: CodingSpec,
    ) -> List[CodingTestCase]:
        expected_len = len(spec.parameters)
        return [
            t for t in tests
            if len(t.args) == expected_len and not any(arg is None for arg in t.args)
        ]
