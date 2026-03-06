# app/ai/test_generation/ai_test_generator.py

import json
import hashlib
from pathlib import Path
from typing import List

from domain.contracts.test_case import TestCase
from domain.contracts.question import Question

from infrastructure.llm.llm_factory import get_llm


class AITestGenerator:
    # Generates hidden edge-case tests using an LLM.
    # Results are cached to avoid repeated LLM calls.

    CACHE_FILE = Path("data/ai_test_cache.json")

    def __init__(self):

        self._llm = get_llm()
        self._cache = self._load_cache()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def generate_tests(
        self,
        question: Question,
        num_tests: int = 3,
    ) -> List[TestCase]:

        cache_key = self._build_cache_key(question, num_tests)

        # ---------------------------------------------------------
        # Cache hit
        # ---------------------------------------------------------

        if cache_key in self._cache:

            cached = self._cache[cache_key]

            return [
                TestCase(
                    input=t["input"],
                    expected_output=t["expected_output"],
                )
                for t in cached
            ]

        # ---------------------------------------------------------
        # Cache miss → call LLM
        # ---------------------------------------------------------

        tests = self._generate_with_llm(question, num_tests)

        # store cache
        self._cache[cache_key] = [
            {
                "input": t.input,
                "expected_output": t.expected_output,
            }
            for t in tests
        ]

        self._save_cache()

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
Generate {num_tests} edge-case test cases for this coding problem.

Problem:
{question.prompt}

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

    # =========================================================
    # CACHE MANAGEMENT
    # =========================================================

    def _build_cache_key(
        self,
        question: Question,
        num_tests: int,
    ) -> str:

        payload = f"{question.id}:{question.prompt}:{num_tests}"

        return hashlib.sha256(payload.encode()).hexdigest()

    def _load_cache(self) -> dict:

        if not self.CACHE_FILE.exists():
            return {}

        try:

            with open(self.CACHE_FILE, "r") as f:
                return json.load(f)

        except Exception:
            return {}

    def _save_cache(self) -> None:

        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(self.CACHE_FILE, "w") as f:
            json.dump(self._cache, f, indent=2)
