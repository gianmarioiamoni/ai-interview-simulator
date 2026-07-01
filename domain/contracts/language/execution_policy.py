# domain/contracts/language/execution_policy.py

from pydantic import BaseModel, Field


class ExecutionPolicy(BaseModel):
    """Execution parameters for a specific programming language in a session.

    Owned by the Domain layer as a configuration value object. Contains
    language-specific execution limits. Does NOT reference any sandbox,
    runtime, or infrastructure technology (ADR-019 I-22).

    ExecutionPolicy is immutable once created for a session — changes to
    defaults do not affect running or completed sessions (ADR-019 Section E).
    """

    language_id: str = Field(
        ..., min_length=1, description="Language this policy applies to"
    )
    timeout_ms: int = Field(
        default=5000, ge=100, le=60_000,
        description="Maximum execution wall-clock time in milliseconds"
    )
    memory_limit_mb: int = Field(
        default=128, ge=16, le=1024,
        description="Maximum memory allocation in megabytes"
    )
    max_retry_on_transient_error: int = Field(
        default=1, ge=0, le=3,
        description="Retry count for transient execution failures (not logic errors)"
    )
    import_allowlist: list[str] = Field(
        default_factory=list,
        description="Standard library modules permitted; empty list means all standard lib allowed"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
