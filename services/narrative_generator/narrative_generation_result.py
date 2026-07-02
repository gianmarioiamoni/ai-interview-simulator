# services/narrative_generator/narrative_generation_result.py
# NarrativeGenerationResult — immutable output of NarrativeGenerator (E03-M1, ADR-023)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.narrative.narrative import Narrative
from services.narrative_generator.narrative_generation_diagnostics import (
    NarrativeGenerationDiagnostics,
)


class NarrativeGenerationResult(BaseModel):
    """Immutable output of a single NarrativeGenerator run.

    ADR-023 invariants:
    - narrative is None only when is_successful is False.
    - diagnostics is always present regardless of success/failure.
    - failure_reason is non-None only when is_successful is False.
    - This object is terminal: nothing downstream writes back (N-04).
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    narrative: Narrative | None = Field(
        default=None,
        description="Produced Narrative; None when generation failed before assembly.",
    )
    diagnostics: NarrativeGenerationDiagnostics = Field(
        ..., description="Full audit trail for this generation run."
    )
    is_successful: bool = Field(default=True)
    failure_reason: str | None = Field(default=None)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def has_narrative(self) -> bool:
        return self.narrative is not None
