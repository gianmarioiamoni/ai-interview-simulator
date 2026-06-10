# domain/contracts/test_case.py

from typing import ClassVar

from pydantic import BaseModel, Field


class TestCase(BaseModel):

    # prevent pytest from collecting this domain model as a test class
    __test__: ClassVar[bool] = False

    input: str = Field(..., description="Input for the function")
    expected_output: str = Field(..., description="Expected output")

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
