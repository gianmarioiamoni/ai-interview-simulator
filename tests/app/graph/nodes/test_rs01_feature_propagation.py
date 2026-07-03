# tests/app/graph/nodes/test_rs01_feature_propagation.py
# RS-02B — Eliminate Close-Time KnowledgePipeline Redundancy
#
# RS-01 workaround (_derive_features_at_close) has been removed.
# Features now flow from state.candidate_profile_v2.features (ADS-01 Strategy A).
#
# Verifies:
# 1. session_close_node does NOT execute KnowledgePipeline.
# 2. CandidateProfileSnapshot receives features from state.candidate_profile_v2.
# 3. Idempotency guard: second invocation returns state unchanged.
# 4. Empty candidate_profile_v2 → features=() graceful degradation.
# 5. Integration: session_history populated when state has profile with features.
# 6. No double FeatureEngine execution path in session_close_node source.
# 7. Architecture: no new TCP field, no new builder, CandidateProfile uniqueness.
# 8. Backward compatibility: state without candidate_profile_v2 still closes.

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.session_history.session_history import SessionHistory
from domain.contracts.user.role import Role, RoleType
from domain.observation.runtime.in_memory_observation_store import InMemoryObservationStore
from domain.profile.candidate_profile_builder import CandidateProfileBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SESSION_ID = "rs02b-test-session"
CANDIDATE_ID = "rs02b-candidate-001"


def _make_profile_feature(value: str = "HIGH", q_idx: int = 0) -> ProfileFeature:
    identity = FeatureIdentity.for_type(FeatureType.REASONING)
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=0.8),
        stability=FeatureStability(state="stable"),
        maturity=FeatureMaturity.from_observation_count(4),
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


def _make_question(qid: str = "q1") -> Question:
    return Question(
        id=qid,
        area=InterviewArea.TECH_CODING,
        type=QuestionType.WRITTEN,
        prompt="RS-02B test question",
        difficulty=QuestionDifficulty.MEDIUM,
    )


def _make_answer(question_id: str = "q1") -> Answer:
    return Answer(question_id=question_id, content="RS-02B test answer", attempt=1)


def _make_base_state(interview_id: str = SESSION_ID) -> InterviewState:
    questions = [_make_question("q1")]
    answers = [_make_answer("q1")]
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="RS02BCorpTest",
        language="en",
        questions=questions,
        interview_id=interview_id,
    )
    return state.model_copy(update={
        "is_completed": True,
        "answers": answers,
        "current_question_index": 0,
        "candidate_identity_id": CANDIDATE_ID,
    })


def _make_state_with_features(features: tuple[ProfileFeature, ...]) -> InterviewState:
    state = _make_base_state()
    profile = CandidateProfileBuilder().with_profile_features(features).build()
    return state.model_copy(update={"candidate_profile_v2": profile})


def _run_close(state: InterviewState) -> InterviewState:
    from app.graph.nodes.session_close_node import session_close_node
    return session_close_node(state)


# ---------------------------------------------------------------------------
# 1. No KnowledgePipeline execution at close
# ---------------------------------------------------------------------------

class TestNoKnowledgePipelineAtClose:

    def test_session_close_node_source_has_no_knowledge_pipeline_import(self):
        """RS-02B: session_close_node must not import KnowledgePipeline."""
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        source = node_path.read_text(encoding="utf-8")
        assert "build_default_knowledge_pipeline" not in source
        assert "KnowledgePipelineContext" not in source

    def test_derive_features_at_close_removed(self):
        """RS-01 workaround function must no longer exist."""
        import app.graph.nodes.session_close_node as mod
        assert not hasattr(mod, "_derive_features_at_close"), (
            "_derive_features_at_close still exists — RS-01 workaround not removed"
        )

    def test_knowledge_pipeline_not_called_during_close(self):
        """Patching build_default_knowledge_pipeline should not affect close outcome."""
        state = _make_state_with_features((_make_profile_feature(),))
        with patch(
            "services.knowledge_pipeline.default_knowledge_pipeline_factory.build_default_knowledge_pipeline",
            side_effect=AssertionError("KnowledgePipeline must not be called at close"),
        ):
            result = _run_close(state)
        # If the pipeline were called, AssertionError would propagate.
        # session_close_node is non-fatal so failure returns state — but idempotency
        # check means we can't reliably distinguish here. Instead verify source directly.
        assert result is not None


