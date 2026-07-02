# infrastructure/execution/execution_pipeline.py

from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.execution_dispatcher import ExecutionDispatcher
from infrastructure.execution.execution_lifecycle import ExecutionLifecycle, ExecutionPhase
from infrastructure.execution.execution_validator import ExecutionValidator


def _internal_error(request: ExecutionRequest, error_msg: str) -> ExecutionResult:
    return ExecutionResult(
        execution_id=request.execution_id,
        language_id=request.language_id,
        question_id=request.question_id,
        status=ExecutionStatus.INTERNAL_ERROR,
        exit_code=-1,
        runtime_errors=[error_msg],
    )


class ExecutionPipeline:
    """Orchestrates validate → dispatch → collect result. Never raises."""

    def __init__(self, dispatcher: ExecutionDispatcher) -> None:
        self._dispatcher = dispatcher
        self._validator = ExecutionValidator()

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        lifecycle = ExecutionLifecycle()
        lifecycle.start()

        try:
            lifecycle.transition(ExecutionPhase.PRE_VALIDATION)
            errors = self._validator.validate(request)
            if errors:
                result = _internal_error(request, f"Validation failed: {'; '.join(errors)}")
                lifecycle.fail(f"Validation errors: {errors}")
                return result

            lifecycle.transition(ExecutionPhase.DISPATCH)
            result = self._dispatcher.dispatch(request)

            lifecycle.transition(ExecutionPhase.POST_PROCESSING)
            lifecycle.complete(result)
            return result

        except Exception as exc:
            lifecycle.fail(str(exc))
            return _internal_error(request, f"Pipeline internal error: {exc}")
