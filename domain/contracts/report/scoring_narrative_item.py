# domain/contracts/report/scoring_narrative_item.py

from __future__ import annotations

from pydantic import BaseModel, Field


class ScoringNarrativeItem(BaseModel):
    """Immutable coaching narrative item.

    Represents one entry in a ScoringNarrative coaching section
    (held_you_back, knowledge_gaps, next_strategy). The context_detail
    field consolidates section-specific keys (impact, interview_impact,
    expected_improvement) into a single optional field.
    """

    model_config = {"frozen": True, "extra": "forbid"}

    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    context_detail: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "category": self.category,
            "description": self.description,
            "why_it_matters": self.why_it_matters,
            "context_detail": self.context_detail,
        }
