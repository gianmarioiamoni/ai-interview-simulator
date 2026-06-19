# domain/contracts/execution/execution_test_result.py

from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from enum import Enum
from pydantic import BaseModel, Field, WithJsonSchema


_AnyValue = Annotated[Any, WithJsonSchema({"type": "string", "description": "serialized value"})]
_AnyOptValue = Annotated[Optional[Any], WithJsonSchema({"anyOf": [{"type": "string", "description": "serialized value"}, {"type": "null"}]})]
_AnyDict = Annotated[Dict[str, Any], WithJsonSchema({"type": "object", "additionalProperties": {"type": "string"}})]
_AnyList = Annotated[List[Any], WithJsonSchema({"type": "array", "items": {"type": "string"}})]


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

    expected: _AnyOptValue = None
    actual: _AnyOptValue = None

    error: Optional[str] = None

    args: _AnyList = Field(default_factory=list)
    kwargs: _AnyDict = Field(default_factory=dict)

    model_config = {"frozen": True}
