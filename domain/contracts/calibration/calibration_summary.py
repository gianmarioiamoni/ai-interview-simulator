# domain/contracts/calibration/calibration_summary.py
# EPIC-06 E06-M1 — CalibrationSummary (lightweight read-only view of CalibrationSnapshot)

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from domain.contracts.calibration.calibration_snapshot import CalibrationSnapshot


class CalibrationSummary(BaseModel):
    """Lightweight, immutable summary view of a CalibrationSnapshot.

    Mirrors KnowledgeSnapshotSummary / LearningProgressSummary pattern.
    No LLM, no business logic, no mutation. Frozen after construction.
    """

    snapshot_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    knowledge_epoch: str = Field(..., min_length=1)
    computed_at: datetime = Field(...)

    total_dimensions: int = Field(..., ge=0)
    dimensions_within_band: int = Field(..., ge=0)
    dimensions_above_band: int = Field(..., ge=0)
    dimensions_below_band: int = Field(..., ge=0)
    overall_calibration_score: float = Field(..., ge=0.0, le=1.0)
    is_fully_calibrated: bool = Field(default=False)

    schema_version: str = Field(default="1.0", min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_snapshot(cls, snapshot: CalibrationSnapshot) -> "CalibrationSummary":
        """Produce a lightweight summary from a CalibrationSnapshot. Pure derivation."""
        return cls(
            snapshot_id=snapshot.snapshot_id,
            candidate_identity_id=snapshot.candidate_identity_id,
            session_id=snapshot.session_id,
            role=snapshot.role,
            seniority=snapshot.seniority,
            knowledge_epoch=snapshot.knowledge_epoch,
            computed_at=snapshot.computed_at,
            total_dimensions=snapshot.total_dimensions,
            dimensions_within_band=snapshot.dimensions_within_band,
            dimensions_above_band=snapshot.dimensions_above_band,
            dimensions_below_band=snapshot.dimensions_below_band,
            overall_calibration_score=snapshot.overall_calibration_score,
            is_fully_calibrated=snapshot.is_fully_calibrated,
            schema_version=snapshot.schema_version,
        )
