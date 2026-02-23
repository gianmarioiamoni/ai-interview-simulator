# domain/contracts/execution_result.py

# execution result contract
#
# The execution result must:

# - Be associated with a question
# - Distinguish between execution type (coding / database)
# - Contain raw output
# - Indicate success/failure
# - Optionally contain error message
# - Be immutable
# - Not contain logic

from enum import Enum
from pydantic import BaseModel, Field, model_validator


class ExecutionType(str, Enum):
    CODING = "coding"
    DATABASE = "database"


class ExecutionResult(BaseModel):
    question_id: str = Field(..., min_length=1)
    execution_type: ExecutionType
    success: bool
    output: str = Field(default="")
    error: str | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_success_error_consistency(self) -> "ExecutionResult":
        if self.success and self.error is not None:
            raise ValueError("error must be None when success is True")
        if not self.success and not self.error:
            raise ValueError("error required when success is False")
        return self
