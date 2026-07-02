# services/feature_engine/feature_resolution_report.py
# FeatureResolutionReport — per-feature composition outcome (ADR-020 §C, §I, §K)

from enum import Enum

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.profile_feature import ProfileFeature


class ResolutionStrategy(str, Enum):
    """How FeatureComposer resolved candidates for a given FeatureIdentity."""

    SINGLE_CANDIDATE = "single_candidate"
    MERGED = "merged"
    REPLACED = "replaced"
    RETAINED = "retained"  # incremental mode: prior feature kept unchanged


class CandidateResolutionRecord(BaseModel):
    """Record of one candidate's fate during composition (ADR-020 §K)."""

    updater_id: str = Field(..., min_length=1)
    candidate_value: str = Field(..., min_length=1)
    candidate_confidence: float = Field(..., ge=0.0, le=1.0)
    source_observation_count: int = Field(..., ge=0)
    was_winner: bool = Field(default=False)
    was_superseded: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}


class FeatureResolutionRecord(BaseModel):
    """Resolution outcome for a single FeatureIdentity in one computation cycle.

    Part of the per-cycle FeatureResolutionReport (ADR-020 §K).
    """

    feature_type_id: str = Field(..., min_length=1)
    strategy: ResolutionStrategy
    final_value: str = Field(..., min_length=1)
    final_confidence: float = Field(..., ge=0.0, le=1.0)
    candidate_records: tuple[CandidateResolutionRecord, ...] = Field(default_factory=tuple)
    policy_applied: str | None = Field(
        default=None,
        description="Policy class name used for merge/replace; None for single candidate"
    )

    model_config = {"frozen": True, "extra": "forbid"}


class FeatureResolutionReport(BaseModel):
    """Complete composition trace for one FeatureEngine computation cycle.

    Carries one FeatureResolutionRecord per resolved FeatureIdentity.
    Used by FeatureEngineDiagnostics to surface the full decision log.

    ADR-020 §K: Feature Computation Trace.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    current_question_index: int = Field(..., ge=0)
    total_candidates_received: int = Field(default=0, ge=0)
    total_features_resolved: int = Field(default=0, ge=0)
    merge_resolutions: int = Field(default=0, ge=0)
    replace_resolutions: int = Field(default=0, ge=0)
    single_candidate_resolutions: int = Field(default=0, ge=0)
    retained_resolutions: int = Field(default=0, ge=0)
    resolution_records: tuple[FeatureResolutionRecord, ...] = Field(default_factory=tuple)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
