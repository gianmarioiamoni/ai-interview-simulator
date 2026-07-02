# infrastructure/execution/contracts/language_executor_factory.py

from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.execution.contracts.language_executor import LanguageExecutor
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime


class LanguageExecutorFactory(ABC):
    """Abstract factory for resolving LanguageExecutor by language_id.

    Infrastructure layer. Dispatches ExecutionRequests to the correct
    LanguageExecutor without any knowledge of Domain concepts.

    Invariant (I-27-10): One concrete LanguageExecutor per registered
    ProgrammingLanguage. The factory enforces this 1:1 mapping.

    Invariant: The factory never consults Domain layer to resolve executors.
    Resolution is purely by language_id string (opaque key).
    """

    @abstractmethod
    def get(self, language_id: str) -> LanguageExecutor:
        """Return the LanguageExecutor registered for language_id.

        Args:
            language_id: Stable language key (e.g. 'python', 'javascript').

        Returns:
            Concrete LanguageExecutor for the requested language.

        Raises:
            KeyError: if no executor is registered for language_id.
        """
        ...

    @abstractmethod
    def get_or_none(self, language_id: str) -> Optional[LanguageExecutor]:
        """Return the LanguageExecutor for language_id, or None if unregistered."""
        ...

    @abstractmethod
    def register(self, executor: LanguageExecutor) -> None:
        """Register a LanguageExecutor.

        Args:
            executor: Concrete LanguageExecutor to register.

        Raises:
            ValueError: if an executor for executor.language_id is already registered.
        """
        ...

    @abstractmethod
    def supported_languages(self) -> list[str]:
        """Return sorted list of registered language_id values."""
        ...

    @abstractmethod
    def is_supported(self, language_id: str) -> bool:
        """Return True if an executor is registered for language_id."""
        ...

    @abstractmethod
    def available_runtimes(self) -> list[ExecutionRuntime]:
        """Return ExecutionRuntime descriptors for all registered executors."""
        ...
