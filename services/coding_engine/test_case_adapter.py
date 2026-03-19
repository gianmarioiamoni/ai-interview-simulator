# services/coding_engine/test_case_adapter.py

import ast
from typing import List

from domain.contracts.test_case import TestCase
from domain.contracts.coding_test_case import CodingTestCase


class TestCaseAdapter:

    def to_coding_test_cases(
        self,
        test_cases: List[TestCase],
    ) -> List[CodingTestCase]:

        if not test_cases:
            return []

        # already coding test cases
        if isinstance(test_cases[0], CodingTestCase):
            return test_cases
        
        converted: List[CodingTestCase] = []

        for t in test_cases:

            args = []
            kwargs = {}

            # -------------------------
            # Parse input
            # -------------------------
            try:
                parsed_input = ast.literal_eval(t.input)

                if isinstance(parsed_input, tuple):
                    args = list(parsed_input)

                elif isinstance(parsed_input, list):
                    args = parsed_input

                elif isinstance(parsed_input, dict):
                    kwargs = parsed_input

                else:
                    args = [parsed_input]

            except Exception:
                # fallback: pass raw string
                args = [t.input]

            # -------------------------
            # Parse expected
            # -------------------------
            try:
                expected = ast.literal_eval(t.expected_output)
            except Exception:
                expected = t.expected_output

            converted.append(
                CodingTestCase(
                    args=args,
                    kwargs=kwargs,
                    expected=expected,
                )
            )

        return converted
