# tests/ui/replay/test_replay_execution_result_panel.py

from __future__ import annotations

from app.ui.replay.panels.replay_execution_result_panel import ReplayExecutionResultPanel
from tests.ui.replay.conftest import make_question_record


def test_renders_execution_result_for_coding_question() -> None:
    record = make_question_record(
        execution_status="passed",
        passed_tests=8,
        total_tests=10,
        follow_up_question=None,
        ai_hint_explanation=None,
        ai_hint_suggestion=None,
    )
    model = ReplayExecutionResultPanel(record).render()

    assert model is not None
    assert model.execution_status == "passed"
    assert model.status_badge == "Passed"
    assert model.passed_tests == 8
    assert model.total_tests == 10
    assert model.pass_rate_pct == 80.0


def test_returns_none_when_not_coding_question() -> None:
    record = make_question_record(
        follow_up_question=None,
        ai_hint_explanation=None,
        ai_hint_suggestion=None,
    )
    assert record.is_coding_question is False
    assert ReplayExecutionResultPanel(record).render() is None
