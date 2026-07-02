# services/feature_engine/feature_engine_diagnostics.py
# FeatureEngineDiagnostics — full observability record for one cycle (ADR-020 §K)

from pydantic import BaseModel, Field

from services.feature_engine.feature_engine_metrics import FeatureEngineMetrics
from services.feature_engine.feature_resolution_report import FeatureResolutionReport
from services.feature_engine.feature_update_plan import FeatureUpdatePlan


class UpdaterInvocationRecord(BaseModel):
    """Which Observations each Updater received and which candidates it produced."""

    updater_id: str = Field(..., min_length=1)
    invocation_order: int = Field(..., ge=0)
    observation_ids_received: tuple[str, ...] = Field(default_factory=tuple)
    candidate_feature_type_ids_produced: tuple[str, ...] = Field(default_factory=tuple)
    duration_ms: float = Field(default=0.0, ge=0.0)

    model_config = {"frozen": True, "extra": "forbid"}


class FeatureEngineDiagnostics(BaseModel):
    """Complete observability record for one FeatureEngine computation cycle.

    Combines the update plan, updater invocation trace, resolution report,
    and cycle metrics into a single immutable artifact for debugging, auditing,
    and calibration.

    ADR-020 §K diagnostic types:
    - Feature Computation Trace → updater_invocation_records + resolution_report
    - Execution Timing            → metrics.updater_timings
    - Feature Statistics          → resolution_report.*_resolutions counters
    - Replay Diagnostics          → is_replay + reconstruction_delta_summary
    - Audit Diagnostics           → provenance reconstructable via resolution_records
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    current_question_index: int = Field(..., ge=0)
    plan: FeatureUpdatePlan
    updater_invocation_records: tuple[UpdaterInvocationRecord, ...] = Field(
        default_factory=tuple
    )
    resolution_report: FeatureResolutionReport
    metrics: FeatureEngineMetrics
    is_replay: bool = Field(default=False)
    reconstruction_delta_summary: str | None = Field(
        default=None,
        description=(
            "Replay-only: summary of differences between reconstructed features "
            "and stored CandidateProfileSnapshot (ADR-020 §K)"
        ),
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
