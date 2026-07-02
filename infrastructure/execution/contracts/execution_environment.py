# infrastructure/execution/contracts/execution_environment.py

from pydantic import BaseModel, Field, model_validator


class ExecutionEnvironment(BaseModel):
    """Describes the runtime environment in which code is executed.

    Infrastructure-only. Never surfaces to Domain or Application layers.

    runtime_id identifies the concrete execution engine (e.g. 'cpython-3.12',
    'nodejs-22', 'tsc-5.4'). sandbox_type identifies the isolation mechanism
    ('subprocess', 'jvm', 'wasm', 'container'). Both fields are opaque to Domain.
    """

    language_id: str = Field(
        ...,
        min_length=1,
        description="Language this environment runs (e.g. 'python', 'javascript')",
    )
    runtime_id: str = Field(
        ...,
        min_length=1,
        description="Concrete runtime identifier (e.g. 'cpython-3.12', 'nodejs-22')",
    )
    runtime_version: str = Field(
        ...,
        min_length=1,
        description="Exact runtime version string",
    )
    sandbox_type: str = Field(
        ...,
        min_length=1,
        description="Isolation mechanism ('subprocess', 'docker', 'jvm', 'wasm')",
    )
    import_allowlist: list[str] = Field(
        default_factory=list,
        description="Module names explicitly permitted; empty = all stdlib allowed",
    )
    import_blocklist: list[str] = Field(
        default_factory=list,
        description="Module names explicitly forbidden; takes precedence over allowlist",
    )
    env_vars: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables injected into the execution sandbox",
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def validate_allowlist_blocklist_disjoint(self) -> "ExecutionEnvironment":
        overlap = set(self.import_allowlist) & set(self.import_blocklist)
        if overlap:
            raise ValueError(
                f"import_allowlist and import_blocklist overlap: {sorted(overlap)}"
            )
        return self
