# infrastructure/execution/contracts/execution_request.py

from pydantic import BaseModel, Field, model_validator

from infrastructure.execution.contracts.execution_limits import ExecutionLimits
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment


class ExecutionRequest(BaseModel):
    """Complete input contract for a LanguageExecutor.execute() call.

    Assembles all data needed to execute candidate code against a hidden test
    suite. Constructed by the Application routing layer from LanguageConfig,
    Question, CandidateCode, HiddenTests, and ExecutionPolicy.

    Invariant (I-27-1): ExecutionRequest contains no Domain concepts.
    question_id and candidate_code are opaque strings at this boundary.
    hidden_test_suite is a raw code string; its structure is executor-specific.
    """

    execution_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this execution event (UUID recommended)",
    )
    question_id: str = Field(
        ...,
        min_length=1,
        description="Opaque question identifier; executor does not interpret this",
    )
    language_id: str = Field(
        ...,
        min_length=1,
        description="Target language; must match LanguageExecutor.language_id",
    )
    candidate_code: str = Field(
        ...,
        min_length=1,
        description="Raw candidate solution code string",
    )
    hidden_test_suite: str = Field(
        default="",
        description="Raw hidden test code; empty means no test harness (dry-run only)",
    )
    visible_test_suite: str = Field(
        default="",
        description="Visible test code included in harness for candidate feedback",
    )
    environment: ExecutionEnvironment = Field(
        ...,
        description="Target runtime environment specification",
    )
    limits: ExecutionLimits = Field(
        default_factory=ExecutionLimits,
        description="Resource limits for this execution attempt",
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def validate_request_fields(self) -> "ExecutionRequest":
        if not self.candidate_code.strip():
            raise ValueError("candidate_code must not be whitespace-only")
        if self.language_id != self.environment.language_id:
            raise ValueError(
                f"language_id '{self.language_id}' must match "
                f"environment.language_id '{self.environment.language_id}'"
            )
        return self
