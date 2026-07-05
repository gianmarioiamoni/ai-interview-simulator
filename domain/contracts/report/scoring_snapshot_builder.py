# domain/contracts/report/scoring_snapshot_builder.py

from __future__ import annotations

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.report.scoring_dimension import ScoringDimension
from domain.contracts.report.scoring_snapshot import ScoringSnapshot


class ScoringSnapshotBuilder:
    """Sole constructor for ScoringSnapshot.

    Derives the three dict projections (dimension_scores, dimension_signals,
    weighted_breakdown) from scoring_dimensions. These dicts must never be
    set directly on ScoringSnapshot (R-12).
    """

    def __init__(self) -> None:
        self._overall_score: float | None = None
        self._raw_score: float | None = None
        self._adjusted_score: float | None = None
        self._scoring_dimensions: tuple[ScoringDimension, ...] = ()
        self._level: InterviewLevel | None = None
        self._hire_decision: HireDecision | None = None
        self._hiring_probability: float | None = None
        self._percentile_rank: float | None = None
        self._percentile_explanation: str | None = None
        self._decision_explanation: dict[str, list[str]] = {}
        self._gating_triggered: bool = False
        self._gating_reason: str | None = None
        self._confidence: Confidence | None = None
        self._schema_version: str = "1.0"

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def with_overall_score(self, score: float) -> "ScoringSnapshotBuilder":
        self._overall_score = score
        return self

    def with_raw_score(self, score: float | None) -> "ScoringSnapshotBuilder":
        self._raw_score = score
        return self

    def with_adjusted_score(self, score: float | None) -> "ScoringSnapshotBuilder":
        self._adjusted_score = score
        return self

    def with_scoring_dimensions(
        self, dimensions: tuple[ScoringDimension, ...] | list[ScoringDimension]
    ) -> "ScoringSnapshotBuilder":
        self._scoring_dimensions = tuple(dimensions)
        return self

    def with_level(self, level: InterviewLevel) -> "ScoringSnapshotBuilder":
        self._level = level
        return self

    def with_hire_decision(self, decision: HireDecision) -> "ScoringSnapshotBuilder":
        self._hire_decision = decision
        return self

    def with_hiring_probability(self, probability: float) -> "ScoringSnapshotBuilder":
        self._hiring_probability = probability
        return self

    def with_percentile_rank(self, rank: float) -> "ScoringSnapshotBuilder":
        self._percentile_rank = rank
        return self

    def with_percentile_explanation(self, explanation: str) -> "ScoringSnapshotBuilder":
        self._percentile_explanation = explanation
        return self

    def with_decision_explanation(
        self, explanation: dict[str, list[str]]
    ) -> "ScoringSnapshotBuilder":
        self._decision_explanation = explanation
        return self

    def with_gating(
        self, triggered: bool, reason: str | None = None
    ) -> "ScoringSnapshotBuilder":
        self._gating_triggered = triggered
        self._gating_reason = reason
        return self

    def with_confidence(self, confidence: Confidence) -> "ScoringSnapshotBuilder":
        self._confidence = confidence
        return self

    def with_schema_version(self, version: str) -> "ScoringSnapshotBuilder":
        self._schema_version = version
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> ScoringSnapshot:
        self._validate_required()

        dimension_scores = {
            d.dimension_type.value: d.score for d in self._scoring_dimensions
        }
        dimension_signals = {
            d.dimension_type.value: d.signal for d in self._scoring_dimensions
        }
        weighted_breakdown = {
            d.dimension_type.value: d.weighted_contribution
            for d in self._scoring_dimensions
        }

        return ScoringSnapshot(
            overall_score=self._overall_score,  # type: ignore[arg-type]
            raw_score=self._raw_score,
            adjusted_score=self._adjusted_score,
            scoring_dimensions=self._scoring_dimensions,
            dimension_scores=dimension_scores,
            dimension_signals=dimension_signals,
            weighted_breakdown=weighted_breakdown,
            level=self._level,  # type: ignore[arg-type]
            hire_decision=self._hire_decision,  # type: ignore[arg-type]
            hiring_probability=self._hiring_probability,  # type: ignore[arg-type]
            percentile_rank=self._percentile_rank,  # type: ignore[arg-type]
            percentile_explanation=self._percentile_explanation,  # type: ignore[arg-type]
            decision_explanation=self._decision_explanation,
            gating_triggered=self._gating_triggered,
            gating_reason=self._gating_reason,
            confidence=self._confidence,  # type: ignore[arg-type]
            schema_version=self._schema_version,
        )

    def _validate_required(self) -> None:
        missing = [
            name
            for name, value in (
                ("overall_score", self._overall_score),
                ("level", self._level),
                ("hire_decision", self._hire_decision),
                ("hiring_probability", self._hiring_probability),
                ("percentile_rank", self._percentile_rank),
                ("percentile_explanation", self._percentile_explanation),
                ("confidence", self._confidence),
            )
            if value is None
        ]
        if missing:
            raise ValueError(
                f"ScoringSnapshotBuilder.build() missing required fields: {missing}"
            )
        if not self._scoring_dimensions:
            raise ValueError(
                "ScoringSnapshotBuilder.build() requires at least one ScoringDimension"
            )
