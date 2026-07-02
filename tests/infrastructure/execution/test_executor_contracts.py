# tests/infrastructure/execution/test_executor_contracts.py

"""Tests for LanguageExecutor and LanguageExecutorFactory abstract contracts.

Verifies that the abstract methods are enforced, the validate_request guard
works correctly, and that concrete stub implementations satisfy the contracts.
"""

import pytest
from abc import ABC
from typing import Optional
from infrastructure.execution.contracts.language_executor import LanguageExecutor
from infrastructure.execution.contracts.language_executor_factory import LanguageExecutorFactory
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_status import ExecutionStatus


# ---------------------------------------------------------------------------
# Concrete stubs (test-only implementations)
# ---------------------------------------------------------------------------

class StubExecutor(LanguageExecutor):
    """Minimal concrete executor for contract tests."""

    def __init__(self, language_id: str, available: bool = True) -> None:
        self._language_id = language_id
        self._available = available
        self._env = ExecutionEnvironment(
            language_id=language_id,
            runtime_id=f"{language_id}-runtime",
            runtime_version="1.0",
            sandbox_type="subprocess",
        )
        self._runtime = ExecutionRuntime(
            environment=self._env,
            runtime_label=f"{language_id}-stub",
        )

    @property
    def language_id(self) -> str:
        return self._language_id

    @property
    def runtime(self) -> ExecutionRuntime:
        return self._runtime

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.validate_request(request)
        return ExecutionResult(
            execution_id=request.execution_id,
            language_id=self._language_id,
            question_id=request.question_id,
            status=ExecutionStatus.SUCCESS,
        )

    def is_available(self) -> bool:
        return self._available


class StubFactory(LanguageExecutorFactory):
    """Minimal concrete factory for contract tests."""

    def __init__(self) -> None:
        self._registry: dict[str, LanguageExecutor] = {}

    def get(self, language_id: str) -> LanguageExecutor:
        if language_id not in self._registry:
            raise KeyError(f"No executor registered for '{language_id}'")
        return self._registry[language_id]

    def get_or_none(self, language_id: str) -> Optional[LanguageExecutor]:
        return self._registry.get(language_id)

    def register(self, executor: LanguageExecutor) -> None:
        if executor.language_id in self._registry:
            raise ValueError(f"Executor for '{executor.language_id}' already registered")
        self._registry[executor.language_id] = executor

    def supported_languages(self) -> list[str]:
        return sorted(self._registry.keys())

    def is_supported(self, language_id: str) -> bool:
        return language_id in self._registry

    def available_runtimes(self) -> list[ExecutionRuntime]:
        return [e.runtime for e in self._registry.values()]


# ---------------------------------------------------------------------------
# LanguageExecutor abstract contract
# ---------------------------------------------------------------------------

class TestLanguageExecutorIsAbstract:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            LanguageExecutor()  # type: ignore

    def test_stub_implements_contract(self):
        executor = StubExecutor("python")
        assert executor.language_id == "python"
        assert isinstance(executor.runtime, ExecutionRuntime)
        assert executor.is_available() is True

    def test_unavailable_executor(self):
        executor = StubExecutor("python", available=False)
        assert executor.is_available() is False


class TestLanguageExecutorValidateRequest:
    def test_validate_request_passes_correct_language(self, python_env):
        executor = StubExecutor("python")
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="python",
            candidate_code="pass",
            environment=python_env,
        )
        executor.validate_request(req)

    def test_validate_request_raises_wrong_language(self, js_env):
        executor = StubExecutor("python")
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="javascript",
            candidate_code="function f() {}",
            environment=js_env,
        )
        with pytest.raises(ValueError, match="I-27-10"):
            executor.validate_request(req)

    def test_execute_dispatches_correctly(self, python_env):
        executor = StubExecutor("python")
        req = ExecutionRequest(
            execution_id="exec-01",
            question_id="q-01",
            language_id="python",
            candidate_code="pass",
            environment=python_env,
        )
        result = executor.execute(req)
        assert result.execution_id == "exec-01"
        assert result.language_id == "python"
        assert result.status == ExecutionStatus.SUCCESS

    def test_execute_wrong_language_raises(self, js_env):
        executor = StubExecutor("python")
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="javascript",
            candidate_code="pass",
            environment=js_env,
        )
        with pytest.raises(ValueError):
            executor.execute(req)


# ---------------------------------------------------------------------------
# LanguageExecutorFactory abstract contract
# ---------------------------------------------------------------------------

class TestLanguageExecutorFactoryIsAbstract:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            LanguageExecutorFactory()  # type: ignore


class TestLanguageExecutorFactoryRegistration:
    def test_register_and_get(self):
        factory = StubFactory()
        executor = StubExecutor("python")
        factory.register(executor)
        assert factory.get("python") is executor

    def test_duplicate_registration_raises(self):
        factory = StubFactory()
        factory.register(StubExecutor("python"))
        with pytest.raises(ValueError):
            factory.register(StubExecutor("python"))

    def test_get_unregistered_raises(self):
        factory = StubFactory()
        with pytest.raises(KeyError):
            factory.get("unknown")

    def test_get_or_none_unregistered_returns_none(self):
        factory = StubFactory()
        assert factory.get_or_none("unknown") is None

    def test_get_or_none_registered_returns_executor(self):
        factory = StubFactory()
        executor = StubExecutor("javascript")
        factory.register(executor)
        assert factory.get_or_none("javascript") is executor


class TestLanguageExecutorFactoryQueryMethods:
    def test_supported_languages_empty(self):
        factory = StubFactory()
        assert factory.supported_languages() == []

    def test_supported_languages_sorted(self):
        factory = StubFactory()
        factory.register(StubExecutor("typescript"))
        factory.register(StubExecutor("python"))
        factory.register(StubExecutor("javascript"))
        assert factory.supported_languages() == ["javascript", "python", "typescript"]

    def test_is_supported_true(self):
        factory = StubFactory()
        factory.register(StubExecutor("python"))
        assert factory.is_supported("python") is True

    def test_is_supported_false(self):
        factory = StubFactory()
        assert factory.is_supported("python") is False

    def test_available_runtimes_empty(self):
        factory = StubFactory()
        assert factory.available_runtimes() == []

    def test_available_runtimes_returns_all(self):
        factory = StubFactory()
        factory.register(StubExecutor("python"))
        factory.register(StubExecutor("javascript"))
        runtimes = factory.available_runtimes()
        assert len(runtimes) == 2
        lang_ids = {r.language_id for r in runtimes}
        assert lang_ids == {"python", "javascript"}


class TestLanguageExecutorFactoryOnePerLanguage:
    """Enforces I-27-10: one executor per language_id."""

    def test_one_executor_per_language(self):
        factory = StubFactory()
        for lang in ["python", "javascript", "typescript"]:
            factory.register(StubExecutor(lang))
        assert len(factory.supported_languages()) == 3

    def test_same_language_twice_rejected(self):
        factory = StubFactory()
        factory.register(StubExecutor("python"))
        with pytest.raises(ValueError):
            factory.register(StubExecutor("python"))
