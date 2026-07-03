# domain/contracts/identity/candidate_identity.py
# ADR-016A — CandidateIdentity (Aggregate Root; ownership anchor for all session knowledge)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CandidateIdentity(BaseModel):
    """Stable, immutable ownership anchor for all interview knowledge (ADR-016A).

    Aggregate Root. Not an authenticated user. Not an auth system concept.

    ADR-016A invariants:
    - candidate_identity_id is immutable after creation (assigned once; uuid4)
    - created_at is immutable after creation
    - schema_version is immutable after creation
    - display_name is the only mutable field (cosmetic; no downstream semantic effect)

    All fields except display_name are frozen via model semantics.
    Sole producer: session initialisation pipeline (V1.2).
    """

    candidate_identity_id: str = Field(
        ..., min_length=1, description="Stable opaque uuid4 identifier (ADR-016A §B)"
    )
    created_at: datetime = Field(
        ..., description="UTC creation timestamp; immutable after assignment"
    )
    schema_version: str = Field(
        default="1.0", min_length=1, description="Forward-compatible schema version"
    )
    display_name: Optional[str] = Field(
        default=None, description="Candidate-supplied optional name; only mutable field"
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def id(self) -> str:
        """Alias for candidate_identity_id."""
        return self.candidate_identity_id