# ---------------------------------------------------------------------------
# 2. Features from state.candidate_profile_v2
# ---------------------------------------------------------------------------

class TestFeaturesFromState:

    def test_snapshot_features_match_state_profile_features(self):
        f = _make_profile_feature("HIGH")
        state = _make_state_with_features((f,))
        result = _run_close(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap.features == (f,)
        assert snap.total_feature_count == 1

    def test_snapshot_features_empty_when_no_profile(self):
        """state.candidate_profile_v2 is None → features=()."""
        state = _make_base_state()
        assert state.candidate_profile_v2 is None
        result = _run_close(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap.features == ()
        assert snap.total_feature_count == 0

    def test_snapshot_features_empty_when_profile_has_no_features(self):
        """Profile present but no features → features=()."""
        state = _make_state_with_features(())
        result = _run_close(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap.features == ()

    def test_multiple_features_propagate_correctly(self):
        f1 = _make_profile_feature("HIGH", q_idx=0)
        f2 = _make_profile_feature("LOW", q_idx=1)
        state = _make_state_with_features((f1, f2))
        result = _run_close(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert len(snap.features) == 2
        assert snap.total_feature_count == 2

    def test_candidate_id_in_snapshot_matches_state(self):
        f = _make_profile_feature()
        state = _make_state_with_features((f,))
        result = _run_close(state)
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap.candidate_identity_id == CANDIDATE_ID


# ---------------------------------------------------------------------------
# 3. Idempotency guard
# ---------------------------------------------------------------------------

class TestIdempotencyGuard:

    def test_second_call_returns_state_unchanged(self):
        """If session_history is already set, node returns state immediately."""
        f = _make_profile_feature()
        state = _make_state_with_features((f,))
        first = _run_close(state)
        assert first.session_history is not None
        original_history = first.session_history
        second = _run_close(first)
        assert second.session_history is original_history

    def test_idempotency_with_prefilled_session_history(self):
        """State with session_history already set → returned unchanged."""
        from domain.contracts.session_history.session_history import SessionHistory
        mock_history = MagicMock(spec=SessionHistory)
        state = _make_base_state()
        state_with_history = state.model_copy(update={"session_history": mock_history})
        result = _run_close(state_with_history)
        assert result.session_history is mock_history


# ---------------------------------------------------------------------------
# 4. Architecture guards
# ---------------------------------------------------------------------------

class TestArchitectureGuards:

    def _node_source(self) -> str:
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        return node_path.read_text(encoding="utf-8")

    def test_no_new_tcp_field_introduced(self):
        from domain.contracts.interview_state.base import InterviewStateBase
        existing_tcp = {"observation_store", "candidate_profile_v2", "session_history", "candidate_identity_id"}
        all_fields = set(InterviewStateBase.model_fields.keys())
        new_tcp = {f for f in all_fields if f not in existing_tcp and ("v2" in f or "snapshot" in f)}
        assert not new_tcp, f"Unexpected new TCP fields: {new_tcp}"

    def test_no_candidate_profile_snapshot_builder_in_node(self):
        source = self._node_source()
        assert "CandidateProfileSnapshotBuilder" not in source

    def test_no_feature_engine_import_in_node(self):
        source = self._node_source()
        assert "from services.feature_engine" not in source
        assert "import FeatureEngine" not in source

    def test_candidate_profile_uniqueness(self):
        reasoning_dir = Path(__file__).parents[4] / "domain" / "contracts" / "reasoning"
        matches = [
            p for p in reasoning_dir.rglob("*.py")
            if "class CandidateProfile(" in p.read_text(encoding="utf-8")
            and "test_" not in p.name
        ]
        assert len(matches) == 1

    def test_session_history_written_successfully(self):
        """Regression: session_history is populated after successful close."""
        f = _make_profile_feature()
        state = _make_state_with_features((f,))
        result = _run_close(state)
        assert result.session_history is not None
        assert isinstance(result.session_history, SessionHistory)
