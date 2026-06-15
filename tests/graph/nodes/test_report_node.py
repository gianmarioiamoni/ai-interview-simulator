# tests/graph/nodes/test_report_node.py

from unittest.mock import Mock

from app.graph.nodes.report_node import report_node
from tests.factories.interview_state_factory import build_interview_state

from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question_evaluation import QuestionEvaluation


def test_report_node_clears_is_processing():

    state = build_interview_state()
    state = state.model_copy(update={"is_processing": True, "current_step": "some_step"})

    new_state = report_node(state)

    assert new_state.is_processing is False


def test_report_node_clears_current_step():

    state = build_interview_state()
    state = state.model_copy(update={"is_processing": True, "current_step": "generating_report"})

    new_state = report_node(state)

    assert new_state.current_step is None


def test_report_node_preserves_interview_evaluation():

    state = build_interview_state()
    interview_eval = Mock()
    state = state.model_copy(
        update={
            "interview_evaluation": interview_eval,
            "is_processing": True,
            "current_step": "report",
        }
    )

    new_state = report_node(state)

    assert new_state.interview_evaluation is interview_eval
    assert new_state.is_processing is False
    assert new_state.current_step is None


def test_report_node_clears_processing_when_evaluation_is_none():

    state = build_interview_state()
    state = state.model_copy(
        update={
            "interview_evaluation": None,
            "is_processing": True,
            "current_step": "report",
        }
    )

    new_state = report_node(state)

    assert new_state.is_processing is False
    assert new_state.current_step is None
    assert new_state.interview_evaluation is None


def test_report_node_clears_processing_when_results_empty():

    state = build_interview_state()
    state = state.model_copy(
        update={
            "results_by_question": {},
            "interview_evaluation": None,
            "is_processing": True,
            "current_step": "report",
        }
    )

    new_state = report_node(state)

    assert new_state.is_processing is False
    assert new_state.current_step is None
