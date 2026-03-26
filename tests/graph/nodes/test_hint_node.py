# tests/unit/graph/nodes/test_hint_node.py

from unittest.mock import Mock

from app.graph.nodes.hint_node import HintNode
from domain.contracts.execution_result import ExecutionResult, ExecutionStatus, ExecutionType


def test_hint_level_error_progression():

    node = HintNode(Mock())

    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.RUNTIME_ERROR,
        success=False,
        output="",
        error="boom",
        passed_tests=0,
        total_tests=0,
        execution_time_ms=0,
        test_results=[],
    )

    level1 = node._resolve_hint_level(1, "unknown", execution)
    level2 = node._resolve_hint_level(2, "unknown", execution)

    assert level1.name == "TARGETED"
    assert level2.name == "SOLUTION"


def test_hint_respects_quality_correct():

    node = HintNode(Mock())

    level = node._resolve_hint_level(1, "correct", None)

    assert level.name == "NONE"


def test_hint_unknown_quality_fallback():

    node = HintNode(Mock())

    level = node._resolve_hint_level(2, "unknown", None)

    assert level.name == "BASIC"
