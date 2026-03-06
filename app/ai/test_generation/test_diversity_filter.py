# app/ai/test_generation/test_diversity_filter.py

from domain.contracts.test_case import TestCase


class TestDiversityFilter:
    # Removes duplicated or overly similar test cases.

    def filter(
        self,
        tests: list[TestCase],
        max_tests: int,
    ) -> list[TestCase]:

        unique_inputs = set()

        filtered = []

        for test in tests:

            if test.input in unique_inputs:
                continue

            unique_inputs.add(test.input)

            filtered.append(test)

            if len(filtered) >= max_tests:
                break

        return filtered
