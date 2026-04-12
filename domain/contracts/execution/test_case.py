# domain/contracts/test_case.py

from pydantic import BaseModel, Field


class TestCase(BaseModel):

    input: str = Field(..., description="Input for the function")
    expected_output: str = Field(..., description="Expected output")

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
