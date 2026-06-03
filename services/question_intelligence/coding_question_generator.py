# services/question_intelligence/coding_question_generator.py

import json
from typing import List

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from app.ports.llm_port import LLMPort

from app.core.logger import get_logger

logger = get_logger(__name__)


# =========================================================
# DTOs (Structured Output)
# =========================================================


class GeneratedTestCase(BaseModel):
    args: List = Field(default_factory=list)
    expected: object


class GeneratedCodingQuestion(BaseModel):
    prompt: str
    coding_spec: CodingSpec
    visible_tests: List[GeneratedTestCase]


# =========================================================
# Generator
# =========================================================


class CodingQuestionGenerator:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # -----------------------------------------------------

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int = 1,
    ) -> List[GeneratedCodingQuestion]:

        prompt = self._build_generation_prompt(
            role=role.value,
            level=level.value,
            n=n,
        )

        response = self._llm.invoke(prompt)

        try:
            return self._parse_llm_response(response.content)
        except ValueError as e:
            raise ValueError(str(e)) from e

    # -----------------------------------------------------

    def enrich_from_prompt(
        self,
        seed_prompt: str,
        role: RoleType,
        level: SeniorityLevel,
        provenance: QuestionProvenance | None = None,
    ) -> GeneratedCodingQuestion | None:

        _ = provenance

        prompt = self._build_enrichment_prompt(
            seed_prompt=seed_prompt,
            role=role.value,
            level=level.value,
        )

        try:
            response = self._llm.invoke(prompt)
            validated_items = self._parse_llm_response(response.content)
        except (ValueError, Exception) as e:
            logger.warning(f"[Coding enrich] Failed to parse enrichment response: {e}")
            return None

        if not validated_items:
            logger.warning("[Coding enrich] No coding questions after enrichment")
            return None

        return validated_items[0]

    # =========================================================
    # INTERNALS
    # =========================================================

    def _parse_llm_response(
        self,
        content: str,
    ) -> List[GeneratedCodingQuestion]:

        try:
            raw_data = json.loads(content)
        except Exception as e:
            raise ValueError(f"Invalid JSON from LLM: {e}") from e

        if not isinstance(raw_data, list):
            raise ValueError("LLM response must be a JSON array")

        validated_items: List[GeneratedCodingQuestion] = []

        for item in raw_data:
            try:
                validated = GeneratedCodingQuestion.model_validate(item)

                if not validated.visible_tests:
                    raise ValueError("Coding question must include at least one test case")

                validated_items.append(validated)

            except (ValidationError, ValueError) as e:
                raise ValueError(f"Invalid coding question structure: {e}") from e

        return validated_items

    def _build_generation_prompt(
        self,
        role: str,
        level: str,
        n: int,
    ) -> str:

        return f"""
You are a senior technical interviewer.

Generate {n} Python coding interview questions for a {level} {role}.

Each question MUST include:

1. A clear problem description
2. A strict function contract
3. At least 2 valid test cases

{self._json_output_contract()}

Rules:
- Function name MUST match coding_spec.entrypoint
- Parameters MUST match coding_spec.parameters
- The function signature MUST be clearly described in the prompt
- Avoid ambiguous descriptions
- No markdown
- Only valid JSON
"""

    def _build_enrichment_prompt(
        self,
        seed_prompt: str,
        role: str,
        level: str,
    ) -> str:

        return f"""
You are a senior technical interviewer.

Reframe the following interview seed into ONE Python coding problem
for a {level} {role} candidate.

Seed question:
{seed_prompt}

Each output item MUST include:

1. A clear and unambiguous problem description
2. A strict function contract
3. At least 2 valid test cases with JSON-serializable args and expected values

{self._json_output_contract()}

Rules:
- Function name MUST match coding_spec.entrypoint
- Parameters MUST match coding_spec.parameters
- The function signature MUST be clearly described in the prompt
- Use type "function" unless a class-based solution is clearly required
- Avoid ambiguous descriptions
- No markdown
- Only valid JSON
- Return exactly 1 question in the array

"""

    def _json_output_contract(self) -> str:

        return """
Return STRICT JSON array:

[
  {
    "prompt": "...",

    "coding_spec": {
      "type": "function",
      "entrypoint": "function_name",
      "parameters": ["param1", "param2"]
    },

    "visible_tests": [
      {
        "args": [...],
        "expected": ...
      }
    ]
  }
]
"""
