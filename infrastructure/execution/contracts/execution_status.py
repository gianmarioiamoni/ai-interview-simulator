# infrastructure/execution/contracts/execution_status.py

from enum import Enum


class ExecutionStatus(str, Enum):
    """Normalised terminal state of a code execution attempt.

    Language-independent. One concrete LanguageExecutor maps its language-specific
    outcome to exactly one ExecutionStatus value before returning ExecutionResult.

    Invariant (I-27-9): The status taxonomy is fixed at this layer.
    No language-specific statuses are permitted in ExecutionResult.
    """

    SUCCESS = "success"
    FAILED_TESTS = "failed_tests"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    COMPILATION_ERROR = "compilation_error"
    SANDBOX_VIOLATION = "sandbox_violation"
    INTERNAL_ERROR = "internal_error"

    @property
    def is_terminal_success(self) -> bool:
        return self == ExecutionStatus.SUCCESS

    @property
    def is_execution_failure(self) -> bool:
        return self in {
            ExecutionStatus.FAILED_TESTS,
            ExecutionStatus.SYNTAX_ERROR,
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.COMPILATION_ERROR,
        }

    @property
    def is_infrastructure_failure(self) -> bool:
        return self in {
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.MEMORY_EXCEEDED,
            ExecutionStatus.SANDBOX_VIOLATION,
            ExecutionStatus.INTERNAL_ERROR,
        }
