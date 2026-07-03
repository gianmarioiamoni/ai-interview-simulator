# domain/contracts/calibration/calibration_snapshot.py
# EPIC-06 E06-M1 — CalibrationSnapshot (immutable closure artifact per evaluation)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from domain.contracts.calibration.calibration_profile import CalibrationProfile


class DimensionCalibrationResult(BaseModel):
    """Calibration result for one dimension at one point in time.

    Derived by comparing an actual feature confidence value against
    a FeatureCalibrationBand from CalibrationProfile.
    """

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    actual_confidence: float = Field(..., ge=0.0, le=1.0)
    expected_min: float = Field(..., ge=0.0, le=1.0)
    expected_max: float = Field(..., ge=0.0, le=1.0)
    expected_mean: float = Field(..., ge=0.0, le=1.0)
    deviation: float = Field(..., description="actual_confidence - expected_mean")
    is_within_band: bool = Field(default=True)
    is_above_band: bool = Field(default=False)
    is_below_band: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}


class CalibrationSnapshot(BaseModel):
    """Immutable calibration closure artifact.

    Captures the calibration state at a specific evaluation point.
    Derived from CalibrationProfile + KnowledgeSnapshot.
    Never modifies any input — pure read.

    Mirrors the KnowledgeSnapshot / ReplayResult immutable closure pattern.
    Sole creation path: CalibrationBuilder.
    """

    snapshot_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    knowledge_epoch: str = Field(default="1", min_length=1)
    schema_version: str = Field(default="1.0", min_length=1)

    calibration_profile: CalibrationProfile = Field(
        ..., description="CalibrationProfile used as the baseline anchor"
    )
    dimension_results: tuple[DimensionCalibrationResult, ...] = Field(
        default_factory=tuple,
        description="Per-dimension calibration results"
    )

    overall_calibration_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Aggregate calibration score: fraction of dimensions within band"
    )
    dimensions_within_band: int = Field(default=0, ge=0)
    dimensions_above_band: int = Field(default=0, ge=0)
    dimensions_below_band: int = Field(default=0, ge=0)

    computed_at: datetime = Field(...)
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def is_fully_calibrated(self) -> bool:
        if not self.dimension_results:
            return False
        return self.dimensions_within_band == len(self.dimension_results)

    @property
    def total_dimensions(self) -> int:
        return len(self.dimension_results)
