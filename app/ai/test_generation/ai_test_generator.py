# app/ai/test_generation/ai_test_generator.py

import json
from typing import List

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.question.question import Question
from domain.contracts.execution.coding_spec import CodingSpec

from infrastructure.llm.llm_factory import get_llm

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

    def __init__(self):

        self._llm = get_llm()
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

        self._validate_tests_against_spec(
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
    ) -> None:

        expected_len = len(spec.parameters)

        for t in tests:

            if len(t.args) != expected_len:
                raise ValueError(
                    f"Invalid test args length. Expected {expected_len}, got {len(t.args)}"
                )

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
