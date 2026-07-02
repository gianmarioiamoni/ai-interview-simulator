# services/narrative_generator/narrative_generation_context.py
# NarrativeGenerationContext — immutable input bundle for NarrativeGenerator (E03-M1, ADR-023)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.language.language_profile import LanguageProfile
from domain.contracts.reasoning.candidate_profile import CandidateProfile


class NarrativeGenerationContext(BaseModel):
    """Immutable input bundle for a single NarrativeGenerator invocation.

    Carries all read-only inputs required to produce a Narrative.

    ADR-023 invariants:
    - NarrativeGenerator never mutates CandidateProfile (N-01).
    - NarrativeGenerator never computes ProfileFeatures (constraint).
    - No ObservationStore, FeatureEngine internals, or detector outputs here.
    - No persistence, no replay.

    Inputs not yet modelled as domain contracts (KnowledgeGaps, EvaluationSummary)
    are represented as structured plain types until their contracts are formalised.
    """

    session_id: str = Field(..., min_length=1, description="Owning session")
    candidate_identity_id: str = Field(..., min_length=1, description="Candidate being assessed")
    question_index: int = Field(..., ge=0, description="Final question index of this session cycle")

    profile: CandidateProfile = Field(
        ..., description="Read-only CandidateProfile; never mutated (N-01)"
    )
    features: FeatureCollection = Field(
        ..., description="Pre-computed ProfileFeatures from FeatureEngine; never recomputed here"
    )
    language_profile: LanguageProfile | None = Field(
        default=None,
        description="Language configuration for the session; optional",
    )

    # Knowledge gaps expressed as a plain tuple of area strings.
    # Formalised as a domain contract in a later milestone.
    knowledge_gap_areas: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Knowledge gap area labels derived from ObservationStore; passed in, never read here",
    )

    # Evaluation summary as a plain mapping of dimension → label.
    # Formalised as a domain contract in a later milestone.
    evaluation_summary: dict[str, str] = Field(
        default_factory=dict,
        description="Per-dimension evaluation labels (e.g. dimension → 'HIGH'/'LOW')",
    )

    # Interview metadata (topic, level, etc.) as a plain mapping.
    # Formalised as a domain contract in a later milestone.
    interview_metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Interview-level metadata (e.g. topic, seniority_level)",
    )

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
