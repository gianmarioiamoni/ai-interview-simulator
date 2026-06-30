# domain/contracts/reasoning/reasoning_basis.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoning_confidence import ReasoningConfidence
from domain.contracts.reasoning.trend import Trend


class ReasoningBasis(BaseModel):
    """Structured provenance for a ReasonerDecision (ADR-035).

    All fields are structured data — no free text.
    NarrativeGenerator consumes this to produce candidate-facing language.
    """

    detected_patterns: list[EvidenceType] = Field(default_factory=list)
    dominant_dimension: ProfileDimension | None = None
    session_quality_trend: Trend = Trend.INSUFFICIENT_DATA
    follow_up_triggers: list[EvidenceType] = Field(default_factory=list)
    navigation_triggers: list[EvidenceType] = Field(default_factory=list)
    reasoning_confidence: ReasoningConfidence = Field(
        default_factory=ReasoningConfidence
    )

    model_config = {"frozen": True, "extra": "forbid"}
