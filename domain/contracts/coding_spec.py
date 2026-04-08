# domain/contracts/coding_spec.py

from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional


class CodingSpec(BaseModel):
    # ---------------------------------------------------------
    # Callable definition
    # ---------------------------------------------------------

    type: Literal["function", "class_method"] = "function"

    # function OR class name
    entrypoint: str = Field(..., min_length=1)

    # only for class_method
    method_name: Optional[str] = None

    # signature
    parameters: list[str] = Field(default_factory=list)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @model_validator(mode="after")
    def validate_spec(self):

        if self.type == "class_method":
            if not self.method_name:
                raise ValueError("method_name required for class_method")

        return self

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
