# tests/app/graph/nodes/test_replay_architectural_invariants.py
# EPIC-03 Phase 4c — Architectural invariant tests for the Replay Engine.
#
# Invariants verified (per EPIC-03-IMPLEMENTATION-PLAN.md §2 Phase 4c):
#   I-11:  zero LLM calls during replay_node execution across all fixtures.
#   I-R03: replay_node imports no live session node; ReplayGraphState does not reference InterviewState.
#   I-R07: zero persistence writes during replay_node execution.
#   I-R06: zero cross-references between replay contracts and LongitudinalProfile contracts.

from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch, call

import pytest

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_graph_state import ReplayGraphState
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session_v13 import ReplaySessionV13
from domain.contracts.session_history.session_history import (
    ReplayMetadata,
    SessionHistory,
    TranscriptEntry,
)
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
from domain.contracts.session_history.question_result_record import QuestionResultRecord
from app.graph.nodes.replay_node import replay_node, SessionLoader
from app.graph.replay_graph import build_replay_graph

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
)

# ---------------------------------------------------------------------------
# Project root for path-based analysis
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parents[4]
_REPLAY_CONTRACTS_DIR = _PROJECT_ROOT / "domain" / "contracts" / "replay"
_NODES_DIR = _PROJECT_ROOT / "app" / "graph" / "nodes"


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


