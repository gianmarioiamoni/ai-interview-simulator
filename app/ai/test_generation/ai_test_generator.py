# app/ai/test_generation/ai_test_generator.py

from typing import List

from domain.contracts.test_case import TestCase
from domain.contracts.question import Question

from infrastructure.llm.llm_factory import get_llm

from app.ai.test_generation.test_cache_service import TestCacheService
from app.ai.test_generation.test_diversity_filter import TestDiversityFilter


class AITestGenerator:
    # Generates hidden edge-case tests using an LLM.
    # Pipeline:
    # Question
    #   ↓
    # Cache lookup
    #   ↓
    # LLM generation
    #   ↓
    # Diversity filter
    #   ↓
    # Cache store

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
    ) -> List[TestCase]:

        # ---------------------------------------------------------
        # Cache lookup
        # ---------------------------------------------------------

        cached = self._cache.get_tests(question, num_tests)

        if cached:
            return cached

        # ---------------------------------------------------------
        # LLM generation
        # ---------------------------------------------------------

        tests = self._generate_with_llm(question, num_tests * 2)

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
    ) -> List[TestCase]:

        prompt = f"""
Generate {num_tests} diverse edge-case test cases for this coding problem.

Problem:
{question.prompt}

Focus on edge cases such as:

- empty input
- single element
- repeated values
- unusual characters
- boundary values
- very large input

Return JSON array only:

[
  {{"input": "...", "expected_output": "..."}}
]
"""

        response = self._llm.invoke(prompt)

        tests_json = response.json()

        return [
            TestCase(
                input=t["input"],
                expected_output=t["expected_output"],
            )
            for t in tests_json
        ]
