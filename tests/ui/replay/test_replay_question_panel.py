# tests/ui/replay/test_replay_question_panel.py

from __future__ import annotations

from app.ui.replay.panels.replay_question_panel import ReplayQuestionPanel
from tests.ui.replay.conftest import make_question_record


def test_happy_path_renders_core_fields() -> None:
    record = make_question_record()
    model = ReplayQuestionPanel(record).render()

    assert model.question_index == 0
    assert model.question_type == "technical"
    assert model.area_label == "Algorithms"
    assert model.question_prompt == "Prompt 0"
    assert model.candidate_answer == "Answer text"
    assert model.answer_display == "Answer text"
    assert model.score == 70.0
    assert model.max_score == 100.0
    assert model.score_pct == 70.0
    assert model.feedback == "Solid approach."
    assert model.strengths == ("Clear structure",)
    assert model.weaknesses == ("Missed edge cases",)
    assert model.follow_up_question == "Can you elaborate?"
    assert model.has_hint is True
    assert model.ai_hint_explanation == "Think about complexity."
    assert model.ai_hint_suggestion == "Use a hash map."
    assert model.attempts == 1
    assert model.is_coding_question is False
    assert model.execution_result is None


def test_empty_answer_shows_neutral_indicator() -> None:
    record = make_question_record(
        candidate_answer="",
        strengths=(),
        weaknesses=(),
        follow_up_question=None,
        ai_hint_explanation=None,
        ai_hint_suggestion=None,
    )
    model = ReplayQuestionPanel(record).render()

    assert model.candidate_answer == ""
    assert model.answer_display == "No answer recorded"
    assert model.strengths == ()
    assert model.weaknesses == ()
    assert model.follow_up_question is None
    assert model.has_hint is False


def test_delegates_to_execution_panel_when_coding() -> None:
    record = make_question_record(
        execution_status="failed",
        passed_tests=2,
        total_tests=5,
        follow_up_question=None,
        ai_hint_explanation=None,
        ai_hint_suggestion=None,
    )
    model = ReplayQuestionPanel(record).render()

    assert model.is_coding_question is True
    assert model.execution_result is not None
    assert model.execution_result.passed_tests == 2
    assert model.execution_result.total_tests == 5
    assert model.execution_result.pass_rate_pct == 40.0
