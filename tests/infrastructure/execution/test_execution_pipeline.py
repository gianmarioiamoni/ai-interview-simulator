# tests/infrastructure/execution/test_execution_pipeline.py

import pytest
from unittest.mock import MagicMock

from infrastructure.execution.execution_pipeline import ExecutionPipeline
from infrastructure.execution.execution_dispatcher import ExecutionDispatcher
from infrastructure.execution.language_executor_registry import LanguageExecutorRegistry
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.language_executor import LanguageExecutor


def make_mock_executor(lang_id: str, runtime: ExecutionRuntime, available: bool = True, raises: Exception | None = None) -> LanguageExecutor:
    class MockExecutor(LanguageExecutor):
        @property
        def language_id(self) -> str:
            return lang_id

        @property
        def runtime(self) -> ExecutionRuntime:
            return runtime

        def execute(self, request: ExecutionRequest) -> ExecutionResult:
            if raises:
                raise raises
            return ExecutionResult(
                execution_id=request.execution_id,
                language_id=request.language_id,
                question_id=request.question_id,
                status=ExecutionStatus.SUCCESS,
            )

        def is_available(self) -> bool:
            return available

    return MockExecutor()


@pytest.fixture
def python_runtime(python_env, default_limits) -> ExecutionRuntime:
    return ExecutionRuntime(
        environment=python_env,
        limits=default_limits,
        runtime_label="python-3.12",
    )


@pytest.fixture
def registry() -> LanguageExecutorRegistry:
    return LanguageExecutorRegistry()


@pytest.fixture
def dispatcher(registry) -> ExecutionDispatcher:
    return ExecutionDispatcher(registry)


@pytest.fixture
def pipeline(dispatcher) -> ExecutionPipeline:
    return ExecutionPipeline(dispatcher)


# --- Success path ---

class TestPipelineSuccess:
    def test_run_returns_execution_result(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = pipeline.run(minimal_request)
        assert isinstance(result, ExecutionResult)

    def test_run_returns_success_status(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = pipeline.run(minimal_request)
        assert result.status == ExecutionStatus.SUCCESS

    def test_run_preserves_execution_id(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = pipeline.run(minimal_request)
        assert result.execution_id == minimal_request.execution_id

    def test_run_preserves_language_id(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = pipeline.run(minimal_request)
        assert result.language_id == minimal_request.language_id

    def test_run_preserves_question_id(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = pipeline.run(minimal_request)
        assert result.question_id == minimal_request.question_id


# --- Never raises ---

class TestPipelineNeverRaises:
    def test_unknown_language_never_raises(self, pipeline, minimal_request):
        result = pipeline.run(minimal_request)
        assert isinstance(result, ExecutionResult)

    def test_unavailable_executor_never_raises(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, available=False))
        result = pipeline.run(minimal_request)
        assert isinstance(result, ExecutionResult)

    def test_executor_exception_never_raises(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=RuntimeError("boom")))
        result = pipeline.run(minimal_request)
        assert isinstance(result, ExecutionResult)


# --- Failure paths return INTERNAL_ERROR ---

class TestPipelineFailureHandling:
    def test_unknown_language_returns_internal_error(self, pipeline, minimal_request):
        result = pipeline.run(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_unavailable_executor_returns_internal_error(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, available=False))
        result = pipeline.run(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_executor_raises_returns_internal_error(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=Exception("crash")))
        result = pipeline.run(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_dispatcher_exception_wraps_into_internal_error(self, minimal_request):
        bad_dispatcher = MagicMock()
        bad_dispatcher.dispatch.side_effect = RuntimeError("dispatcher blew up")
        pipeline = ExecutionPipeline(bad_dispatcher)
        result = pipeline.run(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_unknown_language_preserves_ids(self, pipeline, minimal_request):
        result = pipeline.run(minimal_request)
        assert result.execution_id == minimal_request.execution_id
        assert result.question_id == minimal_request.question_id


# --- Determinism ---

class TestPipelineDeterminism:
    def test_same_request_same_result_status(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        r1 = pipeline.run(minimal_request)
        r2 = pipeline.run(minimal_request)
        assert r1.status == r2.status

    def test_multiple_runs_independent(self, pipeline, registry, python_runtime, python_env):
        registry.register(make_mock_executor("python", python_runtime))
        requests = [
            ExecutionRequest(
                execution_id=f"exec-{i}",
                question_id="q-1",
                language_id="python",
                candidate_code="x = 1",
                environment=python_env,
            )
            for i in range(5)
        ]
        results = [pipeline.run(r) for r in requests]
        assert all(r.status == ExecutionStatus.SUCCESS for r in results)


# --- Validation integration ---

class TestPipelineValidation:
    def test_valid_request_passes_validation(self, pipeline, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = pipeline.run(minimal_request)
        assert result.status == ExecutionStatus.SUCCESS