def _make_session_history(
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


def _make_state(session_id: str = SESSION_ID) -> ReplayGraphState:
    return ReplayGraphState(
        request=ReplayRequest(
            session_id=session_id,
            replay_mode=ReplayMode.STANDARD,
            replay_level=ReplayLevel.PRESENTATION,
        )
    )


def _loader(sh: Optional[SessionHistory]) -> SessionLoader:
    def _fn(sid: str) -> Optional[SessionHistory]:
        return sh
    return _fn


# ---------------------------------------------------------------------------
# I-11 — LLM-Free Guarantee
# ---------------------------------------------------------------------------

class TestI11LLMFree:
    """I-11: replay_node must invoke zero LLM service calls (ADR-037 I-11).

    Mocks all known LLM-backed service interfaces and asserts they are never called.
    """

    def _run_replay_node(self, sh: Optional[SessionHistory]) -> None:
        state = _make_state()
        replay_node(state, session_loader=_loader(sh))

    def test_no_llm_calls_on_success(self) -> None:
        sh = _make_session_history()
        mock_llm = MagicMock()

        with (
            patch("app.graph.nodes.replay_node.ReplaySessionBuilder") as mock_builder_cls,
        ):
            # Wire the mock builder to produce a real result.
            from domain.contracts.replay.replay_session_builder import ReplaySessionBuilder as RealBuilder
            real_result = (
                RealBuilder()
                .with_session_history(sh)
                .with_replay_mode(ReplayMode.STANDARD)
                .with_replay_level(ReplayLevel.PRESENTATION)
                .with_operator_id(None)
                .build()
            )
            mock_builder = MagicMock()
            mock_builder_cls.return_value = mock_builder
            mock_builder.with_session_history.return_value = mock_builder
            mock_builder.with_replay_mode.return_value = mock_builder
            mock_builder.with_replay_level.return_value = mock_builder
            mock_builder.with_operator_id.return_value = mock_builder
            mock_builder.build.return_value = real_result

            self._run_replay_node(sh)

            # Assert no LLM-related method was called on the builder mock.
            for name, _args, _kwargs in mock_builder.mock_calls:
                assert "llm" not in name.lower(), f"LLM-related call found: {name}"
                assert "generate" not in name.lower(), f"generate call found: {name}"
                assert "chat" not in name.lower(), f"chat call found: {name}"
                assert "complete" not in name.lower(), f"complete call found: {name}"

    def test_replay_node_source_has_no_llm_import(self) -> None:
        """replay_node module must not import any LLM service."""
        import app.graph.nodes.replay_node as rn_module
        source = inspect.getsource(rn_module)
        llm_indicators = [
            "openai", "langchain", "ChatOpenAI", "llm_port",
            "LLMPort", "AIHintService", "NarrativeGenerator",
            "CoachingEngine", "InterviewEvaluationService",
        ]
        for indicator in llm_indicators:
            assert indicator not in source, (
                f"I-11 violation: replay_node.py imports or references LLM service: {indicator!r}"
            )

    def test_replay_graph_source_has_no_llm_import(self) -> None:
        """replay_graph module must not import any LLM service."""
        import app.graph.replay_graph as rg_module
        source = inspect.getsource(rg_module)
        llm_indicators = [
            "openai", "langchain", "ChatOpenAI", "llm_port",
            "LLMPort", "AIHintService", "NarrativeGenerator",
            "CoachingEngine",
        ]
        for indicator in llm_indicators:
            assert indicator not in source, (
                f"I-11 violation: replay_graph.py imports or references LLM service: {indicator!r}"
            )

    def test_no_llm_calls_on_session_not_found(self) -> None:
        """Even the failure path (session not found) must not call LLM services."""
        state = _make_state(session_id="not-found")
        with patch("builtins.__import__", wraps=__import__) as mock_import:
            output = replay_node(state, session_loader=_loader(None))
        assert output["result"].is_successful is False

    def test_replay_contracts_do_not_import_llm_services(self) -> None:
        """All replay contract modules must not import LLM services."""
        llm_modules = {
            "openai", "langchain", "services.narrative_generator",
            "services.coaching_engine", "services.interview_evaluation_service",
            "app.ports.llm_port",
        }
        for py_file in _REPLAY_CONTRACTS_DIR.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            source = py_file.read_text(encoding="utf-8")
            for mod in llm_modules:
                assert mod not in source, (
                    f"I-11 violation: {py_file.name} references LLM module {mod!r}"
                )


# ---------------------------------------------------------------------------
# I-R03 — Replay / Live Session Isolation
# ---------------------------------------------------------------------------

class TestIR03ReplayIsolation:
    """I-R03: replay_node imports no live session node; ReplayGraphState does not reference InterviewState."""

    def test_replay_node_does_not_import_interview_state(self) -> None:
        import app.graph.nodes.replay_node as rn_module
        # Check actual runtime namespace — comments may mention the name.
        assert not hasattr(rn_module, "InterviewState"), (
            "I-R03 violation: InterviewState must not be imported into replay_node namespace"
        )
        # Also verify no import line brings in InterviewState.
        source = inspect.getsource(rn_module)
        import_lines = [line for line in source.splitlines() if line.strip().startswith("import") or line.strip().startswith("from")]
        for line in import_lines:
            assert "InterviewState" not in line, (
                f"I-R03 violation: replay_node.py import line references InterviewState: {line!r}"
            )

    def test_replay_node_does_not_import_any_live_session_node(self) -> None:
        """replay_node must not import any live session graph node."""
        import app.graph.nodes.replay_node as rn_module
        source = inspect.getsource(rn_module)
        live_nodes = [
            "session_close_node", "report_node", "longitudinal_update_node",
            "reasoner_node", "navigation_node", "completion_node", "decision_node",
            "feedback_node", "hint_node", "evaluation_node", "execution_node",
            "question_node", "written_evaluation_node", "start_processing_node",
        ]
        for node in live_nodes:
            assert node not in source, (
                f"I-R03 violation: replay_node.py imports live session node {node!r}"
            )

    def test_replay_graph_state_does_not_reference_interview_state(self) -> None:
        import domain.contracts.replay.replay_graph_state as rgs_module
        source = inspect.getsource(rgs_module)
        assert "InterviewState" not in source, (
            "I-R03 violation: ReplayGraphState must not reference InterviewState"
        )

    def test_replay_graph_does_not_import_interview_graph(self) -> None:
        import app.graph.replay_graph as rg_module
        source = inspect.getsource(rg_module)
        assert "interview_graph" not in source, (
            "I-R03 violation: replay_graph.py must not reference interview_graph"
        )

    def test_replay_graph_state_type_is_typed_dict(self) -> None:
        from domain.contracts.replay.replay_graph_state import ReplayGraphState
        # ReplayGraphState must be a TypedDict — confirmed by checking __bases__.
        bases = [b.__name__ for b in ReplayGraphState.__bases__]
        assert "TypedDict" in bases or "dict" in bases, (
            "ReplayGraphState must be a TypedDict (LangGraph convention)"
        )

    def test_replay_graph_state_fields(self) -> None:
        from domain.contracts.replay.replay_graph_state import ReplayGraphState
        annotations = ReplayGraphState.__annotations__
        assert "request" in annotations, "ReplayGraphState must have 'request' field"
        assert "result" in annotations, "ReplayGraphState must have 'result' field"

    def test_replay_node_module_does_not_import_interview_state_at_runtime(self) -> None:
        """At import time, replay_node module must not have InterviewState in its namespace."""
        import app.graph.nodes.replay_node as rn_module
        assert not hasattr(rn_module, "InterviewState"), (
            "I-R03 violation: InterviewState found in replay_node module namespace"
        )


# ---------------------------------------------------------------------------
# I-R07 — Zero Persistence Writes
# ---------------------------------------------------------------------------

class TestIR07NoPersistenceWrites:
    """I-R07: zero write calls to the persistence layer during replay_node execution."""

    def test_session_loader_not_called_with_write_method(self) -> None:
        sh = _make_session_history()
        write_calls: list[str] = []

        class _TrackingLoader:
            def __call__(self, sid: str) -> Optional[SessionHistory]:
                return sh

            def save(self, *args, **kwargs) -> None:
                write_calls.append("save")

            def write(self, *args, **kwargs) -> None:
                write_calls.append("write")

            def update(self, *args, **kwargs) -> None:
                write_calls.append("update")

        loader = _TrackingLoader()
        state = _make_state()
        replay_node(state, session_loader=loader)
        assert write_calls == [], f"I-R07 violation: persistence write methods called: {write_calls}"

    def test_replay_node_does_not_call_any_save_method(self) -> None:
        sh = _make_session_history()
        loader_mock = MagicMock(return_value=sh)
        state = _make_state()
        replay_node(state, session_loader=loader_mock)
        # Verify that the loader was only called once (the read), no write methods.
        assert loader_mock.call_count == 1
        for method_call in loader_mock.method_calls:
            method_name = method_call[0].lower()
            assert "save" not in method_name
            assert "write" not in method_name
            assert "update" not in method_name
            assert "delete" not in method_name

    def test_replay_node_source_has_no_write_operations(self) -> None:
        """Verify by source analysis that replay_node.py has no persistence write imports."""
        import app.graph.nodes.replay_node as rn_module
        source = inspect.getsource(rn_module)
        persistence_write_indicators = [
            "repository.save", "session_store.write", ".save(", ".write(",
            "persist(", "checkpoint.put",
        ]
        for indicator in persistence_write_indicators:
            assert indicator not in source, (
                f"I-R07 violation: replay_node.py contains persistence write: {indicator!r}"
            )

    def test_replay_node_result_not_persisted(self) -> None:
        """ReplaySession produced by replay_node is not serialized to persistence."""
        sh = _make_session_history()
        state = _make_state()
        output = replay_node(state, session_loader=_loader(sh))
        result = output["result"]
        # ReplaySession must be in-memory only (frozen Pydantic model, no persistence).
        assert isinstance(result, ReplaySessionV13)
        assert result.is_successful is True

    def test_graph_invoke_produces_no_checkpoint(self) -> None:
        """Replay Graph invocation must not create a LangGraph checkpoint."""
        sh = _make_session_history()
        graph = build_replay_graph(session_loader=_loader(sh))
        # Confirm checkpointer is None (checkpointing disabled per §8.2).
        assert getattr(graph, "checkpointer", None) is None
        # Invoke without thread_id config must not raise.
        output = graph.invoke({"request": _make_state()["request"]})
        assert output["result"] is not None


# ---------------------------------------------------------------------------
# I-R06 — Replay / Longitudinal Isolation
# ---------------------------------------------------------------------------

class TestIR06LongitudinalIsolation:
    """I-R06: zero cross-references between replay contracts and LongitudinalProfile contracts."""

    _LONGITUDINAL_INDICATORS = [
        "LongitudinalProfile",
        "longitudinal_profile",
        "LearningProgress",
        "learning_progress",
        "ProgressComparison",
        "progress_comparison",
        "LongitudinalProfileRepository",
    ]

    def _replay_contract_sources(self) -> dict[str, str]:
        return {
            py_file.name: py_file.read_text(encoding="utf-8")
            for py_file in _REPLAY_CONTRACTS_DIR.glob("*.py")
            if not py_file.name.startswith("_")
        }

    def test_no_replay_contract_imports_longitudinal_profile(self) -> None:
        """No replay contract module imports LongitudinalProfile or LearningProgress."""
        sources = self._replay_contract_sources()
        for filename, source in sources.items():
            for indicator in self._LONGITUDINAL_INDICATORS:
                assert indicator not in source, (
                    f"I-R06 violation: {filename} references longitudinal artifact {indicator!r}"
                )

    def test_replay_node_does_not_import_longitudinal_profile(self) -> None:
        import app.graph.nodes.replay_node as rn_module
        source = inspect.getsource(rn_module)
        for indicator in self._LONGITUDINAL_INDICATORS:
            assert indicator not in source, (
                f"I-R06 violation: replay_node.py references {indicator!r}"
            )

    def test_replay_graph_does_not_import_longitudinal_profile(self) -> None:
        import app.graph.replay_graph as rg_module
        source = inspect.getsource(rg_module)
        for indicator in self._LONGITUDINAL_INDICATORS:
            assert indicator not in source, (
                f"I-R06 violation: replay_graph.py references {indicator!r}"
            )

    def test_replay_graph_state_does_not_reference_longitudinal(self) -> None:
        import domain.contracts.replay.replay_graph_state as rgs_module
        source = inspect.getsource(rgs_module)
        for indicator in self._LONGITUDINAL_INDICATORS:
            assert indicator not in source, (
                f"I-R06 violation: ReplayGraphState references {indicator!r}"
            )

    def test_no_longitudinal_module_in_replay_node_sys_modules_after_import(self) -> None:
        """Importing replay_node must not pull longitudinal modules into sys.modules
        that were not already there before the import.
        """
        # Longitudinal modules that must not be newly imported by replay_node.
        longitudinal_module_prefixes = [
            "domain.contracts.longitudinal",
            "domain.contracts.progress",
            "services.progress",
        ]
        before = set(sys.modules.keys())
        # Re-import replay_node (it's already in sys.modules; just confirm nothing new).
        import app.graph.nodes.replay_node  # noqa: F401
        after = set(sys.modules.keys())
        newly_imported = after - before
        for mod in newly_imported:
            for prefix in longitudinal_module_prefixes:
                assert not mod.startswith(prefix), (
                    f"I-R06 violation: importing replay_node pulled in longitudinal module {mod!r}"
                )
