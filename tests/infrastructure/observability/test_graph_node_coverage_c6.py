# tests/infrastructure/observability/test_graph_node_coverage_c6.py
#
# EPIC-08 P2/C6 — batch B instrumentation + production coverage gate (OBS-02/05).

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

from domain.contracts.interview_state import InterviewState
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_request import ReplayRequest
from infrastructure.observability.graph_node_logging import (
    BATCH_A_GRAPH_NODES,
    BATCH_B_GRAPH_NODES,
    PRODUCTION_GRAPH_NODES,
    instrument_graph_node,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
INTERVIEW_GRAPH_PATH = REPO_ROOT / "app" / "graph" / "interview_graph.py"
REPLAY_GRAPH_PATH = REPO_ROOT / "app" / "graph" / "replay_graph.py"
GRAPH_ROOT = REPO_ROOT / "app" / "graph"


def _instrumented_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_instrument = (
            isinstance(func, ast.Name) and func.id == "instrument_graph_node"
        ) or (
            isinstance(func, ast.Attribute) and func.attr == "instrument_graph_node"
        )
        if not is_instrument or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            names.add(first.value)
        elif isinstance(first, ast.Name) and first.id == "_REPLAY_NODE_NAME":
            names.add("replay")
    return names


def _add_node_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_add_node = isinstance(func, ast.Attribute) and func.attr == "add_node"
        if not is_add_node or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            names.add(first.value)
        elif isinstance(first, ast.Name) and first.id == "_REPLAY_NODE_NAME":
            names.add("replay")
    return names


class TestBatchBInventory:
    def test_batch_b_includes_remaining_production_nodes(self) -> None:
        assert BATCH_B_GRAPH_NODES == frozenset(
            {
                "entry",
                "session_close",
                "report",
                "longitudinal_update",
                "replay",
            }
        )

    def test_production_nodes_are_union_of_batches(self) -> None:
        assert PRODUCTION_GRAPH_NODES == BATCH_A_GRAPH_NODES | BATCH_B_GRAPH_NODES
        assert BATCH_A_GRAPH_NODES.isdisjoint(BATCH_B_GRAPH_NODES)


class TestCoverageGate:
    def test_all_production_nodes_are_instrumented(self) -> None:
        interview = _instrumented_names(
            INTERVIEW_GRAPH_PATH.read_text(encoding="utf-8")
        )
        replay = _instrumented_names(REPLAY_GRAPH_PATH.read_text(encoding="utf-8"))
        instrumented = interview | replay
        assert instrumented == PRODUCTION_GRAPH_NODES

    def test_every_registered_graph_node_is_instrumented(self) -> None:
        interview_source = INTERVIEW_GRAPH_PATH.read_text(encoding="utf-8")
        replay_source = REPLAY_GRAPH_PATH.read_text(encoding="utf-8")
        registered = _add_node_names(interview_source) | _add_node_names(replay_source)
        instrumented = _instrumented_names(interview_source) | _instrumented_names(
            replay_source
        )
        assert registered == PRODUCTION_GRAPH_NODES
        assert registered == instrumented

    def test_no_direct_emit_structured_log_in_graph_modules(self) -> None:
        """Sole node emission path is instrument_graph_node → emit_structured_log."""
        violations: list[str] = []
        for path in GRAPH_ROOT.rglob("*.py"):
            relative = path.relative_to(REPO_ROOT).as_posix()
            source = path.read_text(encoding="utf-8")
            if "emit_structured_log" not in source:
                continue
            # Graph builders may import the wrapper only.
            if "from infrastructure.observability" in source or (
                "instrument_graph_node" in source
            ):
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        for alias in node.names:
                            if alias.name == "emit_structured_log":
                                violations.append(f"{relative}: imports emit_structured_log")
                    if isinstance(node, ast.Call):
                        func = node.func
                        if isinstance(func, ast.Name) and func.id == "emit_structured_log":
                            violations.append(f"{relative}: calls emit_structured_log")
                        if (
                            isinstance(func, ast.Attribute)
                            and func.attr == "emit_structured_log"
                        ):
                            violations.append(f"{relative}: calls emit_structured_log")
                continue
            violations.append(f"{relative}: unexpected emit_structured_log reference")
        assert violations == []


class TestBatchBEmission:
    def test_entry_emits_obs02_fields(self, caplog) -> None:
        state = InterviewState.create_empty()
        state = state.model_copy(update={"interview_id": "sess-entry"})
        wrapped = instrument_graph_node("entry", lambda s: s)
        logger = logging.getLogger("infrastructure.observability.structured_log")
        with caplog.at_level(logging.INFO, logger=logger.name):
            wrapped(state)
        payload = json.loads(caplog.records[0].getMessage())
        assert payload["session_id"] == "sess-entry"
        assert payload["graph_node"] == "entry"
        assert payload["status"] == "success"
        assert isinstance(payload["duration_ms"], (int, float))

    def test_replay_resolves_session_id_from_request(self, caplog) -> None:
        state = {
            "request": ReplayRequest(
                session_id="replay-sess-1",
                replay_mode=ReplayMode.STANDARD,
                replay_level=ReplayLevel.PRESENTATION,
            ),
            "result": None,
        }
        wrapped = instrument_graph_node("replay", lambda s: s)
        logger = logging.getLogger("infrastructure.observability.structured_log")
        with caplog.at_level(logging.INFO, logger=logger.name):
            wrapped(state)
        payload = json.loads(caplog.records[0].getMessage())
        assert payload["session_id"] == "replay-sess-1"
        assert payload["graph_node"] == "replay"
        assert payload["status"] == "success"
        assert "duration_ms" in payload
