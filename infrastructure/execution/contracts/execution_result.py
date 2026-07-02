# infrastructure/execution/contracts/execution_result.py

from typing import Optional
from pydantic import BaseModel, Field, model_validator

from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_metrics import ExecutionMetrics
from infrastructure.execution.contracts.execution_diagnostics import ExecutionDiagnostics
from infrastructure.execution.contracts.execution_artifact import ExecutionArtifact


class ExecutionTestResult(BaseModel):
    """Result of a single test case execution.

    Language-independent. test_id is an opaque string assigned by the harness.
    passed is the canonical pass/fail signal. error_message is present only
    when passed is False.
    """

    test_id: str = Field(..., min_length=1)
    passed: bool
    error_message: Optional[str] = Field(default=None)
    duration_ms: int = Field(default=0, ge=0)
    is_hidden: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def validate_error_consistency(self) -> "ExecutionTestResult":
        if self.passed and self.error_message is not None:
            raise ValueError("error_message must be None when passed is True")
        return self


class ExecutionResult(BaseModel):
    """Normalised, language-independent output of a LanguageExecutor.execute() call.

    This is the Infrastructure-to-Application boundary object (ADR-027 Section B).
    Its sole consumer within the Knowledge Pipeline is EvaluationEngine, which
    maps it to the Application/Domain boundary via the evaluation adapter.

    Invariant (I-27-9): Structure is language-independent. No language-specific
    fields, no language-specific status codes. Every concrete LanguageExecutor
    maps its outcome to this contract.

    ExecutionResult is frozen (immutable) once produced.
    """

    execution_id: str = Field(..., min_length=1)
    language_id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)

    status: ExecutionStatus
    exit_code: int = Field(default=0)
    timed_out: bool = Field(default=False)

    stdout: str = Field(default="")
    stderr: str = Field(default="")

    test_results: list[ExecutionTestResult] = Field(default_factory=list)
    runtime_errors: list[str] = Field(default_factory=list)

    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    diagnostics: ExecutionDiagnostics = Field(default_factory=ExecutionDiagnostics)
    artifacts: list[ExecutionArtifact] = Field(default_factory=list)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def validate_consistency(self) -> "ExecutionResult":
        if self.timed_out and self.status != ExecutionStatus.TIMEOUT:
            raise ValueError(
                "status must be TIMEOUT when timed_out is True"
            )
        if self.status == ExecutionStatus.TIMEOUT and not self.timed_out:
            raise ValueError(
                "timed_out must be True when status is TIMEOUT"
            )
        return self

    @property
    def passed(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS

    @property
    def tests_passed(self) -> int:
        return sum(1 for t in self.test_results if t.passed)

    @property
    def tests_failed(self) -> int:
        return sum(1 for t in self.test_results if not t.passed)

    @property
    def tests_total(self) -> int:
        return len(self.test_results)
