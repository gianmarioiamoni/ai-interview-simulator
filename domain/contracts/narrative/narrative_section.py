# domain/contracts/narrative/narrative_section.py
# ADR-023 Section C — NarrativeSection (thematic structural unit)

from pydantic import BaseModel, Field, model_validator

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType


class NarrativeSection(BaseModel):
    """One thematic segment of a Narrative, grounded in one or more ProfileFeatures.

    ADR-023 invariants:
    - C-01: feature_references must be non-empty; a section with zero feature
      references is architecturally forbidden.
    - is_evidence_grounded must be True; False is an invariant violation.
    - prose is LLM-generated; section_type and feature_references are deterministic
      (ADR-023 Principle 3 & 4).

    No LLM calls, no CandidateProfile mutation, no Coaching, no Report.
    """

    section_type: NarrativeSectionType
    prose: str = Field(..., min_length=1, description="LLM-generated; variable")
    feature_references: tuple[FeatureIdentity, ...] = Field(
        ...,
        min_length=1,
        description="ProfileFeatures grounding this section; must be non-empty (C-01)"
    )
    confidence_context: str = Field(
        ..., min_length=1,
        description="LLM-generated description of evidence confidence"
    )
    is_evidence_grounded: bool = Field(
        default=True,
        description="Must be True; False is an invariant violation (C-01)"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _evidence_grounding_invariant(self) -> "NarrativeSection":
        if not self.is_evidence_grounded:
            raise ValueError(
                "NarrativeSection.is_evidence_grounded must be True (ADR-023 C-01). "
                "A section with no feature references is architecturally forbidden."
            )
        if len(self.feature_references) == 0:
            raise ValueError(
                "NarrativeSection.feature_references must be non-empty (ADR-023 C-01)."
            )
        return self
