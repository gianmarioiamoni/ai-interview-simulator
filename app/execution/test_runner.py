# app/execution/test_runner.py

import traceback
from typing import Any

from domain.contracts.test_case import TestCase


class TestRunner:

    def run_tests(self, local_env: dict[str, Any], test_cases: list[TestCase]) -> tuple[int, int]:

        passed = 0
        total = len(test_cases)

        for test in test_cases:

            try:

                func = list(local_env.values())[0]

                result = func(test.input)

                if str(result) == test.expected_output:
                    passed += 1

            except Exception:
                traceback.print_exc()

        return passed, total
