# domain/contracts/execution_result.py

# ExecutionResult contract
#
# Represents the structured result of a coding or database execution.
#
# Requirements
# The execution result must:
# - be associated with a question
# - distinguish execution type (coding / database)
# - indicate structured status
# - contain raw output
# - indicate success/failure
# - optionally contain error message
# - support test statistics (for coding engine)
# - be immutable
# - not contain logic beyond validation

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ExecutionType(str, Enum):
    CODING = "coding"
    DATABASE = "database"


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED_TESTS = "failed_tests"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    INTERNAL_ERROR = "internal_error"


class ExecutionResult(BaseModel):
    # Association
    question_id: str = Field(..., min_length=1)
    execution_type: ExecutionType

    # Structured status
    status: ExecutionStatus
    success: bool

    # Raw execution data
    output: str = Field(default="")
    error: Optional[str] = None

    # Test statistics (primarily for coding engine)
    passed_tests: int = Field(default=0, ge=0)
    total_tests: int = Field(default=0, ge=0)

    # Performance
    execution_time_ms: int = Field(default=0, ge=0)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_consistency(self) -> "ExecutionResult":
        # Success consistency
        if self.success and self.status != ExecutionStatus.SUCCESS:
            raise ValueError("status must be SUCCESS when success is True")

        if not self.success and self.status == ExecutionStatus.SUCCESS:
            raise ValueError("success cannot be False when status is SUCCESS")

        # Error consistency
        if self.success and self.error is not None:
            raise ValueError("error must be None when success is True")

        if not self.success and not self.error:
            raise ValueError("error required when success is False")

        # Test consistency
        if self.passed_tests > self.total_tests:
            raise ValueError("passed_tests cannot exceed total_tests")

        return self
