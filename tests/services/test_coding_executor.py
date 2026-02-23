# tests/services/test_coding_executor.py

from unittest.mock import MagicMock

from domain.contracts.execution_result import ExecutionStatus
from domain.contracts.coding_test_case import CodingTestCase
from services.coding_engine.coding_executor import CodingExecutor


def test_successful_execution():
    executor = CodingExecutor()

    code = """
def solution(x):
    return x * 2
"""

    tests = [
        CodingTestCase(args=[2], expected=4),
        CodingTestCase(args=[3], expected=6),
    ]

    result = executor.execute(
        question_id="q1",
        user_code=code,
        function_name="solution",
        test_cases=tests,
    )

    assert result.success is True
    assert result.passed_tests == 2
    assert result.total_tests == 2


def test_failed_test_execution():
    executor = CodingExecutor()

    code = """
def solution(x):
    return x * 2
"""

    tests = [
        CodingTestCase(args=[2], expected=4),
        CodingTestCase(args=[3], expected=7),
    ]

    result = executor.execute(
        question_id="q1",
        user_code=code,
        function_name="solution",
        test_cases=tests,
    )

    assert result.success is False
    assert result.passed_tests == 1
    assert result.total_tests == 2


def test_syntax_error():
    executor = CodingExecutor()

    code = """
def solution(x)
    return x * 2
"""

    tests = [
        CodingTestCase(args=[2], expected=4),
    ]

    result = executor.execute(
        question_id="q1",
        user_code=code,
        function_name="solution",
        test_cases=tests,
    )

    assert result.success is False
    assert result.status != None


def test_missing_result_marker_triggers_internal_error():
    mock_sandbox = MagicMock()

    mock_sandbox.execute.return_value = type(
        "Raw",
        (),
        {
            "returncode": 0,
            "stdout": "No marker here",
            "stderr": "",
            "execution_time_ms": 10,
            "timeout": False,
        },
    )()

    executor = CodingExecutor(sandbox=mock_sandbox)

    result = executor.execute(
        question_id="q1",
        user_code="",
        function_name="solution",
        test_cases=[],
    )

    assert result.status.name == "INTERNAL_ERROR"
    assert result.success is False


def test_runtime_error_branch():
    mock_sandbox = MagicMock()

    mock_sandbox.execute.return_value = type(
        "Raw",
        (),
        {
            "returncode": 1,
            "stdout": "",
            "stderr": "Traceback error",
            "execution_time_ms": 10,
            "timeout": False,
        },
    )()

    executor = CodingExecutor(sandbox=mock_sandbox)

    result = executor.execute(
        question_id="q1",
        user_code="",
        function_name="solution",
        test_cases=[],
    )

    assert result.status.name == "RUNTIME_ERROR"
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.success is False


def test_timeout_branch():
    mock_sandbox = MagicMock()

    mock_sandbox.execute.return_value = type(
        "Raw",
        (),
        {
            "returncode": -1,
            "stdout": "",
            "stderr": "Execution timed out",
            "execution_time_ms": 1000,
            "timeout": True,
        },
    )()

    executor = CodingExecutor(sandbox=mock_sandbox)

    result = executor.execute(
        question_id="q1",
        user_code="",
        function_name="solution",
        test_cases=[],
    )

    assert result.status == ExecutionStatus.TIMEOUT
    assert result.success is False

def test_syntax_error_detection():
    mock_sandbox = MagicMock()

    mock_sandbox.execute.return_value = type("Raw", (), {
        "returncode": 1,
        "stdout": "",
        "stderr": "SyntaxError: invalid syntax",
        "execution_time_ms": 10,
        "timeout": False,
    })()

    executor = CodingExecutor(sandbox=mock_sandbox)

    result = executor.execute(
        question_id="q1",
        user_code="",
        function_name="solution",
        test_cases=[],
    )

    assert result.status == ExecutionStatus.SYNTAX_ERROR
    assert result.success is False
