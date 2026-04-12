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

from pydantic import BaseModel, Field


class CodingTestCase(BaseModel):
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    expected: Any

    model_config = {"frozen": True}
