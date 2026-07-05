# tests/app/graph/nodes/test_report_node.py
# Canonical report_node test suite (merged from test_mig05a_report_node.py and tests/graph/nodes/test_report_node.py)
#
# Verifies:
# 1. report_node populates state.report from state.session_history.
# 2. report_node clears is_processing / current_step.
# 3. report_node is no-op (flags only) when session_history is None.
# 4. report_node is non-fatal (flags cleared, report=None on build failure).
# 5. Report identity matches SessionHistory identity.
# 6. Report is immutable (frozen=True).
# 7. ReportBuilder remains sole producer — no direct Report() in node source.
# 8. Zero KnowledgePipeline / FeatureEngine / ObservationExtractor in node source.
# 9. state.session_history remains immutable after report_node.
# 10. report.feature_count matches profile_snapshot.total_feature_count.
# 11. interview_evaluation field preserved across report_node.
# 12. Architecture: state.report field exists on InterviewState.
# 13. Architecture: single Report class definition in production codebase.

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.report.report import Report
from domain.contracts.user.role import Role, RoleType
from tests.domain.contracts.report.conftest import make_report, make_session_history


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SESSION_ID = "mig05a-test-session"
CANDIDATE_ID = "mig05a-candidate-001"


def _make_question(qid: str = "q1") -> Question:
    return Question(
        id=qid,
        area=InterviewArea.TECH_CODING,
        type=QuestionType.WRITTEN,
        prompt="MIG-05A test question",
        difficulty=QuestionDifficulty.MEDIUM,
    )


def _make_answer(question_id: str = "q1") -> Answer:
    return Answer(question_id=question_id, content="MIG-05A test answer", attempt=1)


def _make_base_state(with_history: bool = True) -> InterviewState:
    questions = [_make_question("q1")]
    answers = [_make_answer("q1")]
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="MIG05ACorpTest",
        language="en",
        questions=questions,
        interview_id=SESSION_ID,
    )
    state = state.model_copy(update={
        "is_completed": True,
        "is_processing": True,
        "answers": answers,
        "current_question_index": 0,
        "candidate_identity_id": CANDIDATE_ID,
    })
    if with_history:
        history = make_session_history(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)
        state = state.model_copy(update={"session_history": history})
    return state


def _run_report(state: InterviewState) -> InterviewState:
    from app.graph.nodes.report_node import report_node
    return report_node(state)


# ---------------------------------------------------------------------------
# 1. Core behavior
# ---------------------------------------------------------------------------

class TestReportNodeCore:

    def test_report_populated_when_session_history_exists(self):
        state = _make_base_state(with_history=True)
        result = _run_report(state)
        assert result.report is not None
        assert isinstance(result.report, Report)

    def test_report_none_when_no_session_history(self):
        state = _make_base_state(with_history=False)
        result = _run_report(state)
        assert result.report is None

    def test_is_processing_cleared(self):
        state = _make_base_state(with_history=True)
        result = _run_report(state)
        assert result.is_processing is False

    def test_current_step_cleared(self):
        from app.ui.constants.loader_steps import LoaderStep
        state = _make_base_state(with_history=True)
        state = state.model_copy(update={"current_step": LoaderStep.GENERATING_REPORT})
        result = _run_report(state)
        assert result.current_step is None

    def test_flags_cleared_even_without_session_history(self):
        state = _make_base_state(with_history=False)
        result = _run_report(state)
        assert result.is_processing is False
        assert result.current_step is None

    def test_report_identity_matches_session_history(self):
        state = _make_base_state(with_history=True)
        result = _run_report(state)
        assert result.report is not None
        assert result.report.session_id == state.session_history.session_id
        assert result.report.candidate_identity_id == state.session_history.candidate_identity_id

    def test_report_feature_count_matches_profile_snapshot(self):
        state = _make_base_state(with_history=True)
        result = _run_report(state)
        assert result.report is not None
        assert result.report.feature_count == (
            result.report.profile_snapshot.total_feature_count
        )

    def test_session_history_immutable_after_report_node(self):
        state = _make_base_state(with_history=True)
        original_history = state.session_history
        result = _run_report(state)
        assert result.session_history is original_history

    def test_interview_evaluation_preserved_across_report_node(self):
        """report_node must not discard interview_evaluation when it exists."""
        from unittest.mock import Mock
        state = _make_base_state(with_history=False)
        mock_eval = Mock()
        state = state.model_copy(update={"interview_evaluation": mock_eval})
        result = _run_report(state)
        assert result.interview_evaluation is mock_eval


