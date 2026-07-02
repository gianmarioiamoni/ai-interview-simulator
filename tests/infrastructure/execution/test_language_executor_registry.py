# tests/infrastructure/execution/test_language_executor_registry.py

import threading
import pytest
from unittest.mock import MagicMock

from infrastructure.execution.language_executor_registry import LanguageExecutorRegistry
from infrastructure.execution.contracts.language_executor import LanguageExecutor
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_limits import ExecutionLimits


def make_mock_executor(lang_id: str, runtime: ExecutionRuntime, available: bool = True) -> LanguageExecutor:
    class MockExecutor(LanguageExecutor):
        @property
        def language_id(self) -> str:
            return lang_id

        @property
        def runtime(self) -> ExecutionRuntime:
            return runtime

        def execute(self, request: ExecutionRequest) -> ExecutionResult:
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
def js_runtime(js_env, default_limits) -> ExecutionRuntime:
    return ExecutionRuntime(
        environment=js_env,
        limits=default_limits,
        runtime_label="nodejs-22",
    )


@pytest.fixture
def ts_runtime(ts_env, default_limits) -> ExecutionRuntime:
    return ExecutionRuntime(
        environment=ts_env,
        limits=default_limits,
        runtime_label="nodejs-22-tsc",
    )


# --- Registration ---

class TestRegistration:
    def test_register_single_executor(self, registry, python_runtime):
        ex = make_mock_executor("python", python_runtime)
        registry.register(ex)
        assert registry.is_supported("python")

    def test_register_multiple_executors(self, registry, python_runtime, js_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        registry.register(make_mock_executor("javascript", js_runtime))
        assert registry.is_supported("python")
        assert registry.is_supported("javascript")

    def test_duplicate_registration_raises(self, registry, python_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(make_mock_executor("python", python_runtime))

    def test_duplicate_registration_error_message(self, registry, python_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        with pytest.raises(ValueError) as exc_info:
            registry.register(make_mock_executor("python", python_runtime))
        assert "python" in str(exc_info.value)

    def test_register_different_languages_no_conflict(self, registry, python_runtime, js_runtime, ts_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        registry.register(make_mock_executor("javascript", js_runtime))
        registry.register(make_mock_executor("typescript", ts_runtime))
        assert len(registry.supported_languages()) == 3

    def test_empty_registry_no_supported_languages(self, registry):
        assert registry.supported_languages() == []

    def test_empty_registry_no_available_runtimes(self, registry):
        assert registry.available_runtimes() == []


# --- get() ---

class TestGet:
    def test_get_registered_executor(self, registry, python_runtime):
        ex = make_mock_executor("python", python_runtime)
        registry.register(ex)
        result = registry.get("python")
        assert result is ex

    def test_get_unregistered_raises_key_error(self, registry):
        with pytest.raises(KeyError):
            registry.get("ruby")

    def test_get_raises_with_language_in_message(self, registry):
        with pytest.raises(KeyError) as exc_info:
            registry.get("ruby")
        assert "ruby" in str(exc_info.value)

    def test_get_after_empty_registry_raises(self, registry):
        with pytest.raises(KeyError):
            registry.get("python")

    def test_get_returns_correct_executor_when_multiple_registered(self, registry, python_runtime, js_runtime):
        py_ex = make_mock_executor("python", python_runtime)
        js_ex = make_mock_executor("javascript", js_runtime)
        registry.register(py_ex)
        registry.register(js_ex)
        assert registry.get("python") is py_ex
        assert registry.get("javascript") is js_ex


# --- get_or_none() ---

class TestGetOrNone:
    def test_get_or_none_registered(self, registry, python_runtime):
        ex = make_mock_executor("python", python_runtime)
        registry.register(ex)
        assert registry.get_or_none("python") is ex

    def test_get_or_none_unregistered_returns_none(self, registry):
        assert registry.get_or_none("ruby") is None

    def test_get_or_none_empty_registry(self, registry):
        assert registry.get_or_none("python") is None

    def test_get_or_none_multiple_languages(self, registry, python_runtime, js_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        registry.register(make_mock_executor("javascript", js_runtime))
        assert registry.get_or_none("typescript") is None


# --- supported_languages() ---

class TestSupportedLanguages:
    def test_supported_languages_sorted(self, registry, python_runtime, js_runtime, ts_runtime):
        registry.register(make_mock_executor("typescript", ts_runtime))
        registry.register(make_mock_executor("python", python_runtime))
        registry.register(make_mock_executor("javascript", js_runtime))
        result = registry.supported_languages()
        assert result == sorted(result)

    def test_supported_languages_returns_all_registered(self, registry, python_runtime, js_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        registry.register(make_mock_executor("javascript", js_runtime))
        langs = registry.supported_languages()
        assert "python" in langs
        assert "javascript" in langs

    def test_supported_languages_empty(self, registry):
        assert registry.supported_languages() == []

    def test_supported_languages_single(self, registry, python_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        assert registry.supported_languages() == ["python"]


# --- is_supported() ---

class TestIsSupported:
    def test_is_supported_true(self, registry, python_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        assert registry.is_supported("python") is True

    def test_is_supported_false_unregistered(self, registry):
        assert registry.is_supported("python") is False

    def test_is_supported_case_sensitive(self, registry, python_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        assert registry.is_supported("Python") is False
        assert registry.is_supported("PYTHON") is False


# --- available_runtimes() ---

class TestAvailableRuntimes:
    def test_available_runtimes_returns_runtimes(self, registry, python_runtime, js_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        registry.register(make_mock_executor("javascript", js_runtime))
        runtimes = registry.available_runtimes()
        assert len(runtimes) == 2

    def test_available_runtimes_empty(self, registry):
        assert registry.available_runtimes() == []

    def test_available_runtimes_correct_objects(self, registry, python_runtime):
        registry.register(make_mock_executor("python", python_runtime))
        runtimes = registry.available_runtimes()
        assert python_runtime in runtimes


# --- Thread safety ---

class TestThreadSafety:
    def test_concurrent_registration_no_data_race(self, python_env, default_limits):
        registry = LanguageExecutorRegistry()
        errors = []

        def register_lang(lang_id: str) -> None:
            env = ExecutionEnvironment(
                language_id=lang_id,
                runtime_id=f"{lang_id}-runtime",
                runtime_version="1.0",
                sandbox_type="subprocess",
            )
            rt = ExecutionRuntime(environment=env, limits=default_limits, runtime_label=lang_id)
            try:
                registry.register(make_mock_executor(lang_id, rt))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_lang, args=(f"lang{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(registry.supported_languages()) == 10

    def test_concurrent_get_is_safe(self, registry, python_runtime):
        ex = make_mock_executor("python", python_runtime)
        registry.register(ex)
        results = []

        def do_get():
            results.append(registry.get("python"))

        threads = [threading.Thread(target=do_get) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r is ex for r in results)
