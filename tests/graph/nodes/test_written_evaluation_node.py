# tests/graph/nodes/test_written_evaluation_node.py

from unittest.mock import Mock, patch

from app.graph.nodes.written_evaluation_node import WrittenEvaluationNode
from tests.factories.interview_state_factory import build_interview_state


def test_written_eval_no_question_or_answer():

    llm = Mock()
    node = WrittenEvaluationNode(llm)

    state = build_interview_state()
    state = state.model_copy(update={"answers": []})

    new_state = node(state)

    assert new_state == state


def test_written_eval_idempotent():

    llm = Mock()
    node = WrittenEvaluationNode(llm)

    state = build_interview_state()

    q = state.current_question

    # simulate existing evaluation
    from domain.contracts.question.question_result import QuestionResult

    result = QuestionResult(question_id=q.id)
    result = result.model_copy(update={"evaluation": Mock()})

    state = state.model_copy(update={"results_by_question": {q.id: result}})

    new_state = node(state)

    assert new_state == state


@patch("app.graph.nodes.written_evaluation_node.EvaluationDecision")
def test_written_eval_success(mock_decision_cls):

    mock_decision = Mock()
    mock_decision.score = 80
    mock_decision.feedback = "good"
    mock_decision.strengths = []
    mock_decision.weaknesses = []

    mock_decision_cls.model_validate_json.return_value = mock_decision

    llm = Mock()
    llm.invoke.return_value = Mock(content="whatever")

    node = WrittenEvaluationNode(llm)

    state = build_interview_state()

    new_state = node(state)

    q = state.current_question
    result = new_state.get_result_for_question(q.id)

    assert result.evaluation.score == 80
    assert result.evaluation.passed is True


def test_written_eval_parsing_failure():

    llm = Mock()
    llm.invoke.return_value = Mock(content="INVALID JSON")

    node = WrittenEvaluationNode(llm)

    state = build_interview_state()

    new_state = node(state)

    q = state.current_question
    result = new_state.get_result_for_question(q.id)

    assert result.evaluation.score == 0
    assert result.evaluation.passed is False
    assert "parsing" in result.evaluation.feedback.lower()


def test_written_eval_immutable_update():

    llm = Mock()
    llm.invoke.return_value = Mock(content='{"score": 70, "feedback": "ok"}')

    node = WrittenEvaluationNode(llm)

    state = build_interview_state()

    new_state = node(state)

    assert new_state is not state
    assert new_state.results_by_question != state.results_by_question
