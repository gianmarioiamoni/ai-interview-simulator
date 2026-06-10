# tests/graph/nodes/test_feedback_node.py

from unittest.mock import Mock

from app.graph.nodes.feedback_node import FeedbackNode
from tests.factories.interview_state_factory import build_state_with_execution


def _build_node() -> FeedbackNode:
    return FeedbackNode(Mock())


def test_feedback_quality_incorrect():

    node = _build_node()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
    )

    new_state = node(state)

    bundle = new_state.last_feedback_bundle

    assert bundle is not None
    assert bundle.overall_quality == "incorrect"


def test_feedback_quality_partial():

    node = _build_node()

    state = build_state_with_execution(
        passed_tests=3,
        total_tests=5,
    )

    new_state = node(state)

    assert new_state.last_feedback_bundle.overall_quality == "partial"


def test_feedback_quality_correct():

    node = _build_node()

    state = build_state_with_execution(
        passed_tests=5,
        total_tests=5,
    )

    new_state = node(state)

    assert new_state.last_feedback_bundle.overall_quality in ("correct", "optimal")


def test_feedback_runtime_error():

    node = _build_node()

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

    node = _build_node()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=0,
        error="No tests detected",
    )

    new_state = node(state)

    bundle = new_state.last_feedback_bundle

    assert bundle is not None


def test_feedback_generates_signal_on_error():

    node = _build_node()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=0,
        error="syntax error",
    )

    new_state = node(state)

    bundle = new_state.last_feedback_bundle

    signals = [s for block in bundle.blocks for s in block.signals]

    assert len(signals) > 0
    assert any(s.severity == "error" for s in signals)


def test_feedback_generates_learning_for_partial():

    node = _build_node()

    state = build_state_with_execution(
        passed_tests=3,
        total_tests=5,
    )

    new_state = node(state)

    learning = [
        item
        for block in new_state.last_feedback_bundle.blocks
        for item in block.learning
    ]

    assert len(learning) > 0
