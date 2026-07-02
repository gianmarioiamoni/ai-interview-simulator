# infrastructure/execution/language_executor_registry.py

import threading
from typing import Optional

from infrastructure.execution.contracts.language_executor import LanguageExecutor
from infrastructure.execution.contracts.language_executor_factory import LanguageExecutorFactory
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime


class LanguageExecutorRegistry(LanguageExecutorFactory):
    """Thread-safe concrete implementation of LanguageExecutorFactory."""

    def __init__(self) -> None:
        self._executors: dict[str, LanguageExecutor] = {}
        self._lock = threading.Lock()

    def get(self, language_id: str) -> LanguageExecutor:
        with self._lock:
            if language_id not in self._executors:
                raise KeyError(f"No executor registered for language_id='{language_id}'")
            return self._executors[language_id]

    def get_or_none(self, language_id: str) -> Optional[LanguageExecutor]:
        with self._lock:
            return self._executors.get(language_id)

    def register(self, executor: LanguageExecutor) -> None:
        with self._lock:
            if executor.language_id in self._executors:
                raise ValueError(
                    f"Executor already registered for language_id='{executor.language_id}'"
                )
            self._executors[executor.language_id] = executor

    def supported_languages(self) -> list[str]:
        with self._lock:
            return sorted(self._executors.keys())

    def is_supported(self, language_id: str) -> bool:
        with self._lock:
            return language_id in self._executors

    def available_runtimes(self) -> list[ExecutionRuntime]:
        with self._lock:
            return [executor.runtime for executor in self._executors.values()]
