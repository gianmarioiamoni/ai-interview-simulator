from domain.contracts.coding_test_case import CodingTestCase
from services.coding_engine.test_case_runner import TestCaseRunner


def test_build_harness_contains_marker():
    runner = TestCaseRunner()

    user_code = """
def solution(x):
    return x * 2
"""

    test_cases = [
        CodingTestCase(args=[2], expected=4),
        CodingTestCase(args=[3], expected=6),
    ]

    harness = runner.build_harness(
        user_code=user_code,
        function_name="solution",
        test_cases=test_cases,
    )

    assert "__RESULT__" in harness
    assert "solution(2)" in harness
    assert "solution(3)" in harness
    assert "passed += 1" in harness
