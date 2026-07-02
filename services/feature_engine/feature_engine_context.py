# services/feature_engine/feature_engine_context.py
# FeatureEngineContext — immutable invocation context (ADR-020 §C, §E)

from pydantic import BaseModel, Field

from domain.contracts.observation.observation_snapshot import ObservationSnapshot


class FeatureEngineContext(BaseModel):
    """Immutable context for a single FeatureEngine computation cycle.

    Carries all inputs the FeatureEngine and its Updaters need to operate —
    no mutable state, no infrastructure references.

    Invariants (ADR-020 §E, §H):
    - session_id identifies the owning session.
    - candidate_identity_id owns the CandidateProfile being computed.
    - current_question_index is the session position triggering this cycle.
    - snapshot is the ordered, freshness-filtered ObservationStore view.
    - feature_engine_version travels to all emitted ProfileFeature.provenance records.
    - is_replay distinguishes live from replay paths (ADR-020 §H).
    """

    session_id: str = Field(..., min_length=1, description="Session identifier")
    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    current_question_index: int = Field(
        ..., ge=0, description="Session position triggering this computation cycle"
    )
    snapshot: ObservationSnapshot = Field(
        ..., description="Ordered, freshness-filtered ObservationStore snapshot"
    )
    feature_engine_version: str = Field(
        default="1.0.0", min_length=1, description="FeatureEngine version for provenance"
    )
    is_replay: bool = Field(
        default=False,
        description="True when this cycle runs on the replay path (ReplayUpdater only)"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
