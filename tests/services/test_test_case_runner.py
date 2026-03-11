from domain.contracts.test_case import TestCase
from services.coding_engine.test_case_runner import TestCaseRunner


def test_build_harness_contains_marker():
    runner = TestCaseRunner()

    user_code = """
def solution(x):
    return x * 2
"""

    visible_tests = [
        TestCase(input=[2], expected_output=4),
        TestCase(input=[3], expected_output=6),
    ]

    hidden_tests = [
        TestCase(input=[4], expected_output=8),
        TestCase(input=[5], expected_output=10),
    ]

    harness = runner.build_harness(
        user_code=user_code,
        visible_tests=visible_tests,
        hidden_tests=hidden_tests,
    )

    assert "__RESULT__" in harness
    assert "solution(2)" in harness
    assert "solution(3)" in harness
    assert "passed += 1" in harness
