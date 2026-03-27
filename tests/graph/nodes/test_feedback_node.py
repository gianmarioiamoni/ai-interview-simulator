# tests/graph/nodes/test_feedback_node.py

from app.graph.nodes.feedback_node import FeedbackNode
from tests.factories.interview_state_factory import build_state_with_execution


def test_feedback_quality_incorrect():

    node = FeedbackNode()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
    )

    new_state = node(state)

    bundle = new_state.last_feedback_bundle

    assert bundle is not None
    assert bundle.overall_quality == "incorrect"


def test_feedback_quality_partial():

    node = FeedbackNode()

    state = build_state_with_execution(
        passed_tests=2,
        total_tests=5,
    )

    new_state = node(state)

    assert new_state.last_feedback_bundle.overall_quality == "partial"


def test_feedback_quality_correct():

    node = FeedbackNode()

    state = build_state_with_execution(
        passed_tests=5,
        total_tests=5,
    )

    new_state = node(state)

    assert new_state.last_feedback_bundle.overall_quality == "correct"


def test_feedback_runtime_error():

    node = FeedbackNode()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=0,
        error="syntax error",
    )

    new_state = node(state)

    bundle = new_state.last_feedback_bundle

    assert bundle.overall_quality == "incorrect"
    assert bundle.overall_severity == "error"


def test_feedback_no_tests_detected():

    node = FeedbackNode()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=0,
        error="No tests detected",
    )

    new_state = node(state)

    bundle = new_state.last_feedback_bundle

    assert bundle is not None
