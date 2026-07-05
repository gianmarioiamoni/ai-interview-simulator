# tests/app/graph/nodes/test_session_close_node.py
# session_close_node architectural and runtime tests
#
# Verifies:
# 1. session_close_node writes state.session_history when is_completed=True.
# 2. session_history is a valid SessionHistory instance.
# 3. session_history.candidate_identity_id matches state.candidate_identity_id.
# 4. session_history.session_id matches state.interview_id.
# 5. SessionClosePipeline is invoked exactly once per node call.
# 6. session_history is None on pipeline failure (non-fatal).
# 7. No second writer to session_history — architectural guard.
# 8. No double-close: calling node twice on a completed state produces consistent history.
# 9. PAT-06: only one orchestrator — no graph is created inside the node.
# 10. CandidateProfile uniqueness: only one CandidateProfile definition in runtime.

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.session_history.session_history import SessionHistory
from domain.contracts.user.role import Role, RoleType
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.answer import Answer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_question(qid: str = "q1", qtype: QuestionType = QuestionType.WRITTEN) -> Question:
    return Question(
        id=qid,
        area=InterviewArea.TECH_CODING,
        type=qtype,
        prompt="Describe REST principles.",
        difficulty=QuestionDifficulty.MEDIUM,
    )


def _make_answer(question_id: str = "q1") -> Answer:
    return Answer(question_id=question_id, content="REST stands for...", attempt=1)


def _make_completed_state(
    interview_id: str = "sess-mig04-001",
    candidate_identity_id: str | None = "cand-mig04-uuid-001",
    n_questions: int = 1,
) -> InterviewState:
    questions = [_make_question(f"q{i}") for i in range(n_questions)]
    answers = [_make_answer(f"q{i}") for i in range(n_questions)]
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="ACME",
        language="en",
        questions=questions,
        interview_id=interview_id,
    )
    state = state.model_copy(update={
        "is_completed": True,
        "answers": answers,
        "current_question_index": max(n_questions - 1, 0),
    })
    if candidate_identity_id is not None:
        state = state.model_copy(update={"candidate_identity_id": candidate_identity_id})
    return state


def _run_node(state: InterviewState) -> InterviewState:
    from app.graph.nodes.session_close_node import session_close_node
    return session_close_node(state)


# ---------------------------------------------------------------------------
# 1. Core runtime behavior
# ---------------------------------------------------------------------------

class TestSessionCloseNodeCore:

    def test_session_history_is_set_after_node(self):
        state = _make_completed_state()
        result = _run_node(state)
        assert result.session_history is not None

    def test_session_history_is_session_history_instance(self):
        state = _make_completed_state()
        result = _run_node(state)
        assert isinstance(result.session_history, SessionHistory)

    def test_session_history_session_id_matches_interview_id(self):
        state = _make_completed_state(interview_id="sess-abc-001")
        result = _run_node(state)
        assert result.session_history is not None
        assert result.session_history.session_id == "sess-abc-001"

    def test_session_history_candidate_id_matches_state(self):
        state = _make_completed_state(candidate_identity_id="cand-explicit-001")
        result = _run_node(state)
        assert result.session_history is not None
        assert result.session_history.candidate_identity_id == "cand-explicit-001"

    def test_session_history_candidate_id_fallback_to_interview_id(self):
        state = _make_completed_state()
        state = state.model_copy(update={"candidate_identity_id": None})
        result = _run_node(state)
        assert result.session_history is not None
        assert result.session_history.candidate_identity_id == state.interview_id

    def test_knowledge_snapshot_present(self):
        state = _make_completed_state()
        result = _run_node(state)
        assert result.session_history is not None
        assert result.session_history.knowledge_snapshot is not None

    def test_all_other_state_fields_unchanged(self):
        state = _make_completed_state()
        result = _run_node(state)
        assert result.interview_id == state.interview_id
        assert result.is_completed == state.is_completed
        assert result.candidate_identity_id == state.candidate_identity_id
        assert result.observation_store == state.observation_store
        assert result.candidate_profile_v2 == state.candidate_profile_v2

    def test_interview_metadata_role_present(self):
        state = _make_completed_state()
        result = _run_node(state)
        assert result.session_history is not None
        meta = result.session_history.interview_metadata
        assert len(meta.role) > 0

    def test_language_profile_present(self):
        state = _make_completed_state()
        result = _run_node(state)
        assert result.session_history is not None
        assert result.session_history.language_profile is not None


