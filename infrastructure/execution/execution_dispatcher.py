# infrastructure/execution/execution_dispatcher.py

from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.language_executor_registry import LanguageExecutorRegistry


def _internal_error_result(request: ExecutionRequest, error_msg: str) -> ExecutionResult:
    return ExecutionResult(
        execution_id=request.execution_id,
        language_id=request.language_id,
        question_id=request.question_id,
        status=ExecutionStatus.INTERNAL_ERROR,
        exit_code=-1,
        runtime_errors=[error_msg],
    )


class ExecutionDispatcher:
    """Routes ExecutionRequest to the correct LanguageExecutor. Never raises."""

    def __init__(self, registry: LanguageExecutorRegistry) -> None:
        self._registry = registry

    def dispatch(self, request: ExecutionRequest) -> ExecutionResult:
        executor = self._registry.get_or_none(request.language_id)
        if executor is None:
            return _internal_error_result(
                request,
                f"No executor registered for language_id='{request.language_id}'",
            )

        try:
            available = executor.is_available()
        except Exception as exc:
            return _internal_error_result(
                request,
                f"Executor availability check failed: {exc}",
            )

        if not available:
            return _internal_error_result(
                request,
                f"Executor for language_id='{request.language_id}' is not available",
            )

        try:
            return executor.execute(request)
        except Exception as exc:
            return _internal_error_result(
                request,
                f"Executor raised unexpected exception: {exc}",
            )
