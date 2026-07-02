# infrastructure/execution/contracts/execution_artifact.py

from enum import Enum
from pydantic import BaseModel, Field


class ArtifactKind(str, Enum):
    """Taxonomy of artifacts produced during code execution."""

    STDOUT = "stdout"
    STDERR = "stderr"
    COMPILED_BYTECODE = "compiled_bytecode"
    TRANSPILED_SOURCE = "transpiled_source"
    COVERAGE_REPORT = "coverage_report"
    PROFILE_TRACE = "profile_trace"
    SANDBOX_LOG = "sandbox_log"


class ExecutionArtifact(BaseModel):
    """A named output artifact produced during a code execution.

    Artifacts are captured by the sandbox and attached to ExecutionResult.
    They are Infrastructure-only data — no Domain concept reads artifact content.

    kind classifies the artifact. name is a stable human-readable label.
    content is the raw string payload (text artifacts only; binary not supported
    in V1.2). size_bytes is the byte length of content at capture time.
    truncated is True when content was clipped due to ExecutionLimits.max_output_bytes.
    """

    kind: ArtifactKind
    name: str = Field(..., min_length=1)
    content: str = Field(default="")
    size_bytes: int = Field(default=0, ge=0)
    truncated: bool = Field(default=False)
    encoding: str = Field(default="utf-8")

    model_config = {"frozen": True, "extra": "forbid"}
