# domain/contracts/feature/feature_provenance.py
# FeatureProvenance — full lineage from ProfileFeature to source Observations (ADR-020 §G)

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_identity import FeatureIdentity


class FeatureProvenance(BaseModel):
    """Full lineage record linking a ProfileFeature back to its source Observations.

    Immutable once FeatureEngine emits the ProfileFeature. When FeatureEngine
    recomputes a feature, a new FeatureProvenance is produced — the prior record
    is never mutated (ADR-018 §F, ADR-020 §G).

    Required fields per ADR-020 §G:
    - source_observation_ids
    - feature_identity
    - schema_version
    - computed_at_question_index
    - feature_engine_version
    - updater_id
    """

    feature_identity: FeatureIdentity = Field(
        ..., description="Stable identity — unchanged across schema versions"
    )
    source_observation_ids: tuple[str, ...] = Field(
        default=(),
        description="ObservationId values from which this feature was derived"
    )
    computed_at_question_index: int = Field(
        ..., ge=0, description="Session position at which this provenance record was assembled"
    )
    feature_engine_version: str = Field(
        ..., min_length=1, description="FeatureEngine version that produced this feature"
    )
    updater_id: str = Field(
        ..., min_length=1, description="Which Updater(s) contributed to this feature"
    )
    superseded_observation_ids: tuple[str, ...] = Field(
        default=(),
        description="ObservationId values from a discarded candidate (FeatureReplacementPolicy)"
    )
    language_context: str | None = Field(
        default=None,
        description=(
            "Programming language context — set only for LanguageCapabilityFeature "
            "(the one taxonomy exception per ADR-018 §D)"
        ),
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
