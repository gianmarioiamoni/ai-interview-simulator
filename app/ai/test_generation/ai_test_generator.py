# app/ai/test_generation/ai_test_generator.py

import json
from typing import List

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.question.question import Question
from domain.contracts.execution.coding_spec import CodingSpec

from app.ports.llm_port import LLMPort
from app.ai.test_generation.test_cache_service import TestCacheService
from app.ai.test_generation.test_diversity_filter import TestDiversityFilter


# =========================================================
# DTO (Structured Output)
# =========================================================

class GeneratedTestCase(BaseModel):
    args: list = Field(default_factory=list)
    expected: object


# =========================================================
# GENERATOR
# =========================================================

class AITestGenerator:

    def __init__(self, llm: LLMPort):
        self._llm = llm
        self._cache = TestCacheService()
        self._diversity_filter = TestDiversityFilter()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def generate_tests(
        self,
        question: Question,
        num_tests: int = 3,
    ) -> List[CodingTestCase]:

        if not question.coding_spec:
            raise ValueError("CodingSpec required for test generation")

        # ---------------------------------------------------------
        # Cache lookup
        # ---------------------------------------------------------

        cached = self._cache.get_tests(question, num_tests)

        if cached:
            return cached

        # ---------------------------------------------------------
        # LLM generation
        # ---------------------------------------------------------

        tests = self._generate_with_llm(
            question,
            num_tests * 2,
        )

        # ---------------------------------------------------------
        # VALIDATION vs CodingSpec (STEP 4.3)
        # ---------------------------------------------------------

        tests = self._validate_tests_against_spec(
            tests,
            question.coding_spec,
        )

        # ---------------------------------------------------------
        # Diversity filter
        # ---------------------------------------------------------

        tests = self._diversity_filter.filter(
            tests,
            num_tests,
        )

        # ---------------------------------------------------------
        # Store cache
        # ---------------------------------------------------------

        self._cache.store_tests(
            question,
            num_tests,
            tests,
        )

        return tests

    # =========================================================
    # LLM GENERATION
    # =========================================================

    def _generate_with_llm(
        self,
        question: Question,
        num_tests: int,
    ) -> List[CodingTestCase]:

        spec = question.coding_spec

        prompt = self._build_prompt(
            question.prompt,
            spec,
            num_tests,
        )

        response = self._llm.invoke(prompt)

        try:
            raw_data = json.loads(response.content)
        except Exception as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")

        tests: List[CodingTestCase] = []

        for item in raw_data:

            try:
                validated = GeneratedTestCase.model_validate(item)

                tests.append(
                    CodingTestCase(
                        args=validated.args,
                        expected=validated.expected,
                    )
                )

            except ValidationError:
                continue

        return tests

    # =========================================================
    # VALIDATION (STEP 4.3)
    # =========================================================

    def _validate_tests_against_spec(
        self,
        tests: List[CodingTestCase],
        spec: CodingSpec,
    ) -> List[CodingTestCase]:

        expected_len = len(spec.parameters)

        valid = []

        for t in tests:

            if len(t.args) == expected_len:
                valid.append(t)

        if not valid:
            raise ValueError(
                f"Invalid test args length. Expected args length to be {expected_len}"
            )

        return valid

    # =========================================================
    # PROMPT
    # =========================================================

    def _build_prompt(
        self,
        prompt: str,
        spec: CodingSpec,
        num_tests: int,
    ) -> str:

        return f"""
You are an expert Python tester.

Given this coding problem:

{prompt}

Function contract:

- Entrypoint: {spec.entrypoint}
- Parameters: {spec.parameters}

Generate {num_tests} test cases.

Return STRICT JSON:

[
  {{
    "args": [...],
    "expected": ...
  }}
]

Function parameters:
{spec.parameters}

CRITICAL RULE:
- args length MUST be exactly {len(spec.parameters)}
- Example:
  If parameters = ["x"], then:
    args = [value]
  NOT:
    args = [v1, v2, v3]

Each element in args corresponds to ONE parameter.

IMPORTANT:
- If a parameter is a list, it must be passed as a SINGLE element
- Example:
  parameters = ["nums"]
  args = [[1,2,3]]

  If a parameter is a dictionary, it must be passed as a SINGLE element
  Example:
  parameters = ["person"]
  args = [{"name": "John", "age": 30}]

  If a parameter is a tuple, it must be passed as a SINGLE element
  Example:
  parameters = ["point"]
  args = [(1,2)]


Rules:
- args MUST match the parameter order exactly
- expected MUST be correct
- Include edge cases:
  - empty input
  - single element
  - duplicates
  - boundary values
- No explanations
- No markdown
- Only JSON
"""
