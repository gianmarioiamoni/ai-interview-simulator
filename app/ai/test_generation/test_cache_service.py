# app/ai/test_generation/test_cache_service.py

import json
import hashlib
from pathlib import Path
from typing import List, Optional

from domain.contracts.question.question import Question
from domain.contracts.execution.coding_test_case import CodingTestCase


class TestCacheService:
    # Persistent cache for AI-generated tests.
    # Supports backward compatibility with legacy TestCase format.

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
    ) -> Optional[List[CodingTestCase]]:

        key = self._build_cache_key(question, num_tests)

        if key not in self._cache:
            return None

        cached = self._cache[key]

        results: List[CodingTestCase] = []

        for item in cached:

            # -----------------------------------------------------
            # NEW FORMAT (preferred)
            # -----------------------------------------------------

            if "args" in item:
                results.append(
                    CodingTestCase(
                        args=item.get("args", []),
                        kwargs=item.get("kwargs", {}),
                        expected=item.get("expected"),
                    )
                )

            # -----------------------------------------------------
            # LEGACY FORMAT (fallback)
            # -----------------------------------------------------

            elif "input" in item:
                results.append(
                    CodingTestCase(
                        args=[item.get("input")],
                        kwargs={},
                        expected=item.get("expected_output"),
                    )
                )

        return results

    def store_tests(
        self,
        question: Question,
        num_tests: int,
        tests: List[CodingTestCase],
    ) -> None:

        key = self._build_cache_key(question, num_tests)

        # ---------------------------------------------------------
        # STORE ONLY NEW FORMAT
        # ---------------------------------------------------------

        self._cache[key] = [
            {
                "args": t.args,
                "kwargs": t.kwargs,
                "expected": t.expected,
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
