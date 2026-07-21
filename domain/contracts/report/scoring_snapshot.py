# domain/contracts/report/scoring_snapshot.py

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.report.scoring_dimension import ScoringDimension


class ScoringSnapshot(BaseModel):
    """Immutable aggregate scoring record for a completed session.

    A Projection Artifact (OP-02): carries all scoring data previously held
    by InterviewEvaluation. Produced exclusively by ScoringSnapshotBuilder.

    The three convenience dict fields (dimension_scores, dimension_signals,
    weighted_breakdown) are derived from scoring_dimensions at validation time
    and must never be set independently (R-12).
    """

    model_config = {"frozen": True, "extra": "forbid"}

    # Aggregate scoring
    overall_score: float = Field(ge=0.0, le=100.0)
    raw_score: float | None = Field(default=None, ge=0.0, le=100.0)
    adjusted_score: float | None = Field(default=None, ge=0.0, le=100.0)

    # Dimension scoring — canonical source
    scoring_dimensions: tuple[ScoringDimension, ...]

    # Derived projections — populated by ScoringSnapshotBuilder, validated below
    dimension_scores: dict[str, float]
    dimension_signals: dict[str, float]
    weighted_breakdown: dict[str, float]

    # Decision
    level: InterviewLevel
    hire_decision: HireDecision
    hiring_probability: float = Field(ge=0.0, le=100.0)
    percentile_rank: float = Field(ge=0.0, le=100.0)
    percentile_explanation: str = Field(min_length=1)
    decision_explanation: dict[str, list[str]]
    gating_triggered: bool
    gating_reason: str | None = None

    # Confidence
    confidence: Confidence

    schema_version: str = Field(default="1.0", min_length=1)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_non_empty_dimensions(self) -> "ScoringSnapshot":
        # V-SS-02
        if len(self.scoring_dimensions) == 0:
            raise ValueError("scoring_dimensions must not be empty (V-SS-02)")
        return self

    @model_validator(mode="after")
    def _validate_gating_reason(self) -> "ScoringSnapshot":
        # V-SS-01
        if self.gating_triggered and self.gating_reason is None:
            raise ValueError(
                "gating_reason must be set when gating_triggered=True (V-SS-01)"
            )
        return self

    @model_validator(mode="after")
    def _validate_derived_dict_key_parity(self) -> "ScoringSnapshot":
        # V-SS-04 / R-12: derived dict keys must equal dimension type values
        expected = {d.dimension_type.value for d in self.scoring_dimensions}
        for name, actual in (
            ("dimension_scores", set(self.dimension_scores.keys())),
            ("dimension_signals", set(self.dimension_signals.keys())),
            ("weighted_breakdown", set(self.weighted_breakdown.keys())),
        ):
            if actual != expected:
                raise ValueError(
                    f"{name} keys {sorted(actual)!r} must equal "
                    f"scoring_dimensions keys {sorted(expected)!r} (R-12)"
                )
        return self
