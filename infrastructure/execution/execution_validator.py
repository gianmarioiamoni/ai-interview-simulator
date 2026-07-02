# infrastructure/execution/execution_validator.py

from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_limits import ExecutionLimits

_TIMEOUT_MAX = 60_000
_MEMORY_MAX = 1024
_OUTPUT_MAX = 10_485_760


class ExecutionValidator:
    """Validates ExecutionRequest before dispatch."""

    def validate(self, request: ExecutionRequest) -> list[str]:
        errors: list[str] = []

        if not request.execution_id or not request.execution_id.strip():
            errors.append("execution_id must not be empty")

        if not request.language_id or not request.language_id.strip():
            errors.append("language_id must not be empty")

        if not request.candidate_code or not request.candidate_code.strip():
            errors.append("candidate_code must not be empty or whitespace-only")

        if request.language_id and request.language_id != request.environment.language_id:
            errors.append(
                f"language_id '{request.language_id}' does not match "
                f"environment.language_id '{request.environment.language_id}'"
            )

        limits = request.limits
        if limits.timeout_ms < 100 or limits.timeout_ms > _TIMEOUT_MAX:
            errors.append(
                f"timeout_ms {limits.timeout_ms} out of bounds [100, {_TIMEOUT_MAX}]"
            )
        if limits.memory_limit_mb < 16 or limits.memory_limit_mb > _MEMORY_MAX:
            errors.append(
                f"memory_limit_mb {limits.memory_limit_mb} out of bounds [16, {_MEMORY_MAX}]"
            )
        if limits.max_output_bytes < 1024 or limits.max_output_bytes > _OUTPUT_MAX:
            errors.append(
                f"max_output_bytes {limits.max_output_bytes} out of bounds [1024, {_OUTPUT_MAX}]"
            )
        if limits.network_access:
            errors.append("network_access must be False")
        if limits.filesystem_write:
            errors.append("filesystem_write must be False")

        return errors
