# app/ui/replay/panels/replay_scoring_panel.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.report.scoring_dimension import ScoringDimension


@dataclass(frozen=True)
class ScoringViewModel:
    """C-07 rendering model (EPIC-04-DATA-MODEL §4.7)."""

    overall_score: float
    scoring_dimensions: tuple[ScoringDimension, ...]
    dimension_scores: dict[str, float]
    hire_decision: HireDecision
    hiring_probability: float
    percentile_rank: float
    percentile_explanation: str
    level: InterviewLevel
    gating_triggered: bool
    gating_reason: Optional[str]


class ReplayScoringPanel:
    """C-07: session-level scoring panel (only when has_scoring)."""

    def __init__(self, session: ReplaySession) -> None:
        self._session = session

    def render(self) -> ScoringViewModel | None:
        """Return the view model when scoring exists; otherwise None (I-C07-01)."""
        if not self._session.has_scoring:
            return None

        scoring = self._session.scoring_snapshot
        if scoring is None:
            return None

        gating_reason = scoring.gating_reason if scoring.gating_triggered else None

        return ScoringViewModel(
            overall_score=scoring.overall_score,
            scoring_dimensions=scoring.scoring_dimensions,
            dimension_scores=dict(scoring.dimension_scores),
            hire_decision=scoring.hire_decision,
            hiring_probability=scoring.hiring_probability,
            percentile_rank=scoring.percentile_rank,
            percentile_explanation=scoring.percentile_explanation,
            level=scoring.level,
            gating_triggered=scoring.gating_triggered,
            gating_reason=gating_reason,
        )
