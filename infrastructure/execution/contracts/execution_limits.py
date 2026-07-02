# infrastructure/execution/contracts/execution_limits.py

from pydantic import BaseModel, Field, model_validator


class ExecutionLimits(BaseModel):
    """Resource constraints applied to a single code execution attempt.

    Owned by the Infrastructure layer. Derived from ExecutionPolicy
    (Domain) by the Application routing layer before dispatch.

    Invariant: timeout_ms, memory_limit_mb, and max_output_bytes represent
    hard limits enforced by the sandbox. Violations produce ExecutionStatus
    TIMEOUT or MEMORY_EXCEEDED respectively.
    """

    timeout_ms: int = Field(
        default=5_000,
        ge=100,
        le=60_000,
        description="Wall-clock execution limit in milliseconds",
    )
    memory_limit_mb: int = Field(
        default=128,
        ge=16,
        le=1024,
        description="Maximum heap + stack memory in megabytes",
    )
    max_output_bytes: int = Field(
        default=1_048_576,
        ge=1_024,
        le=10_485_760,
        description="Maximum combined stdout + stderr size in bytes (1 MiB default)",
    )
    max_processes: int = Field(
        default=1,
        ge=1,
        le=8,
        description="Maximum spawned subprocesses (1 = no child spawning)",
    )
    max_file_descriptors: int = Field(
        default=32,
        ge=4,
        le=256,
        description="File descriptor ceiling inside the sandbox",
    )
    network_access: bool = Field(
        default=False,
        description="Whether outbound network access is permitted; always False in V1.2",
    )
    filesystem_write: bool = Field(
        default=False,
        description="Whether filesystem writes are permitted; always False in V1.2",
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def validate_constraints(self) -> "ExecutionLimits":
        if self.network_access:
            raise ValueError("network_access must be False in V1.2 (I-27-6)")
        if self.filesystem_write:
            raise ValueError("filesystem_write must be False in V1.2 (I-27-6)")
        return self
