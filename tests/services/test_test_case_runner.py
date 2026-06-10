# tests/services/test_test_case_runner.py

from domain.contracts.execution.coding_test_case import CodingTestCase
from services.coding_engine.test_case_runner import TestCaseRunner


USER_CODE = """
def solution(x):
    return x * 2
"""


def test_build_harness_contains_markers_and_runner():

    runner = TestCaseRunner()

    visible_tests = [
        CodingTestCase(args=[2], expected=4),
        CodingTestCase(args=[3], expected=6),
    ]

    hidden_tests = [
        CodingTestCase(args=[4], expected=8),
    ]

    harness = runner.build_harness(
        user_code=USER_CODE,
        visible_tests=visible_tests,
        hidden_tests=hidden_tests,
        function_name="solution",
        coding_spec=None,
    )

    assert "__RESULT__" in harness
    assert "__run_tests()" in harness
    assert "solution" in harness


def test_build_harness_embeds_user_code_and_test_data():

    runner = TestCaseRunner()

    harness = runner.build_harness(
        user_code=USER_CODE,
        visible_tests=[CodingTestCase(args=[21], expected=42)],
        hidden_tests=[],
        function_name="solution",
        coding_spec=None,
    )

    assert "return x * 2" in harness
    assert "21" in harness
    assert "42" in harness


def test_build_harness_is_executable_python():

    import ast

    runner = TestCaseRunner()

    harness = runner.build_harness(
        user_code=USER_CODE,
        visible_tests=[CodingTestCase(args=[2], expected=4)],
        hidden_tests=[CodingTestCase(args=[3], expected=6)],
        function_name="solution",
        coding_spec=None,
    )

    # must be syntactically valid python
    ast.parse(harness)


def test_build_harness_with_no_tests_still_renders():

    runner = TestCaseRunner()

    harness = runner.build_harness(
        user_code=USER_CODE,
        visible_tests=[],
        hidden_tests=[],
        function_name="solution",
        coding_spec=None,
    )

    assert "__run_tests()" in harness
