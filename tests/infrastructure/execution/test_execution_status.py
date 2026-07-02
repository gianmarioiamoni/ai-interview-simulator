# tests/infrastructure/execution/test_execution_status.py

import pytest
from infrastructure.execution.contracts.execution_status import ExecutionStatus


class TestExecutionStatusValues:
    def test_all_expected_values_present(self):
        values = {s.value for s in ExecutionStatus}
        assert values == {
            "success",
            "failed_tests",
            "syntax_error",
            "runtime_error",
            "timeout",
            "memory_exceeded",
            "compilation_error",
            "sandbox_violation",
            "internal_error",
        }

    def test_is_str_enum(self):
        assert isinstance(ExecutionStatus.SUCCESS, str)
        assert ExecutionStatus.SUCCESS == "success"

    def test_from_string(self):
        assert ExecutionStatus("success") == ExecutionStatus.SUCCESS
        assert ExecutionStatus("timeout") == ExecutionStatus.TIMEOUT

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            ExecutionStatus("unknown_status")

    def test_serialization(self):
        import json
        data = json.dumps({"status": ExecutionStatus.SUCCESS})
        assert '"success"' in data


class TestExecutionStatusProperties:
    def test_success_is_terminal_success(self):
        assert ExecutionStatus.SUCCESS.is_terminal_success is True

    def test_non_success_not_terminal_success(self):
        for s in ExecutionStatus:
            if s != ExecutionStatus.SUCCESS:
                assert s.is_terminal_success is False

    def test_execution_failures(self):
        execution_failures = {
            ExecutionStatus.FAILED_TESTS,
            ExecutionStatus.SYNTAX_ERROR,
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.COMPILATION_ERROR,
        }
        for s in ExecutionStatus:
            assert s.is_execution_failure == (s in execution_failures)

    def test_infrastructure_failures(self):
        infra_failures = {
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.MEMORY_EXCEEDED,
            ExecutionStatus.SANDBOX_VIOLATION,
            ExecutionStatus.INTERNAL_ERROR,
        }
        for s in ExecutionStatus:
            assert s.is_infrastructure_failure == (s in infra_failures)

    def test_success_not_execution_failure(self):
        assert ExecutionStatus.SUCCESS.is_execution_failure is False

    def test_success_not_infrastructure_failure(self):
        assert ExecutionStatus.SUCCESS.is_infrastructure_failure is False

    def test_execution_and_infrastructure_failure_disjoint(self):
        for s in ExecutionStatus:
            assert not (s.is_execution_failure and s.is_infrastructure_failure)

    def test_timeout_is_infrastructure_failure(self):
        assert ExecutionStatus.TIMEOUT.is_infrastructure_failure is True

    def test_sandbox_violation_is_infrastructure_failure(self):
        assert ExecutionStatus.SANDBOX_VIOLATION.is_infrastructure_failure is True
