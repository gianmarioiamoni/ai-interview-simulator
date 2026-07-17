# tests/infrastructure/observability/test_graph_node_logging_c5.py
#
# EPIC-08 P2/C5 — batch A node instrumentation via sole structured-log helper.

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from domain.contracts.interview_state import InterviewState
from infrastructure.observability.graph_node_logging import (
    BATCH_A_GRAPH_NODES,
    BATCH_B_GRAPH_NODES,
    instrument_graph_node,
)
from infrastructure.observability.structured_log import emit_structured_log

REPO_ROOT = Path(__file__).resolve().parents[3]
INTERVIEW_GRAPH_PATH = REPO_ROOT / "app" / "graph" / "interview_graph.py"


class TestBatchInventory:
    def test_batch_a_is_core_interview_cycle(self) -> None:
        assert BATCH_A_GRAPH_NODES == frozenset(
            {
                "start_processing",
                "navigation",
                "question",
                "router",
                "execution",
                "evaluation",
                "evaluation_aggregate",
                "feedback",
                "reasoner",
                "hint",
                "decision",
                "written",
                "completion",
            }
        )

    def test_batch_a_and_b_are_disjoint(self) -> None:
        assert BATCH_A_GRAPH_NODES.isdisjoint(BATCH_B_GRAPH_NODES)

    def test_interview_graph_instruments_all_batch_a_nodes(self) -> None:
        source = INTERVIEW_GRAPH_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        instrumented: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_instrument = (
                isinstance(func, ast.Name) and func.id == "instrument_graph_node"
            ) or (
                isinstance(func, ast.Attribute)
                and func.attr == "instrument_graph_node"
            )
            if not is_instrument or not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                instrumented.add(first.value)
        assert instrumented == BATCH_A_GRAPH_NODES

    def test_interview_graph_does_not_instrument_batch_b_yet(self) -> None:
        source = INTERVIEW_GRAPH_PATH.read_text(encoding="utf-8")
        for name in BATCH_B_GRAPH_NODES:
            assert f'instrument_graph_node("{name}"' not in source


class TestInstrumentGraphNode:
    def test_success_emits_required_obs02_fields(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        state = InterviewState.create_empty()
        state = state.model_copy(update={"interview_id": "sess-c5"})

        def _node(s: InterviewState) -> InterviewState:
            return s

        wrapped = instrument_graph_node("completion", _node)
        logger = logging.getLogger("infrastructure.observability.structured_log")
        with caplog.at_level(logging.INFO, logger=logger.name):
            result = wrapped(state)

        assert result.interview_id == "sess-c5"
        payloads = [json.loads(r.getMessage()) for r in caplog.records]
        assert len(payloads) == 1
        payload = payloads[0]
        assert payload["session_id"] == "sess-c5"
        assert payload["graph_node"] == "completion"
        assert payload["status"] == "success"
        assert isinstance(payload["duration_ms"], (int, float))
        assert payload["event"] == "graph_node.execute"
        assert payload["component"] == "langgraph"

    def test_failure_emits_then_rethrows(self, caplog: pytest.LogCaptureFixture) -> None:
        state = InterviewState.create_empty()
        state = state.model_copy(update={"interview_id": "sess-fail"})

        def _node(_s: InterviewState) -> InterviewState:
            raise RuntimeError("node boom")

        wrapped = instrument_graph_node("execution", _node)
        logger = logging.getLogger("infrastructure.observability.structured_log")
        with caplog.at_level(logging.ERROR, logger=logger.name):
            with pytest.raises(RuntimeError, match="node boom"):
                wrapped(state)

        payloads = [json.loads(r.getMessage()) for r in caplog.records]
        assert len(payloads) == 1
        assert payloads[0]["status"] == "failure"
        assert payloads[0]["error_type"] == "RuntimeError"
        assert payloads[0]["graph_node"] == "execution"
        assert payloads[0]["session_id"] == "sess-fail"

    def test_emission_uses_sole_helper(self) -> None:
        state = InterviewState.create_empty()
        wrapped = instrument_graph_node("router", lambda s: s)
        with patch(
            "infrastructure.observability.graph_node_logging.emit_structured_log",
            wraps=emit_structured_log,
        ) as mocked:
            wrapped(state)
        mocked.assert_called_once()
        kwargs = mocked.call_args.kwargs
        assert kwargs["graph_node"] == "router"
        assert kwargs["status"] == "success"

    def test_start_processing_behaviour_unchanged(self) -> None:
        from app.graph.nodes.start_processing_node import start_processing_node
        from domain.contracts.shared.action_type import ActionType

        state = InterviewState.create_empty()
        state = state.model_copy(update={"intent": ActionType.NEXT})
        wrapped = instrument_graph_node("start_processing", start_processing_node)
        with patch(
            "infrastructure.observability.graph_node_logging.emit_structured_log"
        ):
            result = wrapped(state)
        direct = start_processing_node(state)
        assert result.is_processing == direct.is_processing
        assert result.current_step == direct.current_step