# ---------------------------------------------------------------------------
# 2. Non-fatal failure behavior
# ---------------------------------------------------------------------------

class TestSessionCloseNodeNonFatal:

    def test_pipeline_failure_returns_state_without_history(self):
        state = _make_completed_state()
        with patch(
            "app.graph.nodes.session_close_node._pipeline"
        ) as mock_pipeline:
            mock_result = MagicMock()
            mock_result.is_successful = False
            mock_result.failure_reason = "Simulated pipeline failure"
            mock_pipeline.run.return_value = mock_result
            result = _run_node(state)

        assert result.session_history is None

    def test_exception_returns_state_unchanged(self):
        state = _make_completed_state()
        with patch(
            "app.graph.nodes.session_close_node._pipeline"
        ) as mock_pipeline:
            mock_pipeline.run.side_effect = RuntimeError("Simulated crash")
            result = _run_node(state)

        assert result.session_history is None
        assert result.interview_id == state.interview_id


# ---------------------------------------------------------------------------
# 3. Single invocation guard (no double-close)
# ---------------------------------------------------------------------------

class TestSingleInvocationGuard:

    def test_session_history_consistent_across_two_calls(self):
        state = _make_completed_state()
        result1 = _run_node(state)
        result2 = _run_node(state)
        assert result1.session_history is not None
        assert result2.session_history is not None
        assert result1.session_history.session_id == result2.session_history.session_id
        assert result1.session_history.candidate_identity_id == result2.session_history.candidate_identity_id

    def test_pipeline_called_exactly_once_per_node_invocation(self):
        state = _make_completed_state()
        with patch(
            "app.graph.nodes.session_close_node._pipeline"
        ) as mock_pipeline:
            mock_result = MagicMock()
            mock_result.is_successful = True
            mock_result.session_history = MagicMock(spec=SessionHistory)
            mock_pipeline.run.return_value = mock_result
            _run_node(state)
            mock_pipeline.run.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Architectural guards — no second writer, no second orchestrator
# ---------------------------------------------------------------------------

class TestArchitecturalGuards:

    def _all_node_sources(self) -> list[Path]:
        # app/graph/nodes/ (project root is parents[4] from test file location)
        nodes_dir = Path(__file__).parents[4] / "app" / "graph" / "nodes"
        return [p for p in nodes_dir.glob("*.py") if not p.name.startswith("test_")]

    def test_no_other_node_writes_session_history(self):
        """Only session_close_node may write session_history.
        report_node reads session_history (MIG-05A) but never writes it.
        """
        permitted_readers = {"session_close_node.py", "report_node.py"}
        for path in self._all_node_sources():
            if path.name in permitted_readers:
                continue
            source = path.read_text(encoding="utf-8")
            assert "session_history" not in source, (
                f"{path.name} must not reference session_history (single-writer invariant)"
            )

    def test_no_other_node_imports_session_close_pipeline(self):
        """SessionClosePipeline is imported only by session_close_node."""
        for path in self._all_node_sources():
            if path.name == "session_close_node.py":
                continue
            source = path.read_text(encoding="utf-8")
            assert "SessionClosePipeline" not in source, (
                f"{path.name} must not import SessionClosePipeline"
            )

    def test_no_other_node_imports_knowledge_snapshot_builder(self):
        """KnowledgeSnapshotBuilder is used only in session_close_node."""
        for path in self._all_node_sources():
            if path.name == "session_close_node.py":
                continue
            source = path.read_text(encoding="utf-8")
            assert "KnowledgeSnapshotBuilder" not in source, (
                f"{path.name} must not use KnowledgeSnapshotBuilder"
            )

    def test_session_close_node_does_not_create_graph(self):
        """session_close_node must not create a StateGraph or sub-graph (PAT-06)."""
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        source = node_path.read_text(encoding="utf-8")
        assert "StateGraph" not in source
        assert "langgraph" not in source

    def test_session_close_node_does_not_call_knowledge_pipeline(self):
        """session_close_node must not invoke KnowledgePipeline (no double extraction)."""
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        source = node_path.read_text(encoding="utf-8")
        assert "KnowledgePipeline(" not in source
        assert "knowledge_pipeline.run" not in source.lower().replace("_", "")


