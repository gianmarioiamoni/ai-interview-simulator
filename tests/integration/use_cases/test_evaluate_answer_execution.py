# tests/integration/use_cases/test_evaluate_answer_execution.py

# Integration test for execution via LangGraph inside EvaluateAnswerUseCase

from unittest.mock import Mock

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from tests.factories.interview_state_factory import build_interview_state


def test_execution_via_graph_updates_state():

    # Arrange
    llm = Mock()
    mock_hint_service = Mock()  # 🔥 IMPORTANT

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        hint_service=mock_hint_service,  # 🔥 inject mock
    )

    state = build_interview_state()

    # Act
    new_state = use_case.execute(state)

    # Assert
    result = new_state.get_result_for_question("q1")

    assert result is not None
    assert result.execution is not None
    assert result.evaluation is not None


def test_hint_is_generated():

    llm = Mock()

    mock_hint_service = Mock()
    mock_hint_service.generate_hint.return_value = "test hint"

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        hint_service=mock_hint_service,
    )

    state = build_interview_state()

    new_state = use_case.execute(state)

    result = new_state.get_result_for_question("q1")

    assert result.ai_hint == "test hint"
    assert result.hint_level is not None


def test_hint_not_generated_twice():

    llm = Mock()

    mock_hint_service = Mock()
    mock_hint_service.generate_hint.return_value = "hint"

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        hint_service=mock_hint_service,
    )

    state = build_interview_state()

    state = use_case.execute(state)
    state = use_case.execute(state)

    # deve essere chiamato UNA SOLA VOLTA
    mock_hint_service.generate_hint.assert_called_once()
