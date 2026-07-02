# infrastructure/execution/execution_context.py

import uuid
from pydantic import BaseModel, Field

from infrastructure.execution.contracts.execution_request import ExecutionRequest


class ExecutionContext(BaseModel):
    """Assembled execution context before dispatch. Frozen."""

    request: ExecutionRequest
    executor_language_id: str
    dispatch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    routing_metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_request(cls, request: ExecutionRequest) -> "ExecutionContext":
        return cls(
            request=request,
            executor_language_id=request.language_id,
            dispatch_id=str(uuid.uuid4()),
            routing_metadata={
                "language_id": request.language_id,
                "execution_id": request.execution_id,
                "question_id": request.question_id,
            },
        )
