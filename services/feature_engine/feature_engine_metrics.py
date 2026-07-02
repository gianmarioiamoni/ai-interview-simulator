# services/feature_engine/feature_engine_metrics.py
# FeatureEngineMetrics — per-cycle and aggregate timing + statistics (ADR-020 §K, §L)

from pydantic import BaseModel, Field


class UpdaterTimingRecord(BaseModel):
    """Execution timing for one FeatureUpdater invocation (ADR-020 §K)."""

    updater_id: str = Field(..., min_length=1)
    duration_ms: float = Field(..., ge=0.0)
    candidates_produced: int = Field(default=0, ge=0)

    model_config = {"frozen": True, "extra": "forbid"}


class FeatureEngineMetrics(BaseModel):
    """Timing and statistical metrics for one FeatureEngine computation cycle.

    Immutable record produced at cycle completion.

    ADR-020 §K (Observability) and §L (Performance Goals):
    - total_cycle_duration_ms: wall-clock time for the entire cycle.
    - updater_timings: per-Updater breakdown.
    - composer_duration_ms: FeatureComposer composition time.
    - commit_duration_ms: CandidateProfile update time.
    - features_computed: count of ProfileFeatures in the output.
    - candidates_collected: total FeatureCandidates from all Updaters.
    - observation_count: Observations delivered to Updaters this cycle.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    current_question_index: int = Field(..., ge=0)
    total_cycle_duration_ms: float = Field(default=0.0, ge=0.0)
    updater_timings: tuple[UpdaterTimingRecord, ...] = Field(default_factory=tuple)
    composer_duration_ms: float = Field(default=0.0, ge=0.0)
    commit_duration_ms: float = Field(default=0.0, ge=0.0)
    features_computed: int = Field(default=0, ge=0)
    candidates_collected: int = Field(default=0, ge=0)
    observation_count: int = Field(default=0, ge=0)
    is_incremental: bool = Field(default=False)
    is_replay: bool = Field(default=False)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
