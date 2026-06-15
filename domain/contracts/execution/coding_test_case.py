# domain/contracts/coding_test_case.py

# CodingTestCase
#
# Represents a single test case for coding questions.
# It defines:
# - positional arguments
# - keyword arguments
# - expected output
# Immutable and validation-only.

from typing import Any, Dict, List
from typing_extensions import Annotated

from pydantic import BaseModel, Field, WithJsonSchema


_AnyValue = Annotated[Any, WithJsonSchema({"type": "string", "description": "serialized value"})]
_AnyDict = Annotated[Dict[str, Any], WithJsonSchema({"type": "object", "additionalProperties": {"type": "string"}})]
_AnyList = Annotated[List[Any], WithJsonSchema({"type": "array", "items": {"type": "string"}})]


class CodingTestCase(BaseModel):
    args: _AnyList = Field(default_factory=list)
    kwargs: _AnyDict = Field(default_factory=dict)
    expected: _AnyValue

    model_config = {"frozen": True}
