# tests/ui/builders/test_ui_response_builder_retry.py

from app.ui.builders.ui_response_builder import UIResponseBuilder
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question import QuestionType
from domain.contracts.shared.action_type import ActionType


def _state_after_retry(qtype: QuestionType = QuestionType.WRITTEN, answer_content: str = "my answer"):
    """State after RETRY: answer exists, result cleared, awaiting input."""
    q = build_question(qid="q1", qtype=qtype)
    answer = Answer(question_id="q1", content=answer_content, attempt=1)
    state = build_interview_state(questions=[q], answers=[answer])
    return state.model_copy(
        update={
            "awaiting_user_input": True,
            "last_feedback_bundle": None,
            "allowed_actions": [],
            "intent": ActionType.NONE,
            "results_by_question": {},
        }
    )


def test_b10_written_editor_prefilled_after_retry():
    """B10: written editor must be pre-filled with prior answer in QUESTION mode after retry."""
    state = _state_after_retry(qtype=QuestionType.WRITTEN, answer_content="my written answer")
    builder = UIResponseBuilder()
    response = builder.build(state)
    assert response.written_editor_value == "my written answer"
    assert response.coding_editor_value == ""
    assert response.database_editor_value == ""


def test_b10_coding_editor_prefilled_after_retry():
    """B10: coding editor must be pre-filled with prior answer in QUESTION mode after retry."""
    state = _state_after_retry(qtype=QuestionType.CODING, answer_content="print('hello')")
    builder = UIResponseBuilder()
    response = builder.build(state)
    assert response.coding_editor_value == "print('hello')"
    assert response.written_editor_value == ""
    assert response.database_editor_value == ""


def test_b10_database_editor_prefilled_after_retry():
    """B10: database editor must be pre-filled with prior answer in QUESTION mode after retry."""
    state = _state_after_retry(qtype=QuestionType.DATABASE, answer_content="SELECT * FROM t")
    builder = UIResponseBuilder()
    response = builder.build(state)
    assert response.database_editor_value == "SELECT * FROM t"
    assert response.written_editor_value == ""
    assert response.coding_editor_value == ""


def test_b10_new_question_no_prior_answer_editor_empty():
    """B10 regression: fresh question with no prior answer keeps editor empty."""
    q = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    state = build_interview_state(questions=[q], answers=[])
    state = state.model_copy(update={"awaiting_user_input": True})
    builder = UIResponseBuilder()
    response = builder.build(state)
    assert response.written_editor_value == ""


def test_b10_feedback_mode_editor_hidden_not_prefilled():
    """B10 regression: in FEEDBACK mode editors are hidden; pre-fill does not apply."""
    from app.contracts.feedback_bundle import FeedbackBundle
    from domain.contracts.feedback.quality import Quality
    from domain.contracts.feedback.severity import Severity

    q = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    answer = Answer(question_id="q1", content="my answer", attempt=1)
    state = build_interview_state(questions=[q], answers=[answer])
    bundle = FeedbackBundle(
        blocks=[],
        overall_severity=Severity.WARNING,
        overall_confidence=1.0,
        overall_quality=Quality.CORRECT,
        markdown="feedback text",
    )
    state = state.model_copy(
        update={
            "last_feedback_bundle": bundle,
            "allowed_actions": [ActionType.RETRY, ActionType.NEXT],
            "awaiting_user_input": True,
        }
    )
    builder = UIResponseBuilder()
    response = builder.build(state)
    assert response.written_editor_visible is False
    assert response.written_editor_value == ""
