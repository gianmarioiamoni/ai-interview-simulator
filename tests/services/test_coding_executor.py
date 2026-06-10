# tests/services/test_coding_executor.py

from unittest.mock import MagicMock

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.execution_result import (
    ExecutionStatus,
    ExecutionType,
)
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import (
    Question,
    QuestionDifficulty,
    QuestionType,
)
from services.coding_engine.coding_executor import CodingExecutor


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


def build_coding_question(
    *,
    visible_tests=None,
    hidden_tests=None,
    function_name: str = "solution",
) -> Question:

    return Question(
        id="q1",
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt="Implement solution(x) returning x * 2.",
        difficulty=QuestionDifficulty.MEDIUM,
        visible_tests=visible_tests or [],
        hidden_tests=hidden_tests or [],
        function_name=function_name,
    )


def build_raw_output(
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
    execution_time_ms: int = 10,
    timeout: bool = False,
):
    return type(
        "Raw",
        (),
        {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": execution_time_ms,
            "timeout": timeout,
        },
    )()


VALID_CODE = """
def solution(x):
    return x * 2
"""


# ---------------------------------------------------------
# SUCCESSFUL EXECUTION
# ---------------------------------------------------------


def test_successful_execution():

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[
            CodingTestCase(args=[2], expected=4),
            CodingTestCase(args=[3], expected=6),
        ],
    )

    result = executor.execute(question, VALID_CODE)

    assert result.success is True
    assert result.status == ExecutionStatus.SUCCESS
    assert result.execution_type == ExecutionType.CODING
    assert result.passed_tests == 2
    assert result.total_tests == 2
    assert result.question_id == "q1"


def test_successful_execution_reports_structured_test_results():

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[CodingTestCase(args=[2], expected=4)],
    )

    result = executor.execute(question, VALID_CODE)

    assert result.success is True
    assert len(result.test_results) == result.total_tests


def test_hidden_tests_are_adapted_and_counted():

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[CodingTestCase(args=[2], expected=4)],
        hidden_tests=[
            CodingTestCase(args=[4], expected=8),
            CodingTestCase(args=[5], expected=10),
        ],
    )

    result = executor.execute(question, VALID_CODE)

    assert result.success is True
    assert result.total_tests == 3
    assert result.passed_tests == 3


# ---------------------------------------------------------
# EXECUTION FAILURES
# ---------------------------------------------------------


def test_failed_test_execution():

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[
            CodingTestCase(args=[2], expected=4),
            CodingTestCase(args=[3], expected=7),  # wrong expectation
        ],
    )

    result = executor.execute(question, VALID_CODE)

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS
    assert result.passed_tests == 1
    assert result.total_tests == 2


def test_function_name_mismatch_resolves_via_fallback():
    # The callable resolver falls back to the single defined function
    # when the declared function_name is missing from the submission.

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[CodingTestCase(args=[2], expected=4)],
        function_name="expected_name",
    )

    result = executor.execute(question, VALID_CODE)

    assert result.success is True
    assert result.passed_tests == 1


def test_failing_hidden_test_fails_overall():
    # Regression: hidden test failures must not be masked by
    # structured visible results (HarnessOutputParser aggregation).

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[CodingTestCase(args=[2], expected=4)],
        hidden_tests=[CodingTestCase(args=[0], expected=99)],
    )

    result = executor.execute(question, VALID_CODE)

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS
    assert result.passed_tests == 1
    assert result.total_tests == 2


# ---------------------------------------------------------
# MALFORMED SUBMISSIONS
# ---------------------------------------------------------


def test_syntax_error_in_user_code():

    executor = CodingExecutor()

    broken_code = """
def solution(x)
    return x * 2
"""

    question = build_coding_question(
        visible_tests=[CodingTestCase(args=[2], expected=4)],
    )

    result = executor.execute(question, broken_code)

    assert result.success is False
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.error


def test_empty_submission_fails():

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[CodingTestCase(args=[2], expected=4)],
    )

    result = executor.execute(question, "")

    assert result.success is False


# ---------------------------------------------------------
# RUNTIME / SANDBOX BRANCHES (mocked sandbox)
# ---------------------------------------------------------


def test_missing_result_marker_triggers_internal_error():

    mock_sandbox = MagicMock()
    mock_sandbox.execute.return_value = build_raw_output(
        returncode=0,
        stdout="No marker here",
    )

    executor = CodingExecutor(sandbox=mock_sandbox)

    question = build_coding_question()

    result = executor.execute(question, "")

    assert result.status == ExecutionStatus.INTERNAL_ERROR
    assert result.success is False


def test_runtime_error_branch():

    mock_sandbox = MagicMock()
    mock_sandbox.execute.return_value = build_raw_output(
        returncode=1,
        stderr="Traceback error",
    )

    executor = CodingExecutor(sandbox=mock_sandbox)

    question = build_coding_question()

    result = executor.execute(question, "")

    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.success is False
    assert result.error == "Traceback error"


def test_timeout_branch():

    mock_sandbox = MagicMock()
    mock_sandbox.execute.return_value = build_raw_output(
        returncode=-1,
        stderr="Execution timed out",
        execution_time_ms=1000,
        timeout=True,
    )

    executor = CodingExecutor(sandbox=mock_sandbox)

    question = build_coding_question()

    result = executor.execute(question, "")

    assert result.status == ExecutionStatus.TIMEOUT
    assert result.success is False
    assert result.error == "Execution timed out"


# ---------------------------------------------------------
# RESULT FORMATTING
# ---------------------------------------------------------


def test_result_carries_output_and_timing():

    executor = CodingExecutor()

    question = build_coding_question(
        visible_tests=[CodingTestCase(args=[2], expected=4)],
    )

    result = executor.execute(question, VALID_CODE)

    assert result.execution_time_ms is not None
    assert result.execution_time_ms >= 0
    assert "__RESULT__" in (result.output or "")
