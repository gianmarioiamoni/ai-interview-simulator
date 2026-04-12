# app/ai/test_generation/test_diversity_filter.py

from typing import List

from domain.contracts.execution.coding_test_case import CodingTestCase


class TestDiversityFilter:

    def filter(
        self,
        tests: List[CodingTestCase],
        max_tests: int,
    ) -> List[CodingTestCase]:

        unique_inputs = set()
        filtered = []

        for test in tests:

            # ---------------------------------------------------------
            # BUILD SIGNATURE (args + kwargs)
            # ---------------------------------------------------------

            key = self._build_key(test)

            if key in unique_inputs:
                continue

            unique_inputs.add(key)
            filtered.append(test)

            if len(filtered) >= max_tests:
                break

        return filtered

    # =========================================================
    # INTERNAL
    # =========================================================

    def _build_key(self, test: CodingTestCase) -> str:
        # Create a hashable representation of the test input.

        args_part = str(test.args)
        kwargs_part = str(sorted(test.kwargs.items())) if test.kwargs else ""

        return f"{args_part}|{kwargs_part}"
