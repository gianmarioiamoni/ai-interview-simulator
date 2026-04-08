# domain/contracts/coding_spec.py

from pydantic import BaseModel, Field

class CodingSpec(BaseModel):
    function_name: str = Field(..., min_length=1)
    parameters: list[str] = Field(default_factory=list)
    is_class_based: bool = Field(default=False)
    class_name: str | None = Field(default=None)
    method_name: str | None = Field(default=None)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }