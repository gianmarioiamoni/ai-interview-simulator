# tests/services/humanizer/test_followup_max_limit.py
#
# Validates follow-up suppression when the per-interview limit is reached,
# consecutive follow-up protection, and state counter integrity.

from unittest.mock import Mock

from app.graph.nodes.question_node import build_question_node
from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.humanizer_policy_engine import HumanizerPolicyEngine
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.question.question import QuestionType


# ─────────────────────────────────────────────────────────────────────────────
# Policy-level limit enforcement
# ─────────────────────────────────────────────────────────────────────────────

def _make_input(follow_up_count: int, last_turn_was_follow_up: bool = False, score: int | None = 10) -> HumanizerInput:

    state = build_interview_state()

    return HumanizerInput(
        current_question=state.current_question,
        follow_up_count=follow_up_count,
        last_turn_was_follow_up=last_turn_was_follow_up,
        last_answer_score=score,
    )


def test_policy_suppresses_follow_up_at_max_limit() -> None:

    engine = HumanizerPolicyEngine()
    max_limit = HumanizerPolicyEngine.MAX_FOLLOW_UPS

    result = engine.decide(_make_input(follow_up_count=max_limit, score=10))

    assert result == HumanizerDecision.DIRECT_QUESTION


def test_policy_suppresses_follow_up_above_max_limit() -> None:

    engine = HumanizerPolicyEngine()
    max_limit = HumanizerPolicyEngine.MAX_FOLLOW_UPS

    result = engine.decide(_make_input(follow_up_count=max_limit + 5, score=10))

    assert result == HumanizerDecision.DIRECT_QUESTION


def test_policy_allows_follow_up_below_limit() -> None:

    engine = HumanizerPolicyEngine()
    max_limit = HumanizerPolicyEngine.MAX_FOLLOW_UPS

    result = engine.decide(_make_input(follow_up_count=max_limit - 1, score=10))

    assert result == HumanizerDecision.FOLLOW_UP


def test_policy_suppresses_consecutive_follow_up() -> None:

    engine = HumanizerPolicyEngine()

    result = engine.decide(_make_input(follow_up_count=0, last_turn_was_follow_up=True, score=10))

    assert result == HumanizerDecision.REMARK_PLUS_QUESTION


# ─────────────────────────────────────────────────────────────────────────────
# question_node state counter integrity
# ─────────────────────────────────────────────────────────────────────────────

def test_question_node_increments_follow_up_count_on_follow_up() -> None:
    from unittest.mock import patch
    from domain.contracts.feedback.quality import Quality
    from domain.contracts.feedback.severity import Severity
    from app.contracts.feedback_bundle import FeedbackBundle

    llm = Mock()
    llm.invoke.return_value = Mock(
        content='{"decision": "follow_up", "message": "follow-up question", "follow_up_used": true}'
    )

    # Enable follow_up in settings so policy can return FOLLOW_UP
    with patch("app.graph.nodes.question_node.settings") as mock_settings:
        mock_settings.humanizer_follow_up_enabled = True
        node = build_question_node(llm)

        state = build_interview_state()
        q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
        # Provide OPTIMAL feedback bundle so policy evaluates score >= threshold (4)
        bundle = FeedbackBundle(
            blocks=[],
            overall_severity=Severity.INFO,
            overall_confidence=1.0,
            overall_quality=Quality.OPTIMAL,
            markdown="",
        )
        state = state.model_copy(
            update={
                "questions": [q],
                "chat_history": [],
                "current_question_index": 0,
                "follow_up_count": 0,
                "enable_humanizer": True,
                "last_feedback_bundle": bundle,
                "last_humanizer_follow_up": False,
            }
        )

        new_state = node(state)

    assert new_state.follow_up_count == 1
    assert new_state.last_humanizer_follow_up is True


def test_question_node_does_not_increment_count_on_direct_question() -> None:

    llm = Mock()
    llm.invoke.return_value = Mock(
        content='{"decision": "direct_question", "message": "next question"}'
    )

    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "follow_up_count": 1,
            "enable_humanizer": True,
        }
    )

    new_state = node(state)

    assert new_state.follow_up_count == 1
    assert new_state.last_humanizer_follow_up is False


def test_question_node_follow_up_count_not_incremented_when_humanizer_disabled() -> None:

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    state = state.model_copy(
        update={
            "enable_humanizer": False,
            "follow_up_count": 0,
        }
    )

    new_state = node(state)

    assert new_state.follow_up_count == 0
    llm.invoke.assert_not_called()


def test_question_node_sets_last_humanizer_follow_up_false_on_non_follow_up() -> None:

    llm = Mock()
    llm.invoke.return_value = Mock(
        content='{"decision": "remark_plus_question", "message": "Good point, now..."}'
    )

    node = build_question_node(llm)

    state = build_interview_state()
    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})
    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "last_humanizer_follow_up": True,
            "enable_humanizer": True,
        }
    )

    new_state = node(state)

    assert new_state.last_humanizer_follow_up is False
