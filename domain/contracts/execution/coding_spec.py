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

    # signature — bare identifier names only, no type annotations
    parameters: list[str] = Field(default_factory=list)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @model_validator(mode="after")
    def validate_spec(self):

        if self.type == "class_method":
            if not self.method_name:
                raise ValueError("method_name required for class_method")

        # Normalize: strip type annotations from parameter names.
        # LLMs sometimes emit "param: type" or "param: List[int]" inside the
        # parameters list. Strip everything after the first colon or space so
        # downstream harness and validator work with bare identifiers only.
        normalized: list[str] = []
        for p in self.parameters:
            bare = p.split(":")[0].split(" ")[0].strip()
            normalized.append(bare)

        object.__setattr__(self, "parameters", normalized)

        return self

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
