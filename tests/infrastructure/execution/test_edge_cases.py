# tests/infrastructure/execution/test_edge_cases.py

"""Edge case and boundary condition tests for execution layer contracts."""

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_limits import ExecutionLimits
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_result import ExecutionResult, ExecutionTestResult
from infrastructure.execution.contracts.execution_metrics import ExecutionMetrics
from infrastructure.execution.contracts.execution_diagnostics import (
    ExecutionDiagnostics,
    RuntimeDiagnostic,
    DiagnosticSeverity,
)
from infrastructure.execution.contracts.execution_artifact import ExecutionArtifact, ArtifactKind


class TestLimitsEdgeCases:
    def test_exact_min_timeout(self):
        assert ExecutionLimits(timeout_ms=100).timeout_ms == 100

    def test_exact_max_timeout(self):
        assert ExecutionLimits(timeout_ms=60_000).timeout_ms == 60_000

    def test_exact_min_memory(self):
        assert ExecutionLimits(memory_limit_mb=16).memory_limit_mb == 16

    def test_exact_max_memory(self):
        assert ExecutionLimits(memory_limit_mb=1024).memory_limit_mb == 1024

    def test_min_output_bytes(self):
        assert ExecutionLimits(max_output_bytes=1024).max_output_bytes == 1024

    def test_max_file_descriptors_boundary(self):
        assert ExecutionLimits(max_file_descriptors=256).max_file_descriptors == 256
        with pytest.raises(ValidationError):
            ExecutionLimits(max_file_descriptors=257)
        assert ExecutionLimits(max_file_descriptors=4).max_file_descriptors == 4
        with pytest.raises(ValidationError):
            ExecutionLimits(max_file_descriptors=3)


class TestMetricsEdgeCases:
    def test_all_tests_errored(self):
        m = ExecutionMetrics(
            tests_total=3,
            tests_passed=0,
            tests_failed=0,
            tests_errored=3,
        )
        assert m.pass_rate == 0.0

    def test_single_test_passed(self):
        m = ExecutionMetrics(
            tests_total=1,
            tests_passed=1,
            tests_failed=0,
            tests_errored=0,
        )
        assert m.pass_rate == 1.0

    def test_zero_total_does_not_validate_components(self):
        m = ExecutionMetrics(
            tests_total=0,
            tests_passed=0,
            tests_failed=0,
            tests_errored=0,
        )
        assert m.pass_rate == 0.0

    def test_max_memory_ratio_clamped(self):
        m = ExecutionMetrics(peak_memory_kb=999_999_999)
        assert m.memory_limit_ratio == 1.0


class TestDiagnosticsEdgeCases:
    def test_error_at_line_one(self):
        d = RuntimeDiagnostic(
            severity=DiagnosticSeverity.ERROR,
            error_type="SyntaxError",
            message="err",
            line=1,
        )
        assert d.line == 1

    def test_error_at_column_one(self):
        d = RuntimeDiagnostic(
            severity=DiagnosticSeverity.ERROR,
            error_type="SyntaxError",
            message="err",
            column=1,
        )
        assert d.column == 1

    def test_empty_diagnostics_no_first_error(self):
        d = ExecutionDiagnostics()
        assert d.first_error is None

    def test_only_warnings_no_first_error(self):
        w = RuntimeDiagnostic(
            severity=DiagnosticSeverity.WARNING,
            error_type="DeprecationWarning",
            message="deprecated",
        )
        d = ExecutionDiagnostics(entries=[w])
        assert d.first_error is None

    def test_large_entry_list(self):
        entries = [
            RuntimeDiagnostic(
                severity=DiagnosticSeverity.ERROR,
                error_type="Error",
                message=f"error {i}",
            )
            for i in range(100)
        ]
        d = ExecutionDiagnostics(entries=entries)
        assert d.error_count == 100


class TestRequestEdgeCases:
    def test_whitespace_code_rejected(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRequest(
                execution_id="exec-x",
                question_id="q-x",
                language_id="python",
                candidate_code=" ",
                environment=python_env,
            )

    def test_large_candidate_code_accepted(self, python_env):
        large_code = "x = 1\n" * 10_000
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="python",
            candidate_code=large_code,
            environment=python_env,
        )
        assert len(req.candidate_code) > 0

    def test_uuid_execution_id(self, python_env):
        req = ExecutionRequest(
            execution_id="550e8400-e29b-41d4-a716-446655440000",
            question_id="q-x",
            language_id="python",
            candidate_code="pass",
            environment=python_env,
        )
        assert "550e8400" in req.execution_id


class TestResultEdgeCases:
    def test_many_test_results(self):
        tests = [
            ExecutionTestResult(test_id=f"t{i}", passed=(i % 2 == 0))
            if i % 2 == 0
            else ExecutionTestResult(test_id=f"t{i}", passed=False, error_message="err")
            for i in range(100)
        ]
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.FAILED_TESTS,
            test_results=tests,
        )
        assert r.tests_total == 100
        assert r.tests_passed == 50
        assert r.tests_failed == 50

    def test_all_status_values_in_result(self):
        """Every ExecutionStatus must be constructable in an ExecutionResult."""
        for status in ExecutionStatus:
            kwargs = {
                "execution_id": "exec-x",
                "language_id": "python",
                "question_id": "q-x",
                "status": status,
            }
            if status == ExecutionStatus.TIMEOUT:
                kwargs["timed_out"] = True
            r = ExecutionResult(**kwargs)
            assert r.status == status

    def test_compilation_error_javascript(self):
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="javascript",
            question_id="q-x",
            status=ExecutionStatus.COMPILATION_ERROR,
        )
        assert r.passed is False

    def test_sandbox_violation_result(self):
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.SANDBOX_VIOLATION,
            stderr="Forbidden module detected: os",
        )
        assert r.status == ExecutionStatus.SANDBOX_VIOLATION

    def test_memory_exceeded_result(self):
        r = ExecutionResult(
            execution_id="exec-x",
            language_id="python",
            question_id="q-x",
            status=ExecutionStatus.MEMORY_EXCEEDED,
        )
        assert r.status.is_infrastructure_failure is True


class TestEnvironmentEdgeCases:
    def test_empty_import_lists_allowed(self):
        env = ExecutionEnvironment(
            language_id="python",
            runtime_id="cpython-3.12",
            runtime_version="3.12.0",
            sandbox_type="subprocess",
            import_allowlist=[],
            import_blocklist=[],
        )
        assert env.import_allowlist == []
        assert env.import_blocklist == []

    def test_multiple_overlap_raises(self):
        with pytest.raises(ValidationError):
            ExecutionEnvironment(
                language_id="python",
                runtime_id="cpython-3.12",
                runtime_version="3.12.0",
                sandbox_type="subprocess",
                import_allowlist=["math", "os", "sys"],
                import_blocklist=["os", "sys", "socket"],
            )

    def test_single_module_in_each_list(self):
        env = ExecutionEnvironment(
            language_id="python",
            runtime_id="cpython-3.12",
            runtime_version="3.12.0",
            sandbox_type="subprocess",
            import_allowlist=["math"],
            import_blocklist=["os"],
        )
        assert "math" in env.import_allowlist
        assert "os" in env.import_blocklist
