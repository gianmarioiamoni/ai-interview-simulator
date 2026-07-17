# tests/app/graph/test_epic08_topology_invariants_c13.py
#
# EPIC-08 P5/C13 — LangGraph topology drift gate (SDN-03, SDN-04, IB-05).
# Freezes interview + replay nodes/edges/routers; EPIC-08 must not change them.

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

from langgraph.graph import END

from app.graph.interview_graph import build_interview_graph
from app.graph.replay_graph import build_replay_graph
from infrastructure.observability.graph_node_logging import PRODUCTION_GRAPH_NODES

REPO_ROOT = Path(__file__).resolve().parents[3]
INTERVIEW_GRAPH_PATH = REPO_ROOT / "app" / "graph" / "interview_graph.py"
REPLAY_GRAPH_PATH = REPO_ROOT / "app" / "graph" / "replay_graph.py"
GRAPH_ROOT = REPO_ROOT / "app" / "graph"
DOMAIN_ROOT = REPO_ROOT / "domain"

# Frozen EPIC-08 baseline (post–EPIC-07). Do not expand without Freeze revision.
FROZEN_INTERVIEW_NODES: frozenset[str] = frozenset(
    {
        "entry",
        "router",
        "navigation",
        "question",
        "execution",
        "evaluation",
        "evaluation_aggregate",
        "feedback",
        "reasoner",
        "hint",
        "decision",
        "written",
        "completion",
        "session_close",
        "report",
        "longitudinal_update",
        "start_processing",
    }
)

FROZEN_INTERVIEW_EDGES: frozenset[tuple[str, str]] = frozenset(
    {
        ("__start__", "entry"),
        ("entry", "router"),
        ("entry", "start_processing"),
        ("router", "execution"),
        ("router", "written"),
        ("execution", "evaluation"),
        ("evaluation", "hint"),
        ("hint", "feedback"),
        ("written", "feedback"),
        ("feedback", "reasoner"),
        ("reasoner", "decision"),
        ("decision", "navigation"),
        ("decision", "__end__"),
        ("start_processing", "navigation"),
        ("navigation", "question"),
        ("question", "completion"),
        ("completion", "evaluation_aggregate"),
        ("evaluation_aggregate", "session_close"),
        ("evaluation_aggregate", "__end__"),
        ("session_close", "report"),
        ("report", "longitudinal_update"),
        ("longitudinal_update", "__end__"),
    }
)

FROZEN_CONDITIONAL_ROUTERS: frozenset[tuple[str, str]] = frozenset(
    {
        ("entry", "route_entry"),
        ("router", "route_by_question_type"),
        ("decision", "route_after_decision"),
        ("evaluation_aggregate", "route_after_completion"),
    }
)

FROZEN_REPLAY_NODES: frozenset[str] = frozenset({"replay"})
FROZEN_REPLAY_EDGES: frozenset[tuple[str, str]] = frozenset(
    {
        ("__start__", "replay"),
        ("replay", "__end__"),
    }
)

_FORBIDDEN_LIFECYCLE_TOKENS: frozenset[str] = frozenset(
    {
        "SIGTERM",
        "ShutdownDrainController",
        "DrainMiddleware",
        "begin_drain",
        "process_edge.shutdown",
        "shutdown_drain",
    }
)


def _business_nodes(compiled) -> frozenset[str]:
    return frozenset(
        name
        for name in compiled.get_graph().nodes.keys()
        if name not in {"__start__", "__end__", END}
    )


def _edges(compiled) -> frozenset[tuple[str, str]]:
    return frozenset((edge.source, edge.target) for edge in compiled.get_graph().edges)


def _conditional_routers(source: str) -> frozenset[tuple[str, str]]:
    tree = ast.parse(source)
    found: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "add_conditional_edges"):
            continue
        if len(node.args) < 2:
            continue
        src_arg, router_arg = node.args[0], node.args[1]
        if not isinstance(src_arg, ast.Constant) or not isinstance(src_arg.value, str):
            continue
        if not isinstance(router_arg, ast.Name):
            continue
        found.add((src_arg.value, router_arg.id))
    return frozenset(found)


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


class TestInterviewTopologyFrozen:
    def test_interview_nodes_match_freeze(self) -> None:
        graph = build_interview_graph(
            llm=MagicMock(),
            longitudinal_repository=MagicMock(),
        )
        assert _business_nodes(graph) == FROZEN_INTERVIEW_NODES

    def test_interview_edges_match_freeze(self) -> None:
        graph = build_interview_graph(
            llm=MagicMock(),
            longitudinal_repository=MagicMock(),
        )
        assert _edges(graph) == FROZEN_INTERVIEW_EDGES

    def test_interview_conditional_routers_match_freeze(self) -> None:
        source = INTERVIEW_GRAPH_PATH.read_text(encoding="utf-8")
        assert _conditional_routers(source) == FROZEN_CONDITIONAL_ROUTERS

    def test_interview_nodes_align_with_production_inventory(self) -> None:
        assert FROZEN_INTERVIEW_NODES == PRODUCTION_GRAPH_NODES - {"replay"}


class TestReplayTopologyFrozen:
    def test_replay_nodes_and_edges_match_freeze(self) -> None:
        graph = build_replay_graph(session_loader=lambda _sid: None)
        assert _business_nodes(graph) == FROZEN_REPLAY_NODES
        assert _edges(graph) == FROZEN_REPLAY_EDGES


class TestNoEpic08OrchestrationDrift:
    def test_no_shutdown_modules_under_graph(self) -> None:
        names = {p.name for p in _py_files(GRAPH_ROOT)}
        assert "shutdown.py" not in names
        assert "drain.py" not in names

    def test_graph_and_domain_have_no_lifecycle_tokens(self) -> None:
        violators: list[str] = []
        for path in (*_py_files(GRAPH_ROOT), *_py_files(DOMAIN_ROOT)):
            text = path.read_text(encoding="utf-8")
            hits = sorted(token for token in _FORBIDDEN_LIFECYCLE_TOKENS if token in text)
            if hits:
                rel = path.relative_to(REPO_ROOT).as_posix()
                violators.append(f"{rel}: {', '.join(hits)}")
        assert violators == []
