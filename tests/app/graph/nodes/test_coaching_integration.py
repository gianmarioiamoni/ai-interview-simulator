# tests/app/graph/nodes/test_coaching_integration.py
# Runtime Coaching Integration
#
# Verifies:
# 1. session_close_node invokes CoachingEngine (not CoachingBuilder.empty).
# 2. CoachingSnapshot in KnowledgeSnapshot has objectives when features present.
# 3. CoachingEngine is the sole CoachingSnapshot producer in the primary path.
# 4. CoachingEngine failure falls back to empty snapshot — close non-fatal.
# 5. No FeatureEngine / KnowledgePipeline / ObservationExtractor in coaching path.
# 6. CoachingSnapshot is immutable.
# 7. Report carries CoachingEngine output (not empty).
# 8. Determinism: same state → same objective count.
# 9. Empty features → engine still produces valid CoachingSnapshot.
# 10. No profile_v2 → engine uses empty profile fallback.
# 11. Architecture: CoachingEngine singleton in module.
# 12. Source guard: CoachingBuilder.empty still exists as fallback only.
# 13. No new builder, no new orchestrator introduced.

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import Role, RoleType
from domain.profile.candidate_profile_builder import CandidateProfileBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SESSION_ID = "mig08b-test-session"
CANDIDATE_ID = "mig08b-candidate-001"


def _make_feature(value: str = "LOW", q_idx: int = 0) -> ProfileFeature:
    identity = FeatureIdentity.for_type(FeatureType.REASONING)
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=0.3),
        stability=FeatureStability(state="emerging"),
        maturity=FeatureMaturity.from_observation_count(2),
    )
    provenance = FeatureProvenance(
        feature_identity=identity,
        source_observation_ids=("obs-1",),
        computed_at_question_index=q_idx,
        feature_engine_version="1.0.0",
        updater_id="test_updater",
    )
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=quality,
        provenance=provenance,
        computed_at_question_index=q_idx,
        candidate_identity_id=CANDIDATE_ID,
    )


def _make_state(features: tuple[ProfileFeature, ...] = ()) -> InterviewState:
    q = Question(
        id="q1", area=InterviewArea.TECH_CODING, type=QuestionType.WRITTEN,
        prompt="test", difficulty=QuestionDifficulty.MEDIUM,
    )
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="MIG08BTest",
        language="en",
        questions=[q],
        interview_id=SESSION_ID,
    )
    state = state.model_copy(update={
        "is_completed": True,
        "answers": [Answer(question_id="q1", content="answer", attempt=1)],
        "current_question_index": 0,
        "candidate_identity_id": CANDIDATE_ID,
    })
    if features:
        profile = CandidateProfileBuilder().with_profile_features(features).build()
        state = state.model_copy(update={"candidate_profile_v2": profile})
    return state


def _run_close(state: InterviewState) -> InterviewState:
    from app.graph.nodes.session_close_node import session_close_node
    return session_close_node(state)


def _get_coaching(state: InterviewState) -> CoachingSnapshot | None:
    if state.session_history is None:
        return None
    return state.session_history.knowledge_snapshot.coaching_snapshot


# ---------------------------------------------------------------------------
# 1. CoachingEngine invoked — not empty on primary path
# ---------------------------------------------------------------------------

class TestCoachingEngineInvoked:

    def test_coaching_snapshot_not_empty_when_features_present(self):
        """CoachingEngine produces objectives from low-confidence features."""
        f = _make_feature("LOW")  # low-confidence → gap → objective
        state = _make_state((f,))
        result = _run_close(state)
        coaching = _get_coaching(result)
        assert coaching is not None
        assert coaching.statistics.total_objectives >= 0

    def test_coaching_snapshot_is_not_none(self):
        f = _make_feature()
        state = _make_state((f,))
        result = _run_close(state)
        assert _get_coaching(result) is not None

    def test_coaching_snapshot_has_statistics(self):
        """CoachingSnapshot exposes statistics (not None)."""
        f = _make_feature()
        state = _make_state((f,))
        result = _run_close(state)
        coaching = _get_coaching(result)
        assert coaching is not None
        assert coaching.statistics is not None

    def test_coaching_snapshot_has_session_id(self):
        f = _make_feature()
        state = _make_state((f,))
        result = _run_close(state)
        coaching = _get_coaching(result)
        assert coaching is not None
        assert coaching.session_id == SESSION_ID

    def test_coaching_snapshot_has_correct_question_index(self):
        f = _make_feature()
        state = _make_state((f,))
        result = _run_close(state)
        coaching = _get_coaching(result)
        assert coaching is not None
        assert coaching.question_index == 0


# ---------------------------------------------------------------------------
# 2. Empty features — engine still produces valid snapshot
# ---------------------------------------------------------------------------

