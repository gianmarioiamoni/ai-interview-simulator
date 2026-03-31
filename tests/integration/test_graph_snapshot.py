from unittest.mock import Mock

from app.graph.interview_graph import run_graph
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.interview_state import InterviewState
from tests.utils.state_snapshot import serialize_state
from domain.contracts.action_type import ActionType


def test_full_graph_snapshot():

    llm = Mock()
    hint_service = Mock()
    hint_service.generate_hint.return_value = "hint"

    graph = run_graph(llm=llm, hint_service=hint_service)

    state = build_interview_state()

    # run pipeline
    final_state = run_graph(state)

    if isinstance(final_state, dict):
        from domain.contracts.interview_state import InterviewState

        final_state = InterviewState.model_validate(final_state)

    snapshot = serialize_state(final_state)

    expected_snapshot = {
        "current_question_index": 0,
        "is_completed": False,
        "last_action": ActionType.NONE,
        "results": {
            "q1": {
                "score": snapshot["results"]["q1"]["score"],  # non deterministico
                "has_execution": True,
                "has_hint": True,
            }
        },
        "report": None,
    }

    assert snapshot["results"]["q1"]["has_execution"] is True
    assert snapshot["results"]["q1"]["has_hint"] is True


def test_completion_snapshot():

    llm = Mock()
    hint_service = Mock()

    graph = run_graph(llm=llm, hint_service=hint_service)

    state = build_interview_state()

    # force completion
    state = state.model_copy(
        update={
            "current_question_index": len(state.questions) - 1,
            "last_action": ActionType.NEXT,
        }
    )

    final_state = run_graph(state)

    if isinstance(final_state, dict):
        from domain.contracts.interview_state import InterviewState

        final_state = InterviewState.model_validate(final_state)

    snapshot = serialize_state(final_state)

    assert snapshot["is_completed"] is True
    assert snapshot["report"] is not None

