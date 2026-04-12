# domain/contracts/retrieval_metadata.py

# Retrieval metadata contract
#
# Strongly-typed metadata associated with retrieval documents.
# Used for filtering, traceability and governance.
#
# Responsibility: immutable and schema-governed metadata container.

from pydantic import BaseModel, Field
from typing import Optional

from domain.contracts.role import Role
from domain.contracts.interview_area import InterviewArea


class RetrievalMetadata(BaseModel):
    role: Role
    area: InterviewArea

    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    source: Optional[str] = Field(default=None, min_length=1)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
