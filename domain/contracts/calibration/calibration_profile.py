# domain/contracts/calibration/calibration_profile.py
# EPIC-06 E06-M1 — CalibrationProfile (immutable runtime calibration anchor)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FeatureCalibrationBand(BaseModel):
    """Expected confidence band for one feature dimension at a given seniority level.

    Derived from SessionHistory[]. Used as a calibration baseline anchor.
    All fields are immutable — no live FeatureEngine modifications.
    """

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    expected_min: float = Field(..., ge=0.0, le=1.0)
    expected_max: float = Field(..., ge=0.0, le=1.0)
    expected_mean: float = Field(..., ge=0.0, le=1.0)
    observation_count: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}


class CalibrationProfile(BaseModel):
    """Immutable calibration baseline derived from SessionHistory[].

    Anchors calibration bands per feature dimension and seniority level.
    Read-only view — never modifies FeatureEngine, CandidateProfile,
    LearningProgress, or SessionHistory.

    No persistence. Derived at query time.
    Sole creation path: CalibrationBuilder.

    Consumers: CalibrationUpdater (planned), CI calibration gate (EPIC-06).
    """

    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    knowledge_epoch: str = Field(default="1", min_length=1)
    schema_version: str = Field(default="1.0", min_length=1)

    feature_bands: tuple[FeatureCalibrationBand, ...] = Field(
        default_factory=tuple,
        description="Per-dimension calibration bands derived from history"
    )

    session_count_used: int = Field(..., ge=0)
    computed_at: datetime = Field(...)

    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def is_empty(self) -> bool:
        return len(self.feature_bands) == 0

    @property
    def feature_type_ids(self) -> frozenset[str]:
        return frozenset(b.feature_type_id for b in self.feature_bands)
