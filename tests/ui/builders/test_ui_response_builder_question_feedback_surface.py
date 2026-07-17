# tests/ui/builders/test_ui_response_builder_question_feedback_surface.py
# EPIC-07 P4/C8 — UIResponseBuilder wires question/feedback SurfaceState.

from app.contracts.feedback_bundle import FeedbackBlockResult, FeedbackBundle
from app.ui.builders.ui_response_builder import UIResponseBuilder
from app.ui.presentation import FEEDBACK_EMPTY_KEY, SurfacePhase, get_empty_copy_entry
from domain.contracts.feedback.quality import Quality
from domain.contracts.feedback.severity import Severity
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question import QuestionType
from domain.contracts.shared.action_type import ActionType
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question


def test_question_mode_surface_ready() -> None:
    q = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    state = build_interview_state(questions=[q], answers=[])
    state = state.model_copy(update={"awaiting_user_input": True})
    response = UIResponseBuilder().build(state)
    assert response.surface_state is not None
    assert response.surface_state.surface_id == "question"
    assert response.surface_state.phase is SurfacePhase.READY


def test_feedback_mode_empty_uses_catalog_copy() -> None:
    q = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    answer = Answer(question_id="q1", content="my answer", attempt=1)
    state = build_interview_state(questions=[q], answers=[answer])
    bundle = FeedbackBundle(
        blocks=[],
        overall_severity=Severity.WARNING,
        overall_confidence=1.0,
        overall_quality=Quality.CORRECT,
        markdown="",
    )
    state = state.model_copy(
        update={
            "last_feedback_bundle": bundle,
            "allowed_actions": [ActionType.RETRY, ActionType.NEXT],
            "awaiting_user_input": True,
        }
    )
    response = UIResponseBuilder().build(state)
    assert response.surface_state is not None
    assert response.surface_state.surface_id == "feedback"
    assert response.surface_state.phase is SurfacePhase.EMPTY
    assert response.surface_state.empty_copy_key == FEEDBACK_EMPTY_KEY
    assert response.feedback_markdown == get_empty_copy_entry(
        FEEDBACK_EMPTY_KEY
    ).message_text
    assert "TODO" not in response.feedback_markdown
    assert "placeholder" not in response.feedback_markdown.lower()


def test_feedback_mode_ready_when_blocks_present() -> None:
    from domain.contracts.question.question_evaluation import QuestionEvaluation
    from domain.contracts.question.question_result import QuestionResult

    q = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    answer = Answer(question_id="q1", content="my answer", attempt=1)
    state = build_interview_state(questions=[q], answers=[answer])
    block = FeedbackBlockResult(
        title="Summary",
        content="Looks good.",
        severity=Severity.INFO,
        confidence=1.0,
        signals=[],
        learning=[],
        quality=None,
    )
    bundle = FeedbackBundle(
        blocks=[block],
        overall_severity=Severity.INFO,
        overall_confidence=1.0,
        overall_quality=Quality.CORRECT,
        markdown="Looks good.",
    )
    evaluation = QuestionEvaluation(
        question_id="q1",
        score=80.0,
        max_score=100.0,
        feedback="Looks good.",
        passed=True,
    )
    result = QuestionResult(question_id="q1", question=q, evaluation=evaluation)
    state = state.model_copy(
        update={
            "last_feedback_bundle": bundle,
            "allowed_actions": [ActionType.RETRY, ActionType.NEXT],
            "awaiting_user_input": True,
            "results_by_question": {"q1": result},
        }
    )
    response = UIResponseBuilder().build(state)
    assert response.surface_state is not None
    assert response.surface_state.phase is SurfacePhase.READY
    assert response.surface_state.empty_copy_key is None
    assert "Looks good." in response.feedback_markdown
