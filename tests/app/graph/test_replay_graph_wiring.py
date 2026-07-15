# tests/app/graph/test_replay_graph_wiring.py
# EPIC-03 Phase 4b — Replay Graph wiring tests.
#
# Validates (per EPIC-03-IMPLEMENTATION-PLAN.md §6 Phase 4 gate):
# - Replay Graph is wired as replay_node → END.
# - LangGraph checkpointing is disabled.
# - build_replay_graph accepts session_loader via DI.
# - Replay Graph is topologically independent from the live session graph.
# - Invoking the compiled graph produces a ReplaySession in result.
# - replay_node is the only node in the Replay Graph.

from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

import pytest

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_graph_state import ReplayGraphState
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session_v13 import ReplaySessionV13
from domain.contracts.session_history.session_history import SessionHistory
from app.graph.replay_graph import build_replay_graph, _REPLAY_NODE_NAME

from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    FIXED_HISTORY_DT,
    make_interview_metadata,
    make_language_profile,
    make_question_timeline,
    make_session_history,
    make_transcript,
)
from domain.contracts.session_history.session_history import (
    ReplayMetadata,
    TranscriptEntry,
)
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
from domain.contracts.session_history.question_result_record import QuestionResultRecord


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_question_result(
    question_id: str = "q-001",
    question_index: int = 0,
) -> QuestionResultRecord:
    return QuestionResultRecord(
        question_id=question_id,
        question_index=question_index,
        question_type="written",
        area_label="Algorithms",
        question_prompt="Describe REST.",
        score=75.0,
        max_score=100.0,
        feedback="Good.",
        attempts=1,
    )


def _make_session_history_with_results(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
) -> SessionHistory:
    snapshot = make_knowledge_snapshot(session_id=session_id, candidate_id=candidate_id)
    return (
        SessionHistoryBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(0)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=session_id))
        .with_transcript([
            TranscriptEntry(
                question_index=0,
                question_id="q-001",
                question_prompt="Describe REST.",
                answer_content="REST is a style.",
                answer_attempt=1,
            )
        ])
        .with_question_timeline(make_question_timeline())
        .with_question_results([_make_question_result()])
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_HISTORY_DT)
        .build()
    )


def _loader_returns(sh: Optional[SessionHistory]):
    def _loader(sid: str) -> Optional[SessionHistory]:
        return sh
    return _loader


def _make_request(
    session_id: str = SESSION_ID,
    replay_mode: ReplayMode = ReplayMode.STANDARD,
    replay_level: ReplayLevel = ReplayLevel.PRESENTATION,
) -> ReplayRequest:
    return ReplayRequest(
        session_id=session_id,
        replay_mode=replay_mode,
        replay_level=replay_level,
    )


# ---------------------------------------------------------------------------
# Graph compilation
# ---------------------------------------------------------------------------

class TestReplayGraphCompilation:
    """build_replay_graph compiles without error."""

    def test_build_replay_graph_returns_compiled_graph(self) -> None:
        graph = build_replay_graph(session_loader=_loader_returns(None))
        assert graph is not None

    def test_build_replay_graph_accepts_session_loader_callable(self) -> None:
        loader = _loader_returns(None)
        graph = build_replay_graph(session_loader=loader)
        assert graph is not None

    def test_build_replay_graph_with_mock_loader(self) -> None:
        loader = MagicMock(return_value=None)
        graph = build_replay_graph(session_loader=loader)
        assert graph is not None


# ---------------------------------------------------------------------------
# Graph topology: replay_node → END
# ---------------------------------------------------------------------------

class TestReplayGraphTopology:
    """Replay Graph is wired as replay_node → END."""

    def test_replay_node_is_registered(self) -> None:
        graph = build_replay_graph(session_loader=_loader_returns(None))
        # LangGraph compiled graphs expose nodes via graph.nodes attribute.
        assert _REPLAY_NODE_NAME in graph.nodes

    def test_only_replay_node_is_registered(self) -> None:
        graph = build_replay_graph(session_loader=_loader_returns(None))
        # Only "replay" and the LangGraph internal "__start__" node should be present.
        node_names = set(graph.nodes.keys())
        expected = {_REPLAY_NODE_NAME, "__start__"}
        assert node_names == expected, (
            f"Unexpected nodes in Replay Graph: {node_names - expected}"
        )

    def test_replay_graph_is_invocable(self) -> None:
        sh = _make_session_history_with_results()
        graph = build_replay_graph(session_loader=_loader_returns(sh))
        state: ReplayGraphState = {"request": _make_request()}
        output = graph.invoke(state)
        assert output is not None

    def test_invoke_produces_result_key(self) -> None:
        sh = _make_session_history_with_results()
        graph = build_replay_graph(session_loader=_loader_returns(sh))
        state: ReplayGraphState = {"request": _make_request()}
        output = graph.invoke(state)
        assert "result" in output

    def test_invoke_result_is_replay_session_v13(self) -> None:
        sh = _make_session_history_with_results()
        graph = build_replay_graph(session_loader=_loader_returns(sh))
        state: ReplayGraphState = {"request": _make_request()}
        output = graph.invoke(state)
        assert isinstance(output["result"], ReplaySessionV13)

    def test_invoke_result_is_successful(self) -> None:
        sh = _make_session_history_with_results()
        graph = build_replay_graph(session_loader=_loader_returns(sh))
        state: ReplayGraphState = {"request": _make_request()}
        output = graph.invoke(state)
        assert output["result"].is_successful is True

    def test_invoke_with_missing_session_returns_failed_result(self) -> None:
        graph = build_replay_graph(session_loader=_loader_returns(None))
        state: ReplayGraphState = {"request": _make_request(session_id="missing")}
        output = graph.invoke(state)
        assert output["result"].is_successful is False

    def test_invoke_result_session_id_matches_request(self) -> None:
        sh = _make_session_history_with_results()
        graph = build_replay_graph(session_loader=_loader_returns(sh))
        state: ReplayGraphState = {"request": _make_request(session_id=SESSION_ID)}
        output = graph.invoke(state)
        assert output["result"].session_id == SESSION_ID

    def test_invoke_result_candidate_id_matches(self) -> None:
        sh = _make_session_history_with_results()
        graph = build_replay_graph(session_loader=_loader_returns(sh))
        state: ReplayGraphState = {"request": _make_request()}
        output = graph.invoke(state)
        assert output["result"].candidate_identity_id == CANDIDATE_ID


