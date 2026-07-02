# tests/infrastructure/execution/test_execution_result.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_result import (
    ExecutionResult,
    ExecutionTestResult,
)
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_metrics import ExecutionMetrics
from infrastructure.execution.contracts.execution_diagnostics import (
    ExecutionDiagnostics,
    RuntimeDiagnostic,
    DiagnosticSeverity,
)
from infrastructure.execution.contracts.execution_artifact import (
    ExecutionArtifact,
    ArtifactKind,
)


class TestExecutionTestResultConstruction:
    def test_passing_test(self):
        t = ExecutionTestResult(test_id="t1", passed=True)
        assert t.passed is True
        assert t.error_message is None

    def test_failing_test_with_message(self):
        t = ExecutionTestResult(
            test_id="t2",
            passed=False,
            error_message="AssertionError: expected 1 got 2",
        )
        assert t.passed is False
        assert t.error_message == "AssertionError: expected 1 got 2"

    def test_passing_with_error_message_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionTestResult(
                test_id="t3",
                passed=True,
                error_message="should not be here",
            )

    def test_hidden_flag(self):
        t = ExecutionTestResult(test_id="t4", passed=True, is_hidden=True)
        assert t.is_hidden is True

    def test_duration_ms_default(self):
        t = ExecutionTestResult(test_id="t5", passed=True)
        assert t.duration_ms == 0

    def test_negative_duration_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionTestResult(test_id="t6", passed=True, duration_ms=-1)

    def test_empty_test_id_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionTestResult(test_id="", passed=True)

    def test_frozen(self):
        t = ExecutionTestResult(test_id="t7", passed=True)
        with pytest.raises(ValidationError):
            t.passed = False


class TestExecutionResultConstruction:
    def test_minimal_success(self, success_result):
        assert success_result.status == ExecutionStatus.SUCCESS
        assert success_result.passed is True
        assert success_result.timed_out is False

    def test_timeout_result(self, timeout_result):
        assert timeout_result.status == ExecutionStatus.TIMEOUT
        assert timeout_result.timed_out is True
        assert timeout_result.passed is False

    def test_defaults(self):
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.SUCCESS,
        )
        assert r.stdout == ""
        assert r.stderr == ""
        assert r.test_results == []
        assert r.runtime_errors == []
        assert r.schema_version == "1.0"

    def test_with_test_results(self):
        tests = [
            ExecutionTestResult(test_id="t1", passed=True),
            ExecutionTestResult(test_id="t2", passed=False, error_message="err"),
        ]
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.FAILED_TESTS,
            test_results=tests,
        )
        assert r.tests_total == 2
        assert r.tests_passed == 1
        assert r.tests_failed == 1

    def test_with_artifacts(self):
        artifact = ExecutionArtifact(
            kind=ArtifactKind.STDOUT,
            name="stdout",
            content="hello",
            size_bytes=5,
        )
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.SUCCESS,
            artifacts=[artifact],
        )
        assert len(r.artifacts) == 1

    def test_with_diagnostics(self, error_diagnostic):
        diag = ExecutionDiagnostics(entries=[error_diagnostic])
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.SYNTAX_ERROR,
            diagnostics=diag,
        )
        assert r.diagnostics.has_errors is True

    def test_with_runtime_errors(self):
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.RUNTIME_ERROR,
            runtime_errors=["ZeroDivisionError at line 5"],
        )
        assert len(r.runtime_errors) == 1


class TestExecutionResultInvariants:
    def test_timeout_requires_timed_out_true(self):
        with pytest.raises(ValidationError):
            ExecutionResult(
                execution_id="exec-x",
                language_id="python",
                question_id="q-x",
                status=ExecutionStatus.TIMEOUT,
                timed_out=False,
            )

    def test_timed_out_requires_timeout_status(self):
        with pytest.raises(ValidationError):
            ExecutionResult(
                execution_id="exec-x",
                language_id="python",
                question_id="q-x",
                status=ExecutionStatus.SUCCESS,
                timed_out=True,
            )

    def test_empty_execution_id_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionResult(
                execution_id="",
                language_id="python",
                question_id="q-x",
                status=ExecutionStatus.SUCCESS,
            )

    def test_empty_language_id_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionResult(
                execution_id="exec-x",
                language_id="",
                question_id="q-x",
                status=ExecutionStatus.SUCCESS,
            )

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ExecutionResult(
                execution_id="exec-x",
                language_id="python",
                question_id="q-x",
                status=ExecutionStatus.SUCCESS,
                unknown="x",
            )


class TestExecutionResultProperties:
    def test_passed_true_on_success(self, success_result):
        assert success_result.passed is True

    def test_passed_false_on_failure(self, timeout_result):
        assert timeout_result.passed is False

    def test_tests_passed_count(self):
        tests = [
            ExecutionTestResult(test_id="t1", passed=True),
            ExecutionTestResult(test_id="t2", passed=True),
            ExecutionTestResult(test_id="t3", passed=False, error_message="fail"),
        ]
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.FAILED_TESTS,
            test_results=tests,
        )
        assert r.tests_passed == 2
        assert r.tests_failed == 1
        assert r.tests_total == 3

    def test_empty_tests_counts_zero(self, success_result):
        assert success_result.tests_total == 0
        assert success_result.tests_passed == 0
        assert success_result.tests_failed == 0


class TestExecutionResultLanguageIndependence:
    """Verify that ExecutionResult structure is identical regardless of language."""

    def test_python_result_structure(self):
        r = ExecutionResult(
            execution_id="exec-py",
            language_id="python",
            question_id="q-py",
            status=ExecutionStatus.SUCCESS,
        )
        assert r.language_id == "python"

    def test_javascript_result_structure(self):
        r = ExecutionResult(
            execution_id="exec-js",
            language_id="javascript",
            question_id="q-js",
            status=ExecutionStatus.SUCCESS,
        )
        assert r.language_id == "javascript"

    def test_typescript_result_structure(self):
        r = ExecutionResult(
            execution_id="exec-ts",
            language_id="typescript",
            question_id="q-ts",
            status=ExecutionStatus.COMPILATION_ERROR,
        )
        assert r.language_id == "typescript"
        assert r.passed is False

    def test_all_statuses_valid_in_result(self):
        for status in ExecutionStatus:
            kwargs = {
                "execution_id": "exec-x",
                "language_id": "python",
                "question_id": "q-x",
                "status": status,
            }
            if status == ExecutionStatus.TIMEOUT:
                kwargs["timed_out"] = True
                kwargs["exit_code"] = -1
            r = ExecutionResult(**kwargs)
            assert r.status == status


class TestExecutionResultSerialization:
    def test_round_trip_success(self, success_result):
        restored = ExecutionResult.model_validate(success_result.model_dump())
        assert restored == success_result

    def test_json_round_trip_success(self, success_result):
        restored = ExecutionResult.model_validate_json(success_result.model_dump_json())
        assert restored == success_result

    def test_round_trip_with_tests(self):
        tests = [ExecutionTestResult(test_id="t1", passed=True)]
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.SUCCESS,
            test_results=tests,
        )
        restored = ExecutionResult.model_validate(r.model_dump())
        assert restored == r

    def test_frozen(self, success_result):
        with pytest.raises(ValidationError):
            success_result.status = ExecutionStatus.FAILED_TESTS
