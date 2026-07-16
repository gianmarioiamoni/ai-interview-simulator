# tests/domain/contracts/report/conftest.py
# Shared fixtures for Report v2.0 contract tests — reuses SessionHistory fixtures

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.generation_metadata import GenerationMetadata
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.report.report import Report
from domain.contracts.report.report_builder import ReportBuilder
from domain.contracts.report.scoring_dimension import ScoringDimension
from domain.contracts.report.scoring_narrative import ScoringNarrative
from domain.contracts.report.scoring_snapshot import ScoringSnapshot
from domain.contracts.report.scoring_snapshot_builder import ScoringSnapshotBuilder
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType

# Reuse upstream fixture helpers
from tests.domain.contracts.session_history.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    FIXED_HISTORY_DT,
    make_session_history as _make_base_session_history,
    make_interview_metadata,
    make_language_profile,
    make_transcript,
    make_question_timeline,
)
from domain.contracts.session_history.session_history import ReplayMetadata

REPORT_ID = "report-test-001"
FIXED_REPORT_DT = datetime(2026, 7, 3, 1, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Scoring fixture helpers
# ---------------------------------------------------------------------------

def make_scoring_dimension(
    dim_type: PerformanceDimensionType = PerformanceDimensionType.TECHNICAL_DEPTH,
    score: float = 75.0,
    signal: float = 0.8,
    weighted_contribution: float = 0.25,
    justification: str = "Solid technical depth demonstrated.",
    level: str = "strong",
) -> ScoringDimension:
    return ScoringDimension(
        dimension_type=dim_type,
        score=score,
        signal=signal,
        weighted_contribution=weighted_contribution,
        justification=justification,
        level=level,
    )


def make_scoring_snapshot() -> ScoringSnapshot:
    dim = make_scoring_dimension()
    return (
        ScoringSnapshotBuilder()
        .with_overall_score(72.5)
        .with_scoring_dimensions((dim,))
        .with_level(InterviewLevel.STRONG)
        .with_hire_decision(HireDecision.HIRE)
        .with_hiring_probability(78.0)
        .with_percentile_rank(65.0)
        .with_percentile_explanation("Better than 65% of candidates.")
        .with_decision_explanation({"strengths": ["Good problem solving"], "gaps": ["System design"]})
        .with_gating(triggered=False)
        .with_confidence(Confidence(base=0.85, final=0.80))
        .build()
    )


def make_scoring_narrative() -> ScoringNarrative:
    return ScoringNarrative(
        executive_summary="Strong candidate — recommended for hire.",
        went_well=("Clear problem decomposition.", "Good communication."),
        improvement_suggestions=("Practice system design.", "Review distributed consensus."),
    )


def make_context_profile() -> InterviewContextProfile:
    return InterviewContextProfile()


def make_session_history(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
) -> object:
    """Build a SessionHistory v2.0 with scoring artefacts for Report v2.0 tests."""
    from tests.domain.contracts.knowledge_snapshot.conftest import make_knowledge_snapshot

    snapshot = make_knowledge_snapshot(session_id=session_id, candidate_id=candidate_id)
    scoring_snapshot = make_scoring_snapshot()
    scoring_narrative = make_scoring_narrative()
    context_profile = make_context_profile()

    # Use empty transcript so question_count=0 matches empty question_assessments (V-R-01)
    return (
        SessionHistoryBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(0)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=session_id))
        .with_transcript([])
        .with_question_timeline([])
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_HISTORY_DT)
        .with_scoring_snapshot(scoring_snapshot)
        .with_scoring_narrative(scoring_narrative)
        .with_context_profile(context_profile)
        .build()
    )


def make_report(
    report_id: str = REPORT_ID,
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
) -> Report:
    history = make_session_history(
        session_id=session_id,
        candidate_id=candidate_id,
    )
    return (
        ReportBuilder()
        .with_session_history(history)
        .with_report_id(report_id)
        .with_created_at(FIXED_REPORT_DT)
        .build()
    )


def make_explainability_coaching_snapshot(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
):
    """EPIC-06 M0 — coaching snapshot with matching objectives + actions."""
    from domain.contracts.coaching.coaching_action import ActionCategory, CoachingAction
    from domain.contracts.coaching.coaching_builder import CoachingBuilder
    from domain.contracts.coaching.learning_objective import (
        LearningObjective,
        ObjectivePriority,
    )
    from domain.contracts.feature.feature_type import FeatureType
    from domain.contracts.observation.observation_type import ObservationType

    objective = LearningObjective(
        objective_id="obj-explainability-1",
        feature_type=FeatureType.REASONING,
        description="Strengthen causal reasoning depth",
        priority=ObjectivePriority.HIGH,
        confidence=0.88,
        supporting_observation_types=(ObservationType.REASONING_DEPTH_LOW,),
        detected_at_question_index=0,
        candidate_identity_id=candidate_id,
    )
    action = CoachingAction.for_objective(
        objective=objective,
        action_id="act-explainability-1",
        category=ActionCategory.DEEP_DIVE,
        description="Complete five causal-reasoning trade-off drills",
        effort_estimate_hours=3.0,
        is_immediate=True,
    )
    return CoachingBuilder.build(
        objectives=(objective,),
        actions=(action,),
        recommendations=(),
        session_id=session_id,
        question_index=0,
    )


def make_report_with_explainability(
    report_id: str = REPORT_ID,
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
) -> Report:
    """EPIC-06 M0 — Report fixture with insights + actions + objectives."""
    from tests.domain.contracts.narrative.conftest import make_narrative

    history = make_session_history(
        session_id=session_id,
        candidate_id=candidate_id,
    )
    return (
        ReportBuilder()
        .with_session_history(history)
        .with_narrative(make_narrative(with_insights=True))
        .with_coaching_snapshot(
            make_explainability_coaching_snapshot(
                session_id=session_id,
                candidate_id=candidate_id,
            )
        )
        .with_report_id(report_id)
        .with_created_at(FIXED_REPORT_DT)
        .build()
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_id() -> str:
    return CANDIDATE_ID


@pytest.fixture
def session_id() -> str:
    return SESSION_ID


@pytest.fixture
def session_history():
    return make_session_history()


@pytest.fixture
def report() -> Report:
    return make_report()


@pytest.fixture
def report_with_explainability() -> Report:
    """EPIC-06 M0 baseline fixture: insights + actions + objectives."""
    return make_report_with_explainability()
