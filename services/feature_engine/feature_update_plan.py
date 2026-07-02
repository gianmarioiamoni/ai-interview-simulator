# services/feature_engine/feature_update_plan.py
# FeatureUpdatePlan — which Updaters to invoke and which features to recompute (ADR-020 §H)

from pydantic import BaseModel, Field


class UpdaterInvocationSpec(BaseModel):
    """Specification for invoking a single FeatureUpdater in a cycle.

    Carries the updater identity and the set of feature_type_ids it should
    target in this invocation (may be a subset for incremental mode).
    """

    updater_id: str = Field(..., min_length=1)
    invocation_order: int = Field(..., ge=0)
    target_feature_type_ids: frozenset[str] = Field(
        default_factory=frozenset,
        description="feature_type_ids to (re)compute; empty = compute all registered"
    )
    is_incremental: bool = Field(
        default=False,
        description="True when this invocation targets only delta observations"
    )

    model_config = {"frozen": True, "extra": "forbid"}


class FeatureUpdatePlan(BaseModel):
    """Deterministic plan describing exactly what FeatureEngine will compute this cycle.

    Produced by FeatureEngine before invoking any Updater. Immutable once built.
    Consumers (e.g. diagnostics) may inspect the plan to understand what work
    was scheduled without inspecting runtime internals.

    ADR-020 §D, §H:
    - Live path: ObservationUpdater first, CalibrationUpdater second.
    - Replay path: ReplayUpdater only.
    - Incremental: only affected FeatureIdentities are included in target sets.
    - Full recomputation: all updater specs have empty target sets (= all features).
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    current_question_index: int = Field(..., ge=0)
    updater_specs: tuple[UpdaterInvocationSpec, ...] = Field(
        default_factory=tuple,
        description="Ordered invocation specs; sorted by invocation_order ASC"
    )
    is_full_recomputation: bool = Field(default=True)
    is_incremental: bool = Field(default=False)
    is_replay: bool = Field(default=False)
    affected_feature_type_ids: frozenset[str] = Field(
        default_factory=frozenset,
        description="Feature types affected by new observations since last cycle (incremental only)"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
