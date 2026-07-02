# infrastructure/execution/contracts/execution_runtime.py

from pydantic import BaseModel, Field

from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_limits import ExecutionLimits


class ExecutionRuntime(BaseModel):
    """Describes the combined runtime + limits configuration for an executor.

    Assembles ExecutionEnvironment (what runtime) and ExecutionLimits (what
    constraints). Used internally by LanguageExecutor to configure its sandbox
    before dispatching an ExecutionRequest.

    Infrastructure-only. Never surfaces to Domain or Application layers.
    """

    environment: ExecutionEnvironment
    limits: ExecutionLimits = Field(default_factory=ExecutionLimits)
    runtime_label: str = Field(
        ...,
        min_length=1,
        description="Human-readable runtime label for logging (e.g. 'python-3.12-subprocess')",
    )
    supports_compilation: bool = Field(
        default=False,
        description="True for languages requiring a compile step (TypeScript, Java, Go, Rust)",
    )
    supports_coverage: bool = Field(
        default=False,
        description="Reserved for V1.3+; coverage reporting infrastructure hook",
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def language_id(self) -> str:
        return self.environment.language_id

    @property
    def runtime_id(self) -> str:
        return self.environment.runtime_id
