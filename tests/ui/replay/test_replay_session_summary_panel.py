# tests/ui/replay/test_replay_session_summary_panel.py

from __future__ import annotations

from app.ui.replay.panels.replay_session_summary_panel import ReplaySessionSummaryPanel
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from tests.ui.replay.conftest import make_replay_session, make_scoring_snapshot


def test_renders_all_metadata_fields_with_scoring() -> None:
    session = make_replay_session(scoring_snapshot=make_scoring_snapshot())
    model = ReplaySessionSummaryPanel(session).render()

    assert model.interview_index == 1
    assert model.session_date_display == "2026-07-15"
    assert model.role == "Software Engineer"
    assert model.seniority_level == "Senior"
    assert model.interview_mode == "technical"
    assert model.question_count == 1
    assert model.duration_display == "120s"
    assert model.company == "Acme Corp"
    assert model.has_scoring is True
    assert model.overall_score == 72.5
    assert model.hire_decision == HireDecision.HIRE
    assert model.level == InterviewLevel.STRONG
    assert model.score_unavailable_label is None


def test_score_not_available_when_no_scoring() -> None:
    session = make_replay_session(scoring_snapshot=None)
    model = ReplaySessionSummaryPanel(session).render()

    assert model.has_scoring is False
    assert model.overall_score is None
    assert model.hire_decision is None
    assert model.level is None
    assert model.score_unavailable_label == "Score is not available for this session."


def test_omits_duration_and_company_when_none() -> None:
    session = make_replay_session(
        session_duration_seconds=None,
        company=None,
        scoring_snapshot=None,
    )
    model = ReplaySessionSummaryPanel(session).render()

    assert model.session_duration_seconds is None
    assert model.duration_display is None
    assert model.company is None
