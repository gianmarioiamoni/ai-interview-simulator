# tests/graph/nodes/test_written_evaluation_node.py

from unittest.mock import Mock

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
    from domain.contracts.question_result import QuestionResult

    result = QuestionResult(question_id=q.id)
    result = result.model_copy(update={"evaluation": Mock()})

    state = state.model_copy(update={"results_by_question": {q.id: result}})

    new_state = node(state)

    assert new_state == state


def test_written_eval_success():

    llm = Mock()

    llm.invoke.return_value = Mock(
        content='{"score": 80, "feedback": "good", "strengths": [], "weaknesses": []}'
    )

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
