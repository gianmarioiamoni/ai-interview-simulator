# domain/contracts/feature/profile_feature.py
# ProfileFeature — central V1.2 knowledge unit (ADR-018 §C, ADR-020 §E)

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import FeatureQuality


class ProfileFeature(BaseModel):
    """Named, versionable, confidence-weighted characteristic of a candidate.

    Synthesised by FeatureEngine (sole producer) from Observations in ObservationStore.
    Immutable per computation cycle: recomputation produces a NEW object — never
    a mutation of the prior one (ADR-018 §C).

    Invariants (ADR-018 §C):
    - feature_identity.feature_type_id never references a programming language
    - confidence in [0.0, 1.0]
    - FeatureEngine is the only permitted producer (Domain Invariant I-02)
    - schema_version travels with the feature for replay/cross-session comparison

    Language independence (ADR-018 §L):
    - All feature types are language-independent.
    - LanguageCapabilityFeature is the sole exception; language_context appears
      in provenance.language_context only — never in feature_type or value.
    """

    feature_identity: FeatureIdentity = Field(
        ..., description="Stable identity across schema versions and sessions"
    )
    value: str = Field(
        ..., min_length=1, description="Current feature value (e.g. 'HIGH', 'LOW', 'MODERATE')"
    )
    quality: FeatureQuality = Field(
        ..., description="Confidence, stability, and maturity envelope"
    )
    provenance: FeatureProvenance = Field(
        ..., description="Full lineage back to source Observations"
    )
    computed_at_question_index: int = Field(
        ..., ge=0, description="Session position at which this feature was last computed"
    )
    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    schema_version: str = Field(
        default="1.0",
        description="Feature schema version; travels with the feature for replay compatibility",
    )

    model_config = {"frozen": True, "extra": "forbid"}
