# tests/ui/replay/test_replay_scoring_panel.py

from __future__ import annotations

from app.ui.replay.panels.replay_scoring_panel import ReplayScoringPanel
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from tests.ui.replay.conftest import make_replay_session, make_scoring_snapshot


def test_renders_scoring_fields_when_present() -> None:
    session = make_replay_session(scoring_snapshot=make_scoring_snapshot())
    model = ReplayScoringPanel(session).render()

    assert model is not None
    assert model.overall_score == 72.5
    assert model.hire_decision == HireDecision.HIRE
    assert model.level == InterviewLevel.STRONG
    assert model.hiring_probability == 78.0
    assert model.percentile_rank == 65.0
    assert "65%" in model.percentile_explanation
    assert "technical_depth" in model.dimension_scores
    assert model.gating_triggered is False
    assert model.gating_reason is None


def test_returns_none_when_no_scoring() -> None:
    session = make_replay_session(scoring_snapshot=None)
    assert ReplayScoringPanel(session).render() is None


def test_gating_reason_only_when_triggered() -> None:
    session = make_replay_session(scoring_snapshot=make_scoring_snapshot(gating_triggered=True))
    model = ReplayScoringPanel(session).render()

    assert model is not None
    assert model.gating_triggered is True
    assert model.gating_reason == "Integrity check failed"
