# domain/contracts/feature/feature_candidate.py
# FeatureCandidate — intermediate object produced by FeatureUpdater (ADR-020 §C, §E)

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_identity import FeatureIdentity


class FeatureCandidate(BaseModel):
    """Draft feature value produced by a FeatureUpdater before composition.

    FeatureCandidates are never committed to CandidateProfile directly.
    They are collected by FeatureEngine and resolved by FeatureComposer
    via FeatureMergePolicy or FeatureReplacementPolicy (ADR-020 §C, §E).

    Invariants:
    - candidate_confidence in [0.0, 1.0]
    - source_observation_ids is non-empty (every candidate must be traceable)
    - updater_id identifies the Updater that produced this candidate
    """

    feature_identity: FeatureIdentity = Field(
        ..., description="Stable identity of the feature type this candidate represents"
    )
    candidate_value: str = Field(
        ..., min_length=1, description="Proposed feature value (e.g. 'HIGH', 'LOW', 'MODERATE')"
    )
    candidate_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence estimate from the producing Updater"
    )
    source_observation_ids: tuple[str, ...] = Field(
        ...,
        min_length=1,
        description="ObservationId values this candidate was derived from"
    )
    computed_at_question_index: int = Field(
        ..., ge=0, description="Session position at which this candidate was produced"
    )
    updater_id: str = Field(
        ..., min_length=1, description="Identifier of the FeatureUpdater that produced this"
    )
    language_context: str | None = Field(
        default=None,
        description="Language context forwarded to LanguageCapabilityFeature provenance only"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
