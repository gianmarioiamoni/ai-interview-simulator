# tests/services/humanizer/test_humanizer_policy_engine.py

from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.humanizer_policy_engine import HumanizerPolicyEngine
from tests.factories.interview_state_factory import build_interview_state


def _make_input(
    follow_up_count: int = 0,
    last_turn_was_follow_up: bool = False,
    last_answer_score: int | None = None,
) -> HumanizerInput:

    state = build_interview_state()

    return HumanizerInput(
        current_question=state.current_question,
        follow_up_count=follow_up_count,
        last_turn_was_follow_up=last_turn_was_follow_up,
        last_answer_score=last_answer_score,
    )


def test_returns_direct_question_when_limit_reached() -> None:

    engine = HumanizerPolicyEngine()

    input_data = _make_input(
        follow_up_count=HumanizerPolicyEngine.MAX_FOLLOW_UPS,
        last_answer_score=10,
    )

    assert engine.decide(input_data) == HumanizerDecision.DIRECT_QUESTION


def test_returns_remark_plus_question_after_consecutive_follow_up() -> None:

    engine = HumanizerPolicyEngine()

    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=True,
        last_answer_score=10,
    )

    assert engine.decide(input_data) == HumanizerDecision.REMARK_PLUS_QUESTION


def test_returns_direct_question_when_no_score_available() -> None:

    engine = HumanizerPolicyEngine()

    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=False,
        last_answer_score=None,
    )

    assert engine.decide(input_data) == HumanizerDecision.DIRECT_QUESTION


def test_returns_follow_up_when_score_meets_threshold() -> None:

    engine = HumanizerPolicyEngine()

    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=False,
        last_answer_score=HumanizerPolicyEngine.FOLLOW_UP_THRESHOLD,
    )

    assert engine.decide(input_data) == HumanizerDecision.FOLLOW_UP


def test_returns_follow_up_when_score_exceeds_threshold() -> None:

    engine = HumanizerPolicyEngine()

    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=False,
        last_answer_score=HumanizerPolicyEngine.FOLLOW_UP_THRESHOLD + 1,
    )

    assert engine.decide(input_data) == HumanizerDecision.FOLLOW_UP


def test_returns_remark_plus_question_when_score_below_threshold() -> None:

    engine = HumanizerPolicyEngine()

    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=False,
        last_answer_score=HumanizerPolicyEngine.FOLLOW_UP_THRESHOLD - 1,
    )

    assert engine.decide(input_data) == HumanizerDecision.REMARK_PLUS_QUESTION


def test_limit_check_takes_priority_over_score() -> None:

    engine = HumanizerPolicyEngine()

    # High score but limit already reached
    input_data = _make_input(
        follow_up_count=HumanizerPolicyEngine.MAX_FOLLOW_UPS,
        last_answer_score=10,
    )

    assert engine.decide(input_data) == HumanizerDecision.DIRECT_QUESTION


def test_consecutive_check_takes_priority_over_score() -> None:

    engine = HumanizerPolicyEngine()

    # High score but last turn was a follow-up
    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=True,
        last_answer_score=10,
    )

    assert engine.decide(input_data) == HumanizerDecision.REMARK_PLUS_QUESTION


def test_follow_up_disabled_returns_remark_plus_question_on_optimal_score() -> None:

    engine = HumanizerPolicyEngine(follow_up_enabled=False)

    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=False,
        last_answer_score=HumanizerPolicyEngine.FOLLOW_UP_THRESHOLD,
    )

    assert engine.decide(input_data) == HumanizerDecision.REMARK_PLUS_QUESTION


def test_follow_up_enabled_by_default() -> None:

    engine = HumanizerPolicyEngine()

    input_data = _make_input(
        follow_up_count=0,
        last_turn_was_follow_up=False,
        last_answer_score=HumanizerPolicyEngine.FOLLOW_UP_THRESHOLD,
    )

    assert engine.decide(input_data) == HumanizerDecision.FOLLOW_UP


def test_threshold_aligns_with_quality_optimal_rank() -> None:
    from domain.contracts.feedback.quality import Quality

    assert HumanizerPolicyEngine.FOLLOW_UP_THRESHOLD == Quality.OPTIMAL.rank()
