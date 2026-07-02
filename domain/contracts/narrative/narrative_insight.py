# domain/contracts/narrative/narrative_insight.py
# ADR-023 Section C — NarrativeInsight (atomic evidence-grounded finding)

from pydantic import BaseModel, Field, model_validator

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType


class NarrativeInsight(BaseModel):
    """Atomic finding about the candidate grounded in exactly one ProfileFeature.

    ADR-023 invariants:
    - C-02: source_feature_id is always present; a NarrativeInsight without a
      traceable ProfileFeature is architecturally forbidden.
    - N-05: Every statement is traceable; absence of a ProfileFeature means silence.
    - is_traceable must be True; False is an invariant violation.

    prose is LLM-generated; all other fields are deterministic (ADR-023 Principle 4).
    No LLM, no CandidateProfile mutation, no Coaching, no Report.
    """

    insight_type: NarrativeInsightType
    prose: str = Field(..., min_length=1, description="LLM-generated; variable")
    source_feature_id: FeatureIdentity = Field(
        ..., description="Exactly one ProfileFeature this insight traces to (C-02)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Inherited from source ProfileFeature confidence"
    )
    is_traceable: bool = Field(
        default=True,
        description="Must be True; False is an invariant violation (C-02, N-05)"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _traceability_invariant(self) -> "NarrativeInsight":
        if not self.is_traceable:
            raise ValueError(
                "NarrativeInsight.is_traceable must be True (ADR-023 C-02, N-05). "
                "A NarrativeInsight without a traceable ProfileFeature is forbidden."
            )
        return self