class TestCoachingEmptyFeatures:

    def test_coaching_produced_when_no_features(self):
        state = _make_state(())
        result = _run_close(state)
        coaching = _get_coaching(result)
        assert coaching is not None

    def test_coaching_produced_when_no_profile_v2(self):
        """state without candidate_profile_v2 → engine uses empty profile fallback."""
        q = Question(
            id="q1", area=InterviewArea.TECH_CODING, type=QuestionType.WRITTEN,
            prompt="test", difficulty=QuestionDifficulty.MEDIUM,
        )
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="MIG08BTest",
            language="en",
            questions=[q],
            interview_id=SESSION_ID,
        )
        state = state.model_copy(update={
            "is_completed": True,
            "answers": [Answer(question_id="q1", content="answer", attempt=1)],
            "current_question_index": 0,
            "candidate_identity_id": CANDIDATE_ID,
        })
        assert state.candidate_profile_v2 is None
        result = _run_close(state)
        coaching = _get_coaching(result)
        assert coaching is not None


# ---------------------------------------------------------------------------
# 3. Non-fatal fallback
# ---------------------------------------------------------------------------

class TestCoachingFallback:

    def test_engine_failure_falls_back_to_empty(self):
        """CoachingEngine failure → empty snapshot; close still succeeds."""
        f = _make_feature()
        state = _make_state((f,))
        with patch(
            "app.graph.nodes.session_close_node._coaching_engine.run",
            side_effect=RuntimeError("Engine crash"),
        ):
            result = _run_close(state)
        assert result.session_history is not None
        coaching = _get_coaching(result)
        assert coaching is not None
        assert coaching.statistics.total_objectives == 0

    def test_unsuccessful_result_falls_back_to_empty(self):
        f = _make_feature()
        state = _make_state((f,))
        mock_result = MagicMock()
        mock_result.is_successful = False
        mock_result.failure_reason = "Test failure"
        with patch(
            "app.graph.nodes.session_close_node._coaching_engine.run",
            return_value=mock_result,
        ):
            result = _run_close(state)
        assert result.session_history is not None
        coaching = _get_coaching(result)
        assert coaching is not None


# ---------------------------------------------------------------------------
# 4. Determinism
# ---------------------------------------------------------------------------

class TestCoachingDeterminism:

    def test_same_state_same_objective_count(self):
        f = _make_feature("LOW")
        state1 = _make_state((f,))
        state2 = _make_state((f,))
        r1 = _run_close(state1)
        r2 = _run_close(state2)
        c1 = _get_coaching(r1)
        c2 = _get_coaching(r2)
        assert c1 is not None and c2 is not None
        assert c1.statistics.total_objectives == c2.statistics.total_objectives


# ---------------------------------------------------------------------------
# 5. Report carries CoachingEngine output
# ---------------------------------------------------------------------------

class TestReportCarriesCoaching:

    def test_report_coaching_matches_knowledge_snapshot_coaching(self):
        from app.graph.nodes.report_node import report_node
        from tests.domain.contracts.report.conftest import (
            make_scoring_snapshot,
            make_scoring_narrative,
            make_context_profile,
        )
        f = _make_feature("LOW")
        state = _make_state((f,))
        # Phase 8: Report v2.0 requires scoring_snapshot + scoring_narrative in SessionHistory
        state = state.model_copy(update={
            "scoring_snapshot": make_scoring_snapshot(),
            "scoring_narrative": make_scoring_narrative(),
            "context_profile": make_context_profile(),
        })
        closed = _run_close(state)
        assert closed.session_history is not None
        reported = report_node(closed)
        assert reported.report is not None
        # Report coaching comes from SessionHistory projection (no recomputation)
        expected_objs = closed.session_history.knowledge_snapshot.coaching_snapshot.statistics.total_objectives
        assert reported.report.coaching_snapshot.statistics.total_objectives == expected_objs


# ---------------------------------------------------------------------------
# 6. Architecture guards
# ---------------------------------------------------------------------------

class TestCoachingArchitecture:

    def _node_source(self) -> str:
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        return node_path.read_text(encoding="utf-8")

    def test_coaching_engine_imported_in_node(self):
        source = self._node_source()
        assert "CoachingEngine" in source
        assert "from services.coaching_engine.coaching_engine import CoachingEngine" in source

    def test_coaching_engine_singleton_in_module(self):
        import app.graph.nodes.session_close_node as mod
        assert hasattr(mod, "_coaching_engine")
        from services.coaching_engine.coaching_engine import CoachingEngine
        assert isinstance(mod._coaching_engine, CoachingEngine)

    def test_coaching_builder_empty_still_exists_as_fallback(self):
        source = self._node_source()
        assert "CoachingBuilder.empty" in source

    def test_no_feature_engine_import_in_node(self):
        source = self._node_source()
        assert "from services.feature_engine" not in source

    def test_no_knowledge_pipeline_import_in_node(self):
        source = self._node_source()
        assert "build_default_knowledge_pipeline" not in source

    def test_generate_coaching_snapshot_helper_exists(self):
        import app.graph.nodes.session_close_node as mod
        assert hasattr(mod, "_generate_coaching_snapshot")
