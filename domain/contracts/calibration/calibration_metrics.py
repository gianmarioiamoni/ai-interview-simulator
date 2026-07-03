# domain/contracts/calibration/calibration_metrics.py
# EPIC-06 E06-M1 — CalibrationMetrics (per-dimension and aggregate deviation metrics)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.calibration.calibration_snapshot import CalibrationSnapshot


class DimensionMetric(BaseModel):
    """Metric for one dimension derived from a CalibrationSnapshot."""

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    actual_confidence: float = Field(..., ge=0.0, le=1.0)
    expected_mean: float = Field(..., ge=0.0, le=1.0)
    deviation: float = Field(...)
    absolute_deviation: float = Field(..., ge=0.0)
    is_within_band: bool = Field(default=True)
    status: str = Field(..., description="'within' | 'above' | 'below'")

    model_config = {"frozen": True, "extra": "forbid"}


class CalibrationMetrics(BaseModel):
    """Aggregate and per-dimension metrics derived from a CalibrationSnapshot.

    Pure computation. No LLM, no business logic, no mutation.
    Mirrors the KnowledgeSnapshotStatistics / SessionHistoryStatistics pattern.
    """

    candidate_identity_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    total_dimensions: int = Field(..., ge=0)
    dimensions_within_band: int = Field(..., ge=0)
    dimensions_above_band: int = Field(..., ge=0)
    dimensions_below_band: int = Field(..., ge=0)

    overall_calibration_score: float = Field(..., ge=0.0, le=1.0)
    mean_absolute_deviation: float = Field(..., ge=0.0)
    max_absolute_deviation: float = Field(..., ge=0.0)

    dimension_metrics: tuple[DimensionMetric, ...] = Field(default_factory=tuple)

    is_empty: bool = Field(default=False)
    knowledge_epoch: str = Field(..., min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_snapshot(cls, snapshot: CalibrationSnapshot) -> "CalibrationMetrics":
        """Compute metrics from a CalibrationSnapshot. Pure derivation."""
        results = snapshot.dimension_results
        if not results:
            return cls(
                candidate_identity_id=snapshot.candidate_identity_id,
                session_id=snapshot.session_id,
                total_dimensions=0,
                dimensions_within_band=0,
                dimensions_above_band=0,
                dimensions_below_band=0,
                overall_calibration_score=0.0,
                mean_absolute_deviation=0.0,
                max_absolute_deviation=0.0,
                is_empty=True,
                knowledge_epoch=snapshot.knowledge_epoch,
            )

        dim_metrics: list[DimensionMetric] = []
        for r in results:
            if r.is_within_band:
                status = "within"
            elif r.is_above_band:
                status = "above"
            else:
                status = "below"
            dim_metrics.append(DimensionMetric(
                feature_type_id=r.feature_type_id,
                semantic_category=r.semantic_category,
                actual_confidence=r.actual_confidence,
                expected_mean=r.expected_mean,
                deviation=r.deviation,
                absolute_deviation=abs(r.deviation),
                is_within_band=r.is_within_band,
                status=status,
            ))

        abs_devs = [d.absolute_deviation for d in dim_metrics]
        mean_abs_dev = sum(abs_devs) / len(abs_devs)
        max_abs_dev = max(abs_devs)

        return cls(
            candidate_identity_id=snapshot.candidate_identity_id,
            session_id=snapshot.session_id,
            total_dimensions=snapshot.total_dimensions,
            dimensions_within_band=snapshot.dimensions_within_band,
            dimensions_above_band=snapshot.dimensions_above_band,
            dimensions_below_band=snapshot.dimensions_below_band,
            overall_calibration_score=snapshot.overall_calibration_score,
            mean_absolute_deviation=mean_abs_dev,
            max_absolute_deviation=max_abs_dev,
            dimension_metrics=tuple(dim_metrics),
            is_empty=False,
            knowledge_epoch=snapshot.knowledge_epoch,
        )
