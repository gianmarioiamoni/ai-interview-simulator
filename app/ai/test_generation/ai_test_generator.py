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
from app.prompts.prompt_loader import PromptLoader


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

        template = PromptLoader.load("test_generation/test_generation_prompt.txt")
        parameters = json.dumps(spec.parameters)

        prompt = template.format(
            problem=prompt,
            entrypoint=spec.entrypoint,
            parameters=parameters,
            num_tests=num_tests,
            param_count=len(parameters),
        )

        return prompt

