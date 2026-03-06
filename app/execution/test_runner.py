# app/execution/test_runner.py

import ast
import inspect
import traceback
import logging
from typing import Any

from domain.contracts.test_case import TestCase


logger = logging.getLogger(__name__)


class TestRunner:

    def run_tests(
        self,
        local_env: dict[str, Any],
        test_cases: list[TestCase],
    ) -> tuple[int, int]:

        passed = 0
        total = len(test_cases)

        candidate_function = self._extract_candidate_function(local_env)

        if not candidate_function:
            logger.error("No candidate function found in execution environment")
            return 0, total

        logger.info(f"Testing function: {candidate_function.__name__}")

        for test in test_cases:

            try:

                parsed_input = self._parse_input(test.input)

                logger.debug(f"Test input: {parsed_input}")

                # support multi-argument functions
                if isinstance(parsed_input, tuple):
                    result = candidate_function(*parsed_input)
                else:
                    result = candidate_function(parsed_input)

                logger.debug(f"Result: {result}")

                if str(result) == test.expected_output:
                    passed += 1

            except Exception:

                logger.error(
                    f"Test failed for input {test.input}\n{traceback.format_exc()}"
                )

        return passed, total

    # =========================================================
    # FUNCTION EXTRACTION
    # =========================================================

    def _extract_candidate_function(self, local_env: dict[str, Any]):

        functions = [
            v
            for v in local_env.values()
            if inspect.isfunction(v) and v.__module__ == "__main__"
        ]

        if not functions:
            return None

        # assume first defined function is the candidate solution
        return functions[0]

    # =========================================================
    # INPUT PARSER
    # =========================================================

    def _parse_input(self, value: str):

        try:
            return ast.literal_eval(value)
        except Exception:
            return value
