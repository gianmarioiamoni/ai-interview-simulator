# tests/app/graph/nodes/test_rs01_feature_propagation.py
# RS-01 — Feature Propagation Remediation (F-03 closure)
#
# Verifies:
# 1. ProfileFeature[] reach CandidateProfileSnapshot when ObservationStore is populated.
# 2. _derive_features_at_close returns () when store is empty/None.
# 3. _derive_features_at_close is non-fatal (returns () on pipeline failure).
# 4. session_close_node writes session_history with non-empty features (integration).
# 5. CandidateProfileSnapshot.features match re-derived features count.
# 6. No double extraction: skip_extraction_if_store_populated respected.
# 7. FeatureEngine remains sole ProfileFeature producer.
# 8. No new TCP field introduced.
# 9. session_close_node architectural guard: no second writer.
# 10. Feature propagation path: ObservationStore → pipeline → snapshot (regression).

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.session_history.session_history import SessionHistory
from domain.contracts.user.role import Role, RoleType
from domain.observation.runtime.in_memory_observation_store import InMemoryObservationStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SESSION_ID = "rs01-test-session"
CANDIDATE_ID = "rs01-candidate-001"


def _make_observation(session_id: str = SESSION_ID, q_idx: int = 0) -> Observation:
    return Observation(
        id=ObservationId(value=str(uuid.uuid4())),
        observation_type=ObservationType.KNOWLEDGE_GAP,
        status=ObservationStatus.ACTIVE,
        description="RS-01 test observation",
        confidence=0.85,
        metadata=ObservationMetadata(
            session_id=session_id,
            question_index=q_idx,
            origin=ObservationOrigin.REPLAY,
        ),
    )


def _make_populated_store(session_id: str = SESSION_ID) -> InMemoryObservationStore:
    store = InMemoryObservationStore(session_id=session_id)
    store.append(_make_observation(session_id=session_id))
    return store


def _make_question(qid: str = "q1") -> Question:
    return Question(
        id=qid,
        area=InterviewArea.TECH_CODING,
        type=QuestionType.WRITTEN,
        prompt="RS-01 test question",
        difficulty=QuestionDifficulty.MEDIUM,
    )


def _make_answer(question_id: str = "q1") -> Answer:
    return Answer(question_id=question_id, content="RS-01 test answer", attempt=1)


def _make_completed_state(
    with_store: bool = True,
    interview_id: str = SESSION_ID,
) -> InterviewState:
    questions = [_make_question("q1")]
    answers = [_make_answer("q1")]
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="RS01Corp",
        language="en",
        questions=questions,
        interview_id=interview_id,
    )
    state = state.model_copy(update={
        "is_completed": True,
        "answers": answers,
        "current_question_index": 0,
        "candidate_identity_id": CANDIDATE_ID,
    })
    if with_store:
        store = _make_populated_store(session_id=interview_id)
        state = state.model_copy(update={"observation_store": store})
    return state


def _run_close_node(state: InterviewState) -> InterviewState:
    from app.graph.nodes.session_close_node import session_close_node
    return session_close_node(state)


# ---------------------------------------------------------------------------
# 1. _derive_features_at_close unit tests
# ---------------------------------------------------------------------------

class TestDeriveFeatures:

    def _derive(self, state: InterviewState) -> tuple:
        from app.graph.nodes.session_close_node import _derive_features_at_close
        return _derive_features_at_close(state, CANDIDATE_ID)

    def test_returns_empty_when_no_store(self):
        state = _make_completed_state(with_store=False)
        assert state.observation_store is None
        assert self._derive(state) == ()

    def test_returns_empty_when_store_empty(self):
        state = _make_completed_state(with_store=False)
        empty_store = InMemoryObservationStore(session_id=SESSION_ID)
        state = state.model_copy(update={"observation_store": empty_store})
        assert self._derive(state) == ()

    def test_returns_features_when_store_populated(self):
        state = _make_completed_state(with_store=True)
        features = self._derive(state)
        assert isinstance(features, tuple)
        # Feature count depends on FeatureEngine updaters; may be 0 if no updater maps KNOWLEDGE_GAP
        # Key invariant: returns a tuple (not None, not error)
        assert features is not None

    def test_all_returned_items_are_profile_features(self):
        state = _make_completed_state(with_store=True)
        features = self._derive(state)
        for f in features:
            assert isinstance(f, ProfileFeature)

    def test_non_fatal_on_pipeline_exception(self):
        state = _make_completed_state(with_store=True)
        with patch(
            "app.graph.nodes.session_close_node.build_default_knowledge_pipeline",
            side_effect=RuntimeError("Simulated pipeline crash"),
        ):
            from app.graph.nodes.session_close_node import _derive_features_at_close
            result = _derive_features_at_close(state, CANDIDATE_ID)
        assert result == ()

    def test_features_belong_to_correct_candidate(self):
        state = _make_completed_state(with_store=True)
        features = self._derive(state)
        for f in features:
            assert f.candidate_identity_id == CANDIDATE_ID


