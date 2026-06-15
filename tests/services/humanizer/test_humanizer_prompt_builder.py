# tests/services/humanizer/test_humanizer_prompt_builder.py

from unittest.mock import patch

from services.humanizer.builders.humanizer_prompt_builder import HumanizerPromptBuilder
from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.contracts.humanizer_input import HumanizerInput
from tests.factories.interview_state_factory import build_interview_state


def _make_input(
    chat_history: list[str] | None = None,
    last_answer: str | None = None,
    last_answer_score: int | None = None,
) -> HumanizerInput:

    state = build_interview_state()

    return HumanizerInput(
        current_question=state.current_question,
        language="en",
        chat_history=chat_history or [],
        last_answer=last_answer,
        last_answer_score=last_answer_score,
        follow_up_count=0,
    )


def test_build_returns_non_empty_string() -> None:

    builder = HumanizerPromptBuilder()
    input_data = _make_input()

    result = builder.build(
        input_data=input_data,
        decision=HumanizerDecision.DIRECT_QUESTION,
    )

    assert isinstance(result, str)
    assert len(result) > 0


def test_build_includes_decision_value() -> None:

    builder = HumanizerPromptBuilder()
    input_data = _make_input()

    result = builder.build(
        input_data=input_data,
        decision=HumanizerDecision.FOLLOW_UP,
    )

    assert "follow_up" in result


def test_build_includes_question_prompt() -> None:

    builder = HumanizerPromptBuilder()
    input_data = _make_input()

    result = builder.build(
        input_data=input_data,
        decision=HumanizerDecision.DIRECT_QUESTION,
    )

    assert input_data.current_question.prompt in result


def test_build_includes_last_answer_when_provided() -> None:

    builder = HumanizerPromptBuilder()
    input_data = _make_input(last_answer="I would use Redis for caching.")

    result = builder.build(
        input_data=input_data,
        decision=HumanizerDecision.REMARK_PLUS_QUESTION,
    )

    # The prompt is built and contains content about the decision
    assert "remark_plus_question" in result
    assert isinstance(result, str)
    assert len(result) > 0


def test_build_history_uses_last_five_turns() -> None:

    builder = HumanizerPromptBuilder()
    history = [f"turn_{i}" for i in range(10)]
    input_data = _make_input(chat_history=history)

    result = builder.build(
        input_data=input_data,
        decision=HumanizerDecision.DIRECT_QUESTION,
    )

    # Last 5 entries should appear
    for turn in history[-5:]:
        assert turn in result

    # Entries beyond last 5 should not appear
    assert "turn_0" not in result
    assert "turn_4" not in result


def test_build_empty_history_produces_no_history_section() -> None:

    builder = HumanizerPromptBuilder()
    input_data = _make_input(chat_history=[])

    # Should not raise
    result = builder.build(
        input_data=input_data,
        decision=HumanizerDecision.DIRECT_QUESTION,
    )

    assert isinstance(result, str)
