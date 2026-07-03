# services/coaching_engine/coaching_context.py
# CoachingContext — immutable input context for a CoachingEngine invocation (ADR-025, E04-M1)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_collection import CoachingCollection
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.language.language_profile import LanguageProfile
from domain.contracts.reasoning.candidate_profile import CandidateProfile


class CoachingContext(BaseModel):
    """Immutable input bundle for one CoachingEngine invocation.

    Carries all inputs required for the engine to produce a CoachingSnapshot
    without accessing ObservationStore, FeatureEngine,
    detectors, or Narrative.

    Invariants (ADR-025):
    - session_id and candidate_identity_id are non-empty.
    - question_index >= 0.
    - profile is the current CandidateProfile; never mutated here.
    - features contains the ProfileFeatures computed by FeatureEngine.
    - knowledge_gap_observation_ids references ObservationIDs only (strings).
      The engine never resolves these back to the ObservationStore.
    - learning_progress_summary is an optional opaque token; never used as
      a knowledge source — only carried through to output coherence labelling.
    - language_profile is the session-scoped language configuration.
    - interview_topic and interview_role are metadata labels, not knowledge
      sources.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    profile: CandidateProfile = Field(
        ..., description="Current CandidateProfile; read-only input, never mutated."
    )
    features: tuple[ProfileFeature, ...] = Field(
        default_factory=tuple,
        description="ProfileFeatures from FeatureEngine for this cycle.",
    )
    knowledge_gap_observation_ids: tuple[str, ...] = Field(
        default_factory=tuple,
        description="IDs of KNOWLEDGE_GAP observations; IDs only, no store access.",
    )
    learning_progress_summary: str | None = Field(
        default=None,
        description=(
            "Opaque progress token for output coherence only. "
            "Never used as a knowledge source."
        ),
    )
    language_profile: LanguageProfile | None = Field(
        default=None,
        description="Session language configuration; read-only metadata.",
    )
    interview_topic: str | None = Field(
        default=None,
        description="Interview topic label; metadata only.",
    )
    interview_role: str | None = Field(
        default=None,
        description="Interview role label; metadata only.",
    )
    prior_coaching_snapshot: CoachingCollection | None = Field(
        default=None,
        description=(
            "CoachingCollection from the prior cycle; used for deduplication "
            "of objectives only. Never a knowledge source."
        ),
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}
