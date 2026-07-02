# tests/infrastructure/execution/test_execution_dispatcher.py

import pytest
from unittest.mock import MagicMock

from infrastructure.execution.execution_dispatcher import ExecutionDispatcher
from infrastructure.execution.language_executor_registry import LanguageExecutorRegistry
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
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
def registry() -> LanguageExecutorRegistry:
    return LanguageExecutorRegistry()


@pytest.fixture
def python_runtime(python_env, default_limits) -> ExecutionRuntime:
    return ExecutionRuntime(
        environment=python_env,
        limits=default_limits,
        runtime_label="python-3.12",
    )


@pytest.fixture
def dispatcher(registry) -> ExecutionDispatcher:
    return ExecutionDispatcher(registry)


# --- Success routing ---

class TestSuccessRouting:
    def test_dispatch_returns_execution_result(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = dispatcher.dispatch(minimal_request)
        assert isinstance(result, ExecutionResult)

    def test_dispatch_success_status(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.SUCCESS

    def test_dispatch_preserves_execution_id(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = dispatcher.dispatch(minimal_request)
        assert result.execution_id == minimal_request.execution_id

    def test_dispatch_preserves_language_id(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = dispatcher.dispatch(minimal_request)
        assert result.language_id == minimal_request.language_id

    def test_dispatch_preserves_question_id(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime))
        result = dispatcher.dispatch(minimal_request)
        assert result.question_id == minimal_request.question_id

    def test_dispatch_routes_to_correct_executor(self, dispatcher, registry, python_runtime, js_env, default_limits):
        js_runtime = ExecutionRuntime(environment=js_env, limits=default_limits, runtime_label="nodejs-22")
        py_ex = make_mock_executor("python", python_runtime)
        js_ex = make_mock_executor("javascript", js_runtime)
        registry.register(py_ex)
        registry.register(js_ex)
        js_request = ExecutionRequest(
            execution_id="exec-js-001",
            question_id="q-js",
            language_id="javascript",
            candidate_code="const x = 1;",
            environment=js_env,
        )
        result = dispatcher.dispatch(js_request)
        assert result.language_id == "javascript"


# --- Unknown language ---

class TestUnknownLanguage:
    def test_unknown_language_returns_internal_error(self, dispatcher, minimal_request):
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_unknown_language_never_raises(self, dispatcher, minimal_request):
        result = dispatcher.dispatch(minimal_request)
        assert isinstance(result, ExecutionResult)

    def test_unknown_language_has_runtime_errors(self, dispatcher, minimal_request):
        result = dispatcher.dispatch(minimal_request)
        assert len(result.runtime_errors) > 0

    def test_unknown_language_error_message_contains_language(self, dispatcher, minimal_request):
        result = dispatcher.dispatch(minimal_request)
        assert "python" in result.runtime_errors[0]

    def test_unknown_language_preserves_ids(self, dispatcher, minimal_request):
        result = dispatcher.dispatch(minimal_request)
        assert result.execution_id == minimal_request.execution_id
        assert result.question_id == minimal_request.question_id

    def test_unknown_language_exit_code_negative(self, dispatcher, minimal_request):
        result = dispatcher.dispatch(minimal_request)
        assert result.exit_code == -1


# --- Unavailable executor ---

class TestUnavailableExecutor:
    def test_unavailable_executor_returns_internal_error(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, available=False))
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_unavailable_executor_never_raises(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, available=False))
        result = dispatcher.dispatch(minimal_request)
        assert isinstance(result, ExecutionResult)

    def test_unavailable_executor_has_error_message(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, available=False))
        result = dispatcher.dispatch(minimal_request)
        assert len(result.runtime_errors) > 0

    def test_unavailable_executor_preserves_execution_id(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, available=False))
        result = dispatcher.dispatch(minimal_request)
        assert result.execution_id == minimal_request.execution_id

    def test_availability_check_raises_returns_internal_error(self, dispatcher, registry, python_runtime, minimal_request):
        class FailAvailabilityExecutor(LanguageExecutor):
            @property
            def language_id(self) -> str:
                return "python"
            @property
            def runtime(self) -> ExecutionRuntime:
                return python_runtime
            def execute(self, request: ExecutionRequest) -> ExecutionResult:
                return ExecutionResult(execution_id=request.execution_id, language_id="python", question_id=request.question_id, status=ExecutionStatus.SUCCESS)
            def is_available(self) -> bool:
                raise RuntimeError("health check failed")

        registry.register(FailAvailabilityExecutor())
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR


# --- Executor raises ---

class TestExecutorRaises:
    def test_executor_exception_returns_internal_error(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=RuntimeError("crash")))
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_executor_exception_never_raises(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=Exception("oops")))
        result = dispatcher.dispatch(minimal_request)
        assert isinstance(result, ExecutionResult)

    def test_executor_exception_has_error_in_message(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=ValueError("bad value")))
        result = dispatcher.dispatch(minimal_request)
        assert any("bad value" in e for e in result.runtime_errors)

    def test_executor_value_error_captured(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=ValueError("vex")))
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_executor_arbitrary_exception_captured(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=KeyError("key")))
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_executor_preserves_ids_on_exception(self, dispatcher, registry, python_runtime, minimal_request):
        registry.register(make_mock_executor("python", python_runtime, raises=RuntimeError("crash")))
        result = dispatcher.dispatch(minimal_request)
        assert result.execution_id == minimal_request.execution_id
        assert result.question_id == minimal_request.question_id


# --- Determinism ---

class TestDeterminism:
    def test_same_request_same_routing(self, dispatcher, registry, python_runtime, minimal_request):
        ex = make_mock_executor("python", python_runtime)
        registry.register(ex)
        r1 = dispatcher.dispatch(minimal_request)
        r2 = dispatcher.dispatch(minimal_request)
        assert r1.status == r2.status
        assert r1.language_id == r2.language_id
