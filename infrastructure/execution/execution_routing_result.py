# infrastructure/execution/execution_routing_result.py

from pydantic import BaseModel, Field


class ExecutionRoutingResult(BaseModel):
    """Result of routing resolution for an ExecutionRequest."""

    success: bool
    language_id: str
    executor_available: bool
    routing_errors: list[str] = Field(default_factory=list)
    routing_metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}
