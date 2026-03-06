# app/ai/test_generation/test_cache_service.py

import json
import hashlib
from pathlib import Path
from typing import List

from domain.contracts.question import Question
from domain.contracts.test_case import TestCase


class TestCacheService:
    # Persistent cache for AI-generated tests.
    # Prevents repeated LLM calls for the same question.

    CACHE_FILE = Path("data/ai_test_cache.json")

    def __init__(self):

        self._cache = self._load_cache()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def get_tests(
        self,
        question: Question,
        num_tests: int,
    ) -> List[TestCase] | None:

        key = self._build_cache_key(question, num_tests)

        if key not in self._cache:
            return None

        cached = self._cache[key]

        return [
            TestCase(
                input=t["input"],
                expected_output=t["expected_output"],
            )
            for t in cached
        ]

    def store_tests(
        self,
        question: Question,
        num_tests: int,
        tests: List[TestCase],
    ) -> None:

        key = self._build_cache_key(question, num_tests)

        self._cache[key] = [
            {
                "input": t.input,
                "expected_output": t.expected_output,
            }
            for t in tests
        ]

        self._save_cache()

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