# ---------------------------------------------------------------------------
# Checkpointing disabled (Domain Contracts §8.2)
# ---------------------------------------------------------------------------

class TestReplayGraphCheckpointingDisabled:
    """LangGraph checkpointing is disabled on the Replay Graph."""

    def test_compiled_graph_has_no_checkpointer(self) -> None:
        graph = build_replay_graph(session_loader=_loader_returns(None))
        # When checkpointer=None is passed to compile(), the compiled graph's
        # checkpointer attribute should be None.
        checkpointer = getattr(graph, "checkpointer", None)
        assert checkpointer is None, (
            f"Replay Graph must have checkpointing disabled; got checkpointer={checkpointer!r}"
        )

    def test_invoke_without_config_does_not_raise(self) -> None:
        """Invoking without a thread_id config must not raise (no checkpoint needed)."""
        sh = _make_session_history_with_results()
        graph = build_replay_graph(session_loader=_loader_returns(sh))
        state: ReplayGraphState = {"request": _make_request()}
        # Must not raise even without config={"configurable": {"thread_id": ...}}
        output = graph.invoke(state)
        assert output is not None


# ---------------------------------------------------------------------------
# Topological independence from live session graph
# ---------------------------------------------------------------------------

class TestReplayGraphIsolation:
    """Replay Graph is topologically independent from the live session graph (I-R03)."""

    def test_replay_graph_does_not_import_interview_graph(self) -> None:
        import importlib
        import inspect
        import app.graph.replay_graph as rg_module
        source = inspect.getsource(rg_module)
        assert "interview_graph" not in source, (
            "replay_graph.py must not import or reference interview_graph"
        )

    def test_replay_graph_does_not_import_interview_state(self) -> None:
        import app.graph.replay_graph as rg_module
        # Check actual runtime namespace — not source text (comments may mention the name).
        assert not hasattr(rg_module, "InterviewState"), (
            "replay_graph.py must not import InterviewState into its namespace"
        )
        # Also verify no import statement for InterviewState (import lines only).
        import inspect
        source = inspect.getsource(rg_module)
        import_lines = [line for line in source.splitlines() if line.strip().startswith("import") or line.strip().startswith("from")]
        for line in import_lines:
            assert "InterviewState" not in line, (
                f"replay_graph.py must not import InterviewState; found: {line!r}"
            )

    def test_replay_graph_state_does_not_reference_interview_state(self) -> None:
        import inspect
        import domain.contracts.replay.replay_graph_state as rgs_module
        source = inspect.getsource(rgs_module)
        assert "InterviewState" not in source, (
            "ReplayGraphState must not reference InterviewState (I-R03)"
        )

    def test_build_replay_graph_is_independent_from_build_interview_graph(self) -> None:
        """build_replay_graph must not call build_interview_graph."""
        import inspect
        import app.graph.replay_graph as rg_module
        source = inspect.getsource(rg_module)
        assert "build_interview_graph" not in source

    def test_replay_graph_is_separate_compiled_object(self) -> None:
        """Replay Graph compile produces a separate object from the interview graph."""
        from app.graph.interview_graph import build_interview_graph
        from unittest.mock import MagicMock
        live_graph = build_interview_graph(llm=MagicMock())
        replay = build_replay_graph(session_loader=_loader_returns(None))
        assert live_graph is not replay


# ---------------------------------------------------------------------------
# Session loader DI: called with correct session_id
# ---------------------------------------------------------------------------

class TestReplayGraphSessionLoaderDI:
    """session_loader is correctly injected and called during graph invocation."""

    def test_loader_called_with_request_session_id(self) -> None:
        calls: list[str] = []
        sh = _make_session_history_with_results()

        def _loader(sid: str) -> Optional[SessionHistory]:
            calls.append(sid)
            return sh

        graph = build_replay_graph(session_loader=_loader)
        state: ReplayGraphState = {"request": _make_request(session_id=SESSION_ID)}
        graph.invoke(state)
        assert calls == [SESSION_ID]

    def test_loader_called_exactly_once_per_invocation(self) -> None:
        call_count = {"n": 0}
        sh = _make_session_history_with_results()

        def _loader(sid: str) -> Optional[SessionHistory]:
            call_count["n"] += 1
            return sh

        graph = build_replay_graph(session_loader=_loader)
        state: ReplayGraphState = {"request": _make_request()}
        graph.invoke(state)
        assert call_count["n"] == 1

    def test_different_loaders_produce_independent_graphs(self) -> None:
        sh1 = _make_session_history_with_results(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)
        loader1 = _loader_returns(sh1)
        loader2 = _loader_returns(None)

        g1 = build_replay_graph(session_loader=loader1)
        g2 = build_replay_graph(session_loader=loader2)

        req = _make_request(session_id=SESSION_ID)
        out1 = g1.invoke({"request": req})
        out2 = g2.invoke({"request": req})

        assert out1["result"].is_successful is True
        assert out2["result"].is_successful is False
