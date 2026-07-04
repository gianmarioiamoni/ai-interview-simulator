# tests/integration/use_cases/test_evaluate_answer_execution.py

# Integration test for execution via LangGraph inside EvaluateAnswerUseCase

import pytest
from unittest.mock import Mock

import app.graph.nodes.navigation_node as _nav_module
from app.graph.interview_graph import build_interview_graph
from app.graph.nodes.navigation_node import configure_navigation_node
from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase

from domain.contracts.ai.ai_hint import AIHint
from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.shared.action_type import ActionType

from tests.factories.interview_state_factory import (
    build_interview_state,
    build_state_with_execution,
)


@pytest.fixture(autouse=True)
def _configure_node():
    configure_navigation_node()
    yield
    _nav_module._default_navigation_node = None


TEST_HINT = AIHint(explanation="test hint", suggestion="check your function name")


def test_execution_via_graph_updates_state():

    llm = Mock()
    mock_hint_service = Mock()

    graph = build_interview_graph(llm=llm, hint_service=mock_hint_service)

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        interview_graph=graph,
        hint_service=mock_hint_service,
    )

    state = build_interview_state()

    new_state = use_case.execute(state)

    result = new_state.get_result_for_question("q1")

    assert result is not None
    assert result.execution is not None
    assert result.evaluation is not None
    assert result.ai_hint is not None
    assert result.hint_level is not None


def test_hint_is_generated():

    llm = Mock()

    mock_hint_service = Mock()
    mock_hint_service.generate_hint.return_value = TEST_HINT

    graph = build_interview_graph(llm=llm, hint_service=mock_hint_service)

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        interview_graph=graph,
        hint_service=mock_hint_service,
    )

    state = build_interview_state()

    new_state = use_case.execute(state)

    result = new_state.get_result_for_question("q1")

    assert result.ai_hint == TEST_HINT
    assert result.hint_level is not None


def test_hint_not_generated_twice():

    llm = Mock()

    mock_hint_service = Mock()
    mock_hint_service.generate_hint.return_value = TEST_HINT

    graph = build_interview_graph(llm=llm, hint_service=mock_hint_service)

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        interview_graph=graph,
        hint_service=mock_hint_service,
    )

    state = build_interview_state()

    state = use_case.execute(state)
    state = use_case.execute(state)

    mock_hint_service.generate_hint.assert_called_once()


def test_pipeline_is_idempotent():

    llm = Mock()
    mock_hint_service = Mock()
    mock_hint_service.generate_hint.return_value = TEST_HINT

    graph = build_interview_graph(llm=llm, hint_service=mock_hint_service)

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        interview_graph=graph,
        hint_service=mock_hint_service,
    )

    state = build_interview_state()

    first_state = use_case.execute(state)
    second_state = use_case.execute(first_state)

    result1 = first_state.get_result_for_question("q1")
    result2 = second_state.get_result_for_question("q1")

    assert result1.execution == result2.execution
    assert result1.evaluation == result2.evaluation
    assert result1.ai_hint == result2.ai_hint

    if first_state.is_completed:
        assert first_state.interview_evaluation == second_state.interview_evaluation


class FakeLLMResponse(str):
    """String response that also exposes .content like provider payloads."""

    @property
    def content(self) -> str:
        return str(self)


def test_report_generated_when_completed():

    llm = Mock()
    llm.invoke.return_value = FakeLLMResponse("Executive summary of the interview.")
    llm.invoke_json.side_effect = ValueError("structured output unavailable")
    mock_hint_service = Mock()

    graph = build_interview_graph(llm=llm, hint_service=mock_hint_service)

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        interview_graph=graph,
        hint_service=mock_hint_service,
    )

    state = build_state_with_execution(passed_tests=2, total_tests=2)

    # attach an evaluation to the executed question
    result = state.get_result_for_question("q1")
    evaluated = result.model_copy(
        update={
            "evaluation": QuestionEvaluation(
                question_id="q1",
                score=100.0,
                max_score=100.0,
                feedback="All tests passed.",
                passed=True,
            )
        }
    )
    state = state.model_copy(
        update={
            "results_by_question": {**state.results_by_question, "q1": evaluated}
        }
    )

    # final state: last question reached, user requested the report
    state = state.model_copy(
        update={
            "current_question_index": len(state.questions) - 1,
            "intent": ActionType.GENERATE_REPORT,
            "awaiting_user_input": False,
        }
    )

    graph_result = graph.invoke(state)

    if isinstance(graph_result, dict):
        new_state = InterviewState.model_validate(graph_result)
    else:
        new_state = graph_result

    assert new_state.is_completed is True
    assert new_state.is_processing is False
    assert hasattr(new_state, "interview_evaluation")
