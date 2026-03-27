# tests/integration/use_cases/test_evaluate_answer_execution.py

# Integration test for execution via LangGraph inside EvaluateAnswerUseCase

from unittest.mock import Mock

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.graph.interview_graph import build_interview_graph

from domain.contracts.interview_state import InterviewState

from tests.factories.interview_state_factory import build_interview_state


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
    mock_hint_service.generate_hint.return_value = "test hint"

    graph = build_interview_graph(llm=llm, hint_service=mock_hint_service)

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        interview_graph=graph,
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
    mock_hint_service.generate_hint.return_value = "hint"

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
        assert first_state.report_output == second_state.report_output


def test_report_generated_when_completed():

    llm = Mock()
    mock_hint_service = Mock()

    graph = build_interview_graph(llm=llm, hint_service=mock_hint_service)

    use_case = EvaluateAnswerUseCase(
        llm=llm,
        interview_graph=graph,
        hint_service=mock_hint_service,
    )

    state = build_interview_state()

    # forza stato finale
    state.current_question_index = len(state.questions) - 1
    state.last_action = "next"

    graph_result = graph.invoke(state)

    if isinstance(graph_result, dict):
        new_state = InterviewState.model_validate(graph_result)
    else:
        new_state = graph_result

    assert new_state.is_completed is True
    assert hasattr(new_state, "report_output")
    assert hasattr(new_state, "interview_evaluation")