# ---------------------------------------------------------------------------
# 5. Graph routing guard — session_close inserted between evaluation_aggregate and report
# ---------------------------------------------------------------------------

class TestGraphRouting:

    def _graph_source(self) -> str:
        graph_path = Path(__file__).parents[4] / "app" / "graph" / "interview_graph.py"
        return graph_path.read_text(encoding="utf-8")

    def test_session_close_in_graph(self):
        assert "session_close" in self._graph_source()

    def test_session_close_before_report(self):
        source = self._graph_source()
        sc_idx = source.index("session_close")
        report_idx = source.index('"report"')
        assert sc_idx < report_idx

    def test_route_after_completion_targets_session_close(self):
        source = self._graph_source()
        assert '"session_close"' in source
        assert '"report": "report"' not in source.split("route_after_completion")[1].split("add_edge")[0]


# ---------------------------------------------------------------------------
# 6. CandidateProfile uniqueness
# ---------------------------------------------------------------------------

class TestCandidateProfileUniqueness:

    def test_single_candidate_profile_definition(self):
        """Only one CandidateProfile class must exist in domain/contracts/reasoning."""
        reasoning_dir = (
            Path(__file__).parents[4] / "domain" / "contracts" / "reasoning"
        )
        files_with_class = [
            p for p in reasoning_dir.rglob("*.py")
            if "class CandidateProfile" in p.read_text(encoding="utf-8")
        ]
        assert len(files_with_class) == 1, (
            f"Expected exactly one CandidateProfile definition, found: {[f.name for f in files_with_class]}"
        )

    def test_session_close_node_imports_from_correct_candidate_profile(self):
        """session_close_node must not import CandidateProfile directly."""
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        source = node_path.read_text(encoding="utf-8")
        # Node uses CandidateProfileSnapshot not CandidateProfile (distinct contract)
        assert "from domain.contracts.reasoning.candidate_profile import CandidateProfile" not in source


# ---------------------------------------------------------------------------
# 7. PAT validation guards
# ---------------------------------------------------------------------------

class TestPatValidation:

    def test_pat04_session_history_tcp_is_nullable(self):
        """PAT-04: session_history must default to None (TCP field)."""
        from domain.contracts.interview_state.base import InterviewStateBase
        field = InterviewStateBase.model_fields["session_history"]
        assert field.default is None

    def _node_source(self) -> str:
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        return node_path.read_text(encoding="utf-8")

    def test_pat06_no_sub_graph_in_node(self):
        source = self._node_source()
        assert "StateGraph" not in source
        assert "compile()" not in source

    def test_pat05_builder_only_knowledge_snapshot(self):
        """KnowledgeSnapshot is only created via KnowledgeSnapshotBuilder."""
        source = self._node_source()
        assert "KnowledgeSnapshotBuilder" in source
        assert "KnowledgeSnapshot(" not in source

    def test_pat05_builder_only_session_history(self):
        """SessionHistory is only created via SessionHistoryBuilder (inside pipeline)."""
        source = self._node_source()
        assert "SessionHistory(" not in source
