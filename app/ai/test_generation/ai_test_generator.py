# app/ai/test_generation/ai_test_generator.py

import json
import re
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

You MUST return valid JSON only.
No explanations.
No markdown.

Format:
[
  {{"input": "...", "expected_output": "..."}}
]
"""

        response = self._llm.invoke(prompt)

        content = response.content.strip()
        # ---------------------------------------------------------
        # Remove markdown code blocks if present
        # ---------------------------------------------------------

        if content.startswith("```"):
            content = content.split("```")[1]
            content = content.replace("json", "").strip()

        # ---------------------------------------------------------
        # Parse JSON
        # ---------------------------------------------------------
        try:
            tests_json = _safe_parse_tests(content)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return []

        tests: List[TestCase] = []

        for t in tests_json:

            if not isinstance(t, dict):
                continue

            if "input" not in t or "expected_output" not in t:
                continue

            tests.append(
                TestCase(
                    input=str(t["input"]),
                    expected_output=str(t["expected_output"]),
                )
            )

        return tests


def _safe_parse_tests(content: str):

    content = content.strip()

    # remove markdown blocks
    if content.startswith("```"):
        content = re.sub(r"```.*?\n", "", content)
        content = content.replace("```", "")

    # extract JSON array
    match = re.search(r"\[.*\]", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON array found in LLM output")

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid JSON from LLM: {e}")
