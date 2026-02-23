# Tests for ExecutionSandbox


from unittest.mock import patch

from services.coding_engine.execution_sandbox import ExecutionSandbox


def test_internal_exception_handling():
    sandbox = ExecutionSandbox(timeout_seconds=2)

    with patch(
        "services.coding_engine.execution_sandbox.subprocess.run",
        side_effect=OSError("Subprocess failure"),
    ):
        result = sandbox.execute("print('hello')")

        assert result.returncode == -2
        assert "Subprocess failure" in result.stderr
        assert result.timeout is False


def test_successful_execution():
    sandbox = ExecutionSandbox(timeout_seconds=2)

    code = """
print("hello")
"""

    result = sandbox.execute(code)

    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.timeout is False


def test_runtime_error_execution():
    sandbox = ExecutionSandbox(timeout_seconds=2)

    code = """
raise ValueError("boom")
"""

    result = sandbox.execute(code)

    assert result.returncode != 0
    assert "ValueError" in result.stderr


def test_timeout_execution():
    sandbox = ExecutionSandbox(timeout_seconds=1)

    code = """
while True:
    pass
"""

    result = sandbox.execute(code)

    assert result.timeout is True
    assert "timed out" in result.stderr.lower()


def test_internal_exception_handling():
    sandbox = ExecutionSandbox(timeout_seconds=2)

    with patch(
        "services.coding_engine.execution_sandbox.subprocess.run",
        side_effect=OSError("Subprocess failure"),
    ):
        result = sandbox.execute("print('hello')")

        assert result.returncode == -2
        assert "Subprocess failure" in result.stderr
        assert result.timeout is False
