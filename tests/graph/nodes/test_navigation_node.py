# tests/graph/nodes/test_navigation_node.py
"""Navigation node tests.

All tests configure the node via configure_navigation_node() before
invocation — consistent with the startup contract (PAT-06).
"""

import pytest

import app.graph.nodes.navigation_node as _nav_module
from app.graph.nodes.navigation_node import configure_navigation_node, navigation_node
from tests.factories.interview_state_factory import build_interview_state, build_question
from domain.contracts.shared.action_type import ActionType
from domain.contracts.interview.answer import Answer
from domain.contracts.feedback.quality import Quality
from domain.contracts.feedback.severity import Severity
from app.contracts.feedback_bundle import FeedbackBundle
from domain.contracts.question.question import QuestionType


@pytest.fixture(autouse=True)
def _configure_node():
    """Configure the navigation node before every test and reset after."""
    configure_navigation_node()
    yield
    _nav_module._default_navigation_node = None


# ---------------------------------------------------------------------------
# Invariant: unconfigured node must raise RuntimeError
# ---------------------------------------------------------------------------


def test_unconfigured_navigation_node_raises():
    """PAT-06: navigation_node must raise RuntimeError when not configured."""
    _nav_module._default_navigation_node = None
    state = build_interview_state()
    with pytest.raises(RuntimeError, match="configure_navigation_node"):
        navigation_node(state)


def test_legacy_navigation_node_does_not_exist():
    """_legacy_navigation_node must not exist in the module."""
    assert not hasattr(_nav_module, "_legacy_navigation_node"), (
        "_legacy_navigation_node still exists in navigation_node module"
    )


# ---------------------------------------------------------------------------
# Navigation behaviour (via AdaptiveNavigationNode)
# ---------------------------------------------------------------------------


def test_navigation_next_moves_forward():
    state = build_interview_state()
    state = state.model_copy(
        update={
            "current_question_index": 0,
            "intent": ActionType.NEXT,
        }
    )

    new_state = navigation_node(state)

    assert new_state.current_question_index == 1
    assert new_state.awaiting_user_input is True
    assert new_state.intent is None


def test_navigation_retry_keeps_same_question():
    state = build_interview_state()
    state = state.model_copy(
        update={
            "current_question_index": 1,
            "intent": ActionType.RETRY,
        }
    )

    new_state = navigation_node(state)

    assert new_state.current_question_index == 1
    assert new_state.awaiting_user_input is True
    assert new_state.intent is None


def test_navigation_does_not_overflow():
    state = build_interview_state()
    last_index = len(state.questions) - 1
    state = state.model_copy(
        update={
            "current_question_index": last_index,
            "intent": ActionType.NEXT,
        }
    )

    new_state = navigation_node(state)

    assert new_state.current_question_index == last_index


def test_navigation_with_no_questions_is_safe():
    state = build_interview_state()
    state = state.model_copy(update={"questions": []})

    new_state = navigation_node(state)

    assert new_state == state


def test_navigation_next_captures_last_question_context() -> None:
    q1 = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    q2 = build_question(qid="q2", qtype=QuestionType.WRITTEN)
    answer = Answer(question_id="q1", content="My answer", attempt=1)
    bundle = FeedbackBundle(
        blocks=[],
        overall_severity=Severity.INFO,
        overall_confidence=1.0,
        overall_quality=Quality.OPTIMAL,
        markdown="",
    )

    state = build_interview_state(questions=[q1, q2])
    state = state.model_copy(
        update={
            "answers": [answer],
            "last_feedback_bundle": bundle,
            "current_question_index": 0,
            "intent": ActionType.NEXT,
        }
    )

    new_state = navigation_node(state)

    ctx = new_state.last_question_context
    assert ctx is not None
    assert ctx.question_id == "q1"
    assert ctx.question_prompt == q1.prompt
    assert ctx.answer_content == "My answer"
    assert ctx.quality_rank == Quality.OPTIMAL.rank()


def test_navigation_next_context_none_on_last_question() -> None:
    state = build_interview_state()
    last = len(state.questions) - 1
    state = state.model_copy(
        update={
            "current_question_index": last,
            "intent": ActionType.NEXT,
        }
    )

    new_state = navigation_node(state)

    assert new_state.last_question_context is None


def test_navigation_next_clears_question_display_text() -> None:
    q1 = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    q2 = build_question(qid="q2", qtype=QuestionType.WRITTEN)

    state = build_interview_state(questions=[q1, q2])
    state = state.model_copy(
        update={
            "current_question_index": 0,
            "intent": ActionType.NEXT,
            "question_display_text": "Stale humanized text from Q1",
        }
    )

    new_state = navigation_node(state)

    assert new_state.question_display_text is None


def test_navigation_next_snapshot_previous_area_populated() -> None:
    q1 = build_question(qid="q1", qtype=QuestionType.WRITTEN)
    q2 = build_question(qid="q2", qtype=QuestionType.WRITTEN)

    state = build_interview_state(questions=[q1, q2])
    state = state.model_copy(
        update={
            "current_question_index": 0,
            "intent": ActionType.NEXT,
        }
    )

    new_state = navigation_node(state)

    ctx = new_state.last_question_context
    assert ctx is not None
    expected_area = q1.area.value if q1.area is not None else None
    assert ctx.question_area == expected_area