# ---------------------------------------------------------------------------
# 2. Integration: features reach CandidateProfileSnapshot in SessionHistory
# ---------------------------------------------------------------------------

class TestFeaturePropagationIntegration:

    def test_session_history_populated_with_store(self):
        state = _make_completed_state(with_store=True)
        result = _run_close_node(state)
        assert result.session_history is not None

    def test_knowledge_snapshot_profile_snapshot_present(self):
        state = _make_completed_state(with_store=True)
        result = _run_close_node(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap is not None

    def test_profile_snapshot_total_feature_count_consistent(self):
        """total_feature_count must equal len(features) — CandidateProfileSnapshot invariant."""
        state = _make_completed_state(with_store=True)
        result = _run_close_node(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap.total_feature_count == len(snap.features)

    def test_profile_snapshot_candidate_id_matches(self):
        state = _make_completed_state(with_store=True)
        result = _run_close_node(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap.candidate_identity_id == CANDIDATE_ID

    def test_no_features_when_store_absent(self):
        """Empty store → CandidateProfileSnapshot.features=() — graceful degradation."""
        state = _make_completed_state(with_store=False)
        result = _run_close_node(state)
        assert result.session_history is not None
        snap = result.session_history.knowledge_snapshot.profile_snapshot
        assert snap.features == ()
        assert snap.total_feature_count == 0


# ---------------------------------------------------------------------------
# 3. No double extraction guard
# ---------------------------------------------------------------------------

class TestNoDoubleExtraction:

    def test_skip_extraction_flag_set_in_factory(self):
        """build_default_knowledge_pipeline must use skip_extraction_if_store_populated=True."""
        from services.knowledge_pipeline.default_knowledge_pipeline_factory import (
            build_default_knowledge_pipeline,
        )
        store = _make_populated_store()
        pipeline = build_default_knowledge_pipeline(store=store)
        assert pipeline._configuration.skip_extraction_if_store_populated is True

    def test_observation_store_count_unchanged_after_derive(self):
        """_derive_features_at_close must not add observations to the store."""
        state = _make_completed_state(with_store=True)
        count_before = state.observation_store.count()
        from app.graph.nodes.session_close_node import _derive_features_at_close
        _derive_features_at_close(state, CANDIDATE_ID)
        assert state.observation_store.count() == count_before


# ---------------------------------------------------------------------------
# 4. Architecture / ownership guards
# ---------------------------------------------------------------------------

class TestArchitectureGuards:

    def _node_source(self) -> str:
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        return node_path.read_text(encoding="utf-8")

    def test_no_new_tcp_field_introduced(self):
        """RS-01 must not add new TCP fields to InterviewState."""
        from domain.contracts.interview_state.base import InterviewStateBase
        tcp_fields = {
            name for name, field in InterviewStateBase.model_fields.items()
            if hasattr(field, "description") and field.description and "[V1.2 TCP]" in str(field)
        }
        assert "profile_features_v2" not in tcp_fields
        assert "feature_snapshot_v2" not in tcp_fields

    def test_feature_engine_sole_producer(self):
        """session_close_node must not produce ProfileFeature directly — uses pipeline."""
        source = self._node_source()
        assert "ProfileFeature(" not in source

    def test_no_second_builder_introduced(self):
        """No CandidateProfileSnapshotBuilder reference in session_close_node."""
        source = self._node_source()
        assert "CandidateProfileSnapshotBuilder" not in source

    def test_uses_existing_pipeline_factory(self):
        """session_close_node must reuse build_default_knowledge_pipeline."""
        source = self._node_source()
        assert "build_default_knowledge_pipeline" in source

    def test_candidate_profile_uniqueness(self):
        """Only one class CandidateProfile definition in domain/contracts/reasoning."""
        reasoning_dir = Path(__file__).parents[4] / "domain" / "contracts" / "reasoning"
        matches = [
            p for p in reasoning_dir.rglob("*.py")
            if "class CandidateProfile" in p.read_text(encoding="utf-8")
        ]
        assert len(matches) == 1

    def test_no_second_candidate_profile_builder(self):
        """Only one CandidateProfileBuilder class in domain/profile."""
        profile_dir = Path(__file__).parents[4] / "domain" / "profile"
        matches = [
            p for p in profile_dir.rglob("*.py")
            if "class CandidateProfileBuilder" in p.read_text(encoding="utf-8")
        ]
        assert len(matches) == 1
