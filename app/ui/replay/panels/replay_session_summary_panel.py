# app/ui/replay/panels/replay_session_summary_panel.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.replay.replay_session import ReplaySession


@dataclass(frozen=True)
class SessionSummaryViewModel:
    """C-03 rendering model (EPIC-04-DATA-MODEL §4.3)."""

    interview_index: int
    session_date: datetime
    session_date_display: str
    role: str
    seniority_level: str
    interview_mode: str
    question_count: int
    session_duration_seconds: Optional[float]
    duration_display: Optional[str]
    company: Optional[str]
    overall_score: Optional[float]
    hire_decision: Optional[HireDecision]
    level: Optional[InterviewLevel]
    has_scoring: bool
    score_unavailable_label: Optional[str]
    is_successful: bool


class ReplaySessionSummaryPanel:
    """C-03: session-level metadata and conditional scoring summary."""

    def __init__(self, session: ReplaySession) -> None:
        self._session = session

    def render(self) -> SessionSummaryViewModel:
        metadata = self._session.session_metadata
        has_scoring = self._session.has_scoring
        scoring = self._session.scoring_snapshot

        duration = metadata.session_duration_seconds
        duration_display: Optional[str] = None
        if duration is not None:
            duration_display = f"{duration:.0f}s"

        overall_score: Optional[float] = None
        hire_decision: Optional[HireDecision] = None
        level: Optional[InterviewLevel] = None
        score_unavailable: Optional[str] = None

        if has_scoring and scoring is not None:
            overall_score = scoring.overall_score
            hire_decision = scoring.hire_decision
            level = scoring.level
        else:
            score_unavailable = "Score is not available for this session."

        return SessionSummaryViewModel(
            interview_index=metadata.interview_index,
            session_date=metadata.session_date,
            session_date_display=metadata.session_date.strftime("%Y-%m-%d"),
            role=metadata.role,
            seniority_level=metadata.seniority_level,
            interview_mode=metadata.interview_mode,
            question_count=metadata.question_count,
            session_duration_seconds=duration,
            duration_display=duration_display,
            company=metadata.company,
            overall_score=overall_score,
            hire_decision=hire_decision,
            level=level,
            has_scoring=has_scoring,
            score_unavailable_label=score_unavailable,
            is_successful=self._session.is_successful,
        )
