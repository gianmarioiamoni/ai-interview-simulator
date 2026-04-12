# domain/contracts/test_execution_result.py

from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class TestType(str, Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class TestExecutionResult(BaseModel):
    id: int
    type: TestType
    status: TestStatus

    expected: Optional[Any] = None
    actual: Optional[Any] = None

    error: Optional[str] = None

    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}
