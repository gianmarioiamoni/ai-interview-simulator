# infrastructure/execution/contracts/language_executor.py

from abc import ABC, abstractmethod

from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime


class LanguageExecutor(ABC):
    """Abstract base for all language-specific code executors.

    Infrastructure layer. One concrete implementation per registered
    ProgrammingLanguage (I-27-10).

    LanguageExecutor is blind to all Domain concepts (I-27-1):
    - No knowledge of CandidateProfile
    - No knowledge of FeatureEngine
    - No knowledge of Observation or session evaluation state
    - No knowledge of SessionHistory, Narrative, or Coaching

    Responsibility: Accept ExecutionRequest → return ExecutionResult.
    Nothing else.
    """

    @property
    @abstractmethod
    def language_id(self) -> str:
        """Stable identifier matching ProgrammingLanguage.language_id."""
        ...

    @property
    @abstractmethod
    def runtime(self) -> ExecutionRuntime:
        """Runtime configuration for this executor."""
        ...

    @abstractmethod
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute candidate code against the hidden test suite.

        Args:
            request: Complete, validated ExecutionRequest.

        Returns:
            ExecutionResult with normalised, language-independent structure.

        Raises:
            ValueError: if request.language_id does not match self.language_id.

        Invariants enforced by contract (not by this method):
        - I-27-2: never produces EvidenceSignal
        - I-27-3: never produces Observation
        - I-27-4: never writes to CandidateProfile
        - I-27-5: never writes to SessionHistory
        - I-27-7: never reasons about candidate capability
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the execution runtime is reachable and healthy.

        Used by the Application routing layer to detect degraded executors
        before dispatching. Must not raise; return False on any runtime error.
        """
        ...

    def validate_request(self, request: ExecutionRequest) -> None:
        """Guard: raise ValueError if request.language_id != self.language_id."""
        if request.language_id != self.language_id:
            raise ValueError(
                f"LanguageExecutor '{self.language_id}' received request "
                f"for language '{request.language_id}' (I-27-10)"
            )
