# tests/graph/nodes/test_adaptive_navigation_node.py

from unittest.mock import Mock

from app.graph.nodes.adaptive_navigation_node import AdaptiveNavigationNode
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question
from domain.contracts.shared.action_type import ActionType
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import QuestionDifficulty, QuestionType


def _make_adaptive_state(*, questions=None, planned_area_count: int = 5, current_index: int = 0):
    if questions is None:
        questions = [build_question(qid="q1")]

    state = build_interview_state(
        questions=questions,
        current_question_index=current_index,
    )

    planned_areas = [InterviewArea.TECH_CODING.value] * planned_area_count

    return state.model_copy(
        update={
            "adaptive_interview_enabled": True,
            "planned_areas": planned_areas,
            "intent": ActionType.NEXT,
            "last_feedback_bundle": None,
            "allowed_actions": [],
        }
    )


def test_a3_generation_failure_falls_back_to_existing_next():
    """A3: generation exception when more questions exist advances to next existing question."""
    mock_service = Mock()
    mock_service.generate_next_question.side_effect = ValueError("generation failed")

    q1 = build_question(qid="q1")
    q2 = build_question(qid="q2")
    state = _make_adaptive_state(questions=[q1, q2], planned_area_count=5, current_index=0)

    node = AdaptiveNavigationNode(lazy_service=mock_service)
    new_state = node(state)

    assert new_state.current_question_index == 1
    assert new_state.awaiting_user_input is True


def test_a3_generation_failure_on_last_question_stays_put():
    """A3: generation exception when on last question stays on it (allows generate-report)."""
    mock_service = Mock()
    mock_service.generate_next_question.side_effect = ValueError("exhausted")

    q1 = build_question(qid="q1")
    state = _make_adaptive_state(questions=[q1], planned_area_count=5, current_index=0)

    node = AdaptiveNavigationNode(lazy_service=mock_service)
    new_state = node(state)

    assert new_state.current_question_index == 0
    assert new_state.awaiting_user_input is True


def test_a3_happy_path_appends_new_question():
    """A3: successful generation still appends question and advances index."""
    new_q = build_question(qid="q2")
    mock_memory = Mock()
    mock_service = Mock()
    mock_service.generate_next_question.return_value = (new_q, mock_memory)

    q1 = build_question(qid="q1")
    state = _make_adaptive_state(questions=[q1], planned_area_count=5, current_index=0)

    node = AdaptiveNavigationNode(lazy_service=mock_service)
    new_state = node(state)

    assert len(new_state.questions) == 2
    assert new_state.current_question_index == 1
