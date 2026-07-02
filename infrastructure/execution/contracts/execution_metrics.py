# infrastructure/execution/contracts/execution_metrics.py

from pydantic import BaseModel, Field, model_validator


class ExecutionMetrics(BaseModel):
    """Quantitative runtime measurements captured during code execution.

    Infrastructure-only. Attached to ExecutionResult for observability and
    post-execution analysis. Never read by Domain layer.

    All timing values are in milliseconds. Memory values are in kilobytes.
    """

    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Total wall-clock execution duration in milliseconds",
    )
    cpu_time_ms: int = Field(
        default=0,
        ge=0,
        description="CPU time consumed (user + system) in milliseconds",
    )
    peak_memory_kb: int = Field(
        default=0,
        ge=0,
        description="Peak memory usage in kilobytes",
    )
    stdout_bytes: int = Field(
        default=0,
        ge=0,
        description="Captured stdout size in bytes",
    )
    stderr_bytes: int = Field(
        default=0,
        ge=0,
        description="Captured stderr size in bytes",
    )
    tests_total: int = Field(
        default=0,
        ge=0,
        description="Total number of test cases executed",
    )
    tests_passed: int = Field(
        default=0,
        ge=0,
        description="Number of test cases that passed",
    )
    tests_failed: int = Field(
        default=0,
        ge=0,
        description="Number of test cases that failed",
    )
    tests_errored: int = Field(
        default=0,
        ge=0,
        description="Number of test cases that raised an unexpected error",
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of transient-error retries performed",
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def validate_test_counts(self) -> "ExecutionMetrics":
        derived_total = self.tests_passed + self.tests_failed + self.tests_errored
        if self.tests_total > 0 and derived_total != self.tests_total:
            raise ValueError(
                f"tests_total ({self.tests_total}) must equal "
                f"tests_passed + tests_failed + tests_errored ({derived_total})"
            )
        return self

    @property
    def pass_rate(self) -> float:
        if self.tests_total == 0:
            return 0.0
        return self.tests_passed / self.tests_total

    @property
    def memory_limit_ratio(self) -> float:
        """Fraction of memory used relative to 1 GiB. Informational only."""
        max_kb = 1_048_576
        return min(self.peak_memory_kb / max_kb, 1.0)
