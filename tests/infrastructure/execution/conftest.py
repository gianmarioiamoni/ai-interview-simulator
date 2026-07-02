# tests/infrastructure/execution/conftest.py

import pytest
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_limits import ExecutionLimits
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
from infrastructure.execution.contracts.execution_request import ExecutionRequest
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
from infrastructure.execution.contracts.execution_result import (
    ExecutionResult,
    ExecutionTestResult,
)


@pytest.fixture
def python_env() -> ExecutionEnvironment:
    return ExecutionEnvironment(
        language_id="python",
        runtime_id="cpython-3.12",
        runtime_version="3.12.0",
        sandbox_type="subprocess",
    )


@pytest.fixture
def js_env() -> ExecutionEnvironment:
    return ExecutionEnvironment(
        language_id="javascript",
        runtime_id="nodejs-22",
        runtime_version="22.0.0",
        sandbox_type="subprocess",
    )


@pytest.fixture
def ts_env() -> ExecutionEnvironment:
    return ExecutionEnvironment(
        language_id="typescript",
        runtime_id="nodejs-22-tsc",
        runtime_version="22.0.0",
        sandbox_type="subprocess",
    )


@pytest.fixture
def default_limits() -> ExecutionLimits:
    return ExecutionLimits()


@pytest.fixture
def strict_limits() -> ExecutionLimits:
    return ExecutionLimits(timeout_ms=1000, memory_limit_mb=32)


@pytest.fixture
def python_runtime(python_env, default_limits) -> ExecutionRuntime:
    return ExecutionRuntime(
        environment=python_env,
        limits=default_limits,
        runtime_label="python-3.12-subprocess",
    )


@pytest.fixture
def minimal_request(python_env) -> ExecutionRequest:
    return ExecutionRequest(
        execution_id="exec-001",
        question_id="q-abc",
        language_id="python",
        candidate_code="def solution(): pass",
        environment=python_env,
    )


@pytest.fixture
def success_metrics() -> ExecutionMetrics:
    return ExecutionMetrics(
        duration_ms=42,
        tests_total=5,
        tests_passed=5,
        tests_failed=0,
        tests_errored=0,
    )


@pytest.fixture
def failed_metrics() -> ExecutionMetrics:
    return ExecutionMetrics(
        duration_ms=100,
        tests_total=5,
        tests_passed=3,
        tests_failed=2,
        tests_errored=0,
    )


@pytest.fixture
def success_result(python_env) -> ExecutionResult:
    return ExecutionResult(
        execution_id="exec-001",
        language_id="python",
        question_id="q-abc",
        status=ExecutionStatus.SUCCESS,
        exit_code=0,
        stdout="ok\n",
    )


@pytest.fixture
def timeout_result() -> ExecutionResult:
    return ExecutionResult(
        execution_id="exec-002",
        language_id="python",
        question_id="q-abc",
        status=ExecutionStatus.TIMEOUT,
        exit_code=-1,
        timed_out=True,
        stderr="Execution timed out after 5000ms",
    )


@pytest.fixture
def error_diagnostic() -> RuntimeDiagnostic:
    return RuntimeDiagnostic(
        severity=DiagnosticSeverity.ERROR,
        error_type="SyntaxError",
        message="invalid syntax",
        line=3,
        column=5,
    )


@pytest.fixture
def warning_diagnostic() -> RuntimeDiagnostic:
    return RuntimeDiagnostic(
        severity=DiagnosticSeverity.WARNING,
        error_type="DeprecationWarning",
        message="module X is deprecated",
    )
