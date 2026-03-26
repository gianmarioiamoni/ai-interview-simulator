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