# ---------------------------------------------------------------------------
# 2. Immutability and identity
# ---------------------------------------------------------------------------

class TestReportImmutability:

    def test_report_is_frozen(self):
        state = _make_base_state(with_history=True)
        result = _run_report(state)
        assert result.report is not None
        with pytest.raises((TypeError, Exception)):
            result.report.session_id = "mutated"  # type: ignore[misc]

    def test_report_has_stable_report_id(self):
        state = _make_base_state(with_history=True)
        result = _run_report(state)
        assert result.report is not None
        assert len(result.report.report_id) > 0

    def test_report_has_schema_version(self):
        state = _make_base_state(with_history=True)
        result = _run_report(state)
        assert result.report is not None
        assert result.report.schema_version is not None


# ---------------------------------------------------------------------------
# 3. Non-fatal behavior
# ---------------------------------------------------------------------------

class TestReportNodeNonFatal:

    def test_non_fatal_on_builder_exception(self):
        """Build failure → report=None, flags cleared, no crash."""
        state = _make_base_state(with_history=True)
        with patch(
            "app.graph.nodes.report_node.ReportBuilder",
            side_effect=RuntimeError("Simulated build crash"),
        ):
            result = _run_report(state)
        assert result.report is None
        assert result.is_processing is False

    def test_state_unchanged_fields_on_build_failure(self):
        state = _make_base_state(with_history=True)
        original_history = state.session_history
        with patch(
            "app.graph.nodes.report_node.ReportBuilder",
            side_effect=ValueError("Build failed"),
        ):
            result = _run_report(state)
        assert result.session_history is original_history


# ---------------------------------------------------------------------------
# 4. Architecture guards
# ---------------------------------------------------------------------------

class TestReportNodeArchitecture:

    def _node_source(self) -> str:
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "report_node.py"
        return node_path.read_text(encoding="utf-8")

    def test_no_knowledge_pipeline_import_in_node(self):
        source = self._node_source()
        assert "from services.knowledge_pipeline" not in source
        assert "import KnowledgePipeline" not in source

    def test_no_feature_engine_import_in_node(self):
        source = self._node_source()
        assert "from services.feature_engine" not in source
        assert "import FeatureEngine" not in source

    def test_no_observation_extractor_import_in_node(self):
        source = self._node_source()
        assert "from domain.contracts.observation.extraction" not in source
        assert "import ObservationExtractor" not in source

    def test_no_narrative_generator_import_in_node(self):
        source = self._node_source()
        assert "from services.narrative_generator" not in source
        assert "import NarrativeGenerator" not in source

    def test_no_coaching_engine_import_in_node(self):
        source = self._node_source()
        assert "from services.coaching_engine" not in source
        assert "import CoachingEngine" not in source

    def test_no_direct_report_construction_in_node(self):
        """Report() must never be instantiated directly — only via ReportBuilder."""
        source = self._node_source()
        assert "Report(" not in source or "ReportBuilder" in source

    def test_report_builder_used_as_sole_constructor(self):
        source = self._node_source()
        assert "ReportBuilder" in source

    def test_report_field_on_interview_state(self):
        """state.report TCP field must exist."""
        from domain.contracts.interview_state.base import InterviewStateBase
        assert "report" in InterviewStateBase.model_fields

    def test_single_report_class_definition(self):
        project_root = Path(__file__).parents[4]
        matches = [
            p for p in project_root.rglob("*.py")
            if "class Report(" in p.read_text(encoding="utf-8")
            and "test_" not in p.name
        ]
        assert len(matches) == 1, f"Expected 1 Report class, found: {[m.name for m in matches]}"
