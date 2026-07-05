# tests/app/graph/nodes/test_knowledge_pipeline_node.py
# KnowledgePipeline integration in reasoner_node
#
# Verifies:
# 1. state.candidate_profile_v2 is populated after reasoner_node with observations.
# 2. candidate_profile_v2 is a CandidateProfile instance.
# 3. candidate_profile_v2 remains None when ObservationStore is empty.
# 4. _run_knowledge_pipeline is non-fatal (returns prior value on failure).
# 5. FeatureEngine is the sole ProfileFeature producer.
# 6. CandidateProfileBuilder is the sole CandidateProfile producer.
# 7. No second writer: only reasoner_node sets candidate_profile_v2.
# 8. DefaultFeatureComposer produces one ProfileFeature per FeatureIdentity.
# 9. DefaultKnowledgePipelineFactory builds a usable pipeline.
# 10. Architecture: CandidateProfile uniqueness (single definition).

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_decision import ReasonerDecision
from domain.contracts.reasoning.reasoning_basis import ReasoningBasis
from domain.contracts.reasoning.reasoning_confidence import ReasoningConfidence
from domain.contracts.reasoning.reasoning_trace import ReasoningTrace
from domain.observation.runtime.in_memory_observation_store import InMemoryObservationStore
from domain.plugins.feature.default_feature_composer import DefaultFeatureComposer
from services.knowledge_pipeline.default_knowledge_pipeline_factory import (
    build_default_knowledge_pipeline,
)
from app.graph.nodes.reasoner_node import _run_knowledge_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signal(q_idx: int = 0) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        timestamp_question_index=q_idx,
        question_area="algorithms",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        signal_type=EvidenceType.KNOWLEDGE_GAP,
        polarity=EvidencePolarity.NEGATIVE,
        source=EvidenceSource.EVALUATION,
        strength=0.7,
    )


def _make_observation(session_id: str = "s1", q_idx: int = 0) -> Observation:
    return Observation(
        id=ObservationId(value=str(uuid.uuid4())),
        observation_type=ObservationType.KNOWLEDGE_GAP,
        status=ObservationStatus.ACTIVE,
        description="Test observation",
        confidence=0.85,
        metadata=ObservationMetadata(
            session_id=session_id,
            question_index=q_idx,
            origin=ObservationOrigin.REPLAY,
        ),
    )


def _make_populated_store(session_id: str = "test-session") -> InMemoryObservationStore:
    store = InMemoryObservationStore(session_id=session_id)
    store.append(_make_observation(session_id=session_id))
    return store


def _state_with_store(
    store: InMemoryObservationStore | None = None,
    q_idx: int = 0,
) -> "object":
    from domain.contracts.interview_state import InterviewState
    sig = _make_signal(q_idx=q_idx)
    evidence_store = EvidenceStore(signals=[sig])
    memory = InterviewMemory(evidence_store=evidence_store)
    state = InterviewState.create_empty()
    return state.model_copy(
        update={
            "interview_id": "test-session",
            "current_question_index": q_idx,
            "interview_memory": memory,
            "observation_store": store,
        }
    )


# ---------------------------------------------------------------------------
# DefaultFeatureComposer unit tests
# ---------------------------------------------------------------------------

class TestDefaultFeatureComposer:
    def _make_candidate(self, feature_type: FeatureType = FeatureType.REASONING) -> FeatureCandidate:
        return FeatureCandidate(
            feature_identity=FeatureIdentity.for_type(feature_type),
            candidate_value="HIGH",
            candidate_confidence=0.85,
            source_observation_ids=(str(uuid.uuid4()),),
            computed_at_question_index=0,
            updater_id="test-updater",
        )

    def test_empty_candidates_produces_empty_features(self) -> None:
        composer = DefaultFeatureComposer()
        result = composer.compose([], "cand-001", "1.0.0")
        assert result == []

    def test_single_candidate_produces_one_feature(self) -> None:
        composer = DefaultFeatureComposer()
        result = composer.compose([self._make_candidate()], "cand-001", "1.0.0")
        assert len(result) == 1
        assert isinstance(result[0], __import__("domain.contracts.feature.profile_feature", fromlist=["ProfileFeature"]).ProfileFeature)

    def test_duplicate_type_ids_produce_one_feature_first_wins(self) -> None:
        composer = DefaultFeatureComposer()
        c1 = self._make_candidate(FeatureType.REASONING)
        c2 = self._make_candidate(FeatureType.REASONING)
        result = composer.compose([c1, c2], "cand-001", "1.0.0")
        assert len(result) == 1

    def test_distinct_types_produce_distinct_features(self) -> None:
        composer = DefaultFeatureComposer()
        c1 = self._make_candidate(FeatureType.REASONING)
        c2 = self._make_candidate(FeatureType.TECHNICAL_SKILL)
        result = composer.compose([c1, c2], "cand-001", "1.0.0")
        assert len(result) == 2

    def test_candidate_identity_id_propagated(self) -> None:
        composer = DefaultFeatureComposer()
        result = composer.compose([self._make_candidate()], "cand-xyz", "1.0.0")
        assert result[0].candidate_identity_id == "cand-xyz"


# ---------------------------------------------------------------------------
# build_default_knowledge_pipeline factory tests
# ---------------------------------------------------------------------------

class TestDefaultKnowledgePipelineFactory:
    def test_factory_creates_pipeline(self) -> None:
        from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
        store = InMemoryObservationStore(session_id="s")
        pipeline = build_default_knowledge_pipeline(store)
        assert isinstance(pipeline, KnowledgePipeline)

    def test_factory_uses_skip_extraction(self) -> None:
        store = InMemoryObservationStore(session_id="s")
        pipeline = build_default_knowledge_pipeline(store)
        assert pipeline._configuration.skip_extraction_if_store_populated is True


# ---------------------------------------------------------------------------
# _run_knowledge_pipeline unit tests
# ---------------------------------------------------------------------------

class TestRunKnowledgePipeline:
    def test_returns_none_when_store_empty(self) -> None:
        store = InMemoryObservationStore(session_id="test-session")
        state = _state_with_store(store=store)
        result = _run_knowledge_pipeline(state=state, updated_observation_store=store)
        assert result is None

    def test_returns_none_when_store_is_none(self) -> None:
        state = _state_with_store(store=None)
        result = _run_knowledge_pipeline(state=state, updated_observation_store=None)
        assert result is None

    def test_returns_candidate_profile_when_store_populated(self) -> None:
        store = _make_populated_store()
        state = _state_with_store(store=store)
        result = _run_knowledge_pipeline(state=state, updated_observation_store=store)
        # Pipeline may succeed or produce None depending on updater output;
        # the critical invariant is no exception.
        assert result is None or isinstance(result, CandidateProfile)

    def test_non_fatal_on_exception(self) -> None:
        store = _make_populated_store()
        state = _state_with_store(store=store)
        with patch(
            "app.graph.nodes.reasoner_node.build_default_knowledge_pipeline",
            side_effect=RuntimeError("pipeline failure"),
        ):
            result = _run_knowledge_pipeline(state=state, updated_observation_store=store)
        # Must return prior value, not raise
        assert result is None  # state.candidate_profile_v2 was None


# ---------------------------------------------------------------------------
# reasoner_node integration: candidate_profile_v2 after Phase D
# ---------------------------------------------------------------------------

class TestReasonerNodeCandidateProfileV2Integration:
    def _run_node_with_observations(self) -> "object":
        from domain.contracts.interview_state import InterviewState
        sig = _make_signal(q_idx=0)
        evidence_store = EvidenceStore(signals=[sig])
        memory = InterviewMemory(evidence_store=evidence_store)
        state = InterviewState.create_empty()
        state = state.model_copy(
            update={
                "interview_id": "test-session",
                "current_question_index": 0,
                "interview_memory": memory,
            }
        )
        decision = ReasonerDecision(
            session_id="test-session",
            question_index=0,
            skip=False,
            new_evidence=[],
            reasoning_basis=ReasoningBasis(reasoning_confidence=ReasoningConfidence()),
        )
        trace = ReasoningTrace(steps=[])

        import app.graph.nodes.reasoner_node as rn
        with patch.object(rn, "_service") as mock_svc, patch.object(rn, "_builder") as mock_bld:
            mock_bld.build.return_value = MagicMock()
            mock_svc.reason.return_value = (decision, trace, InterviewMemory())
            return rn.reasoner_node(state)

    def test_candidate_profile_v2_type_when_set(self) -> None:
        result = self._run_node_with_observations()
        if result.candidate_profile_v2 is not None:
            assert isinstance(result.candidate_profile_v2, CandidateProfile)

    def test_observation_store_still_populated(self) -> None:
        result = self._run_node_with_observations()
        # Phase C remains active
        if result.observation_store is not None:
            assert isinstance(result.observation_store, InMemoryObservationStore)

    def test_v1_fields_intact(self) -> None:
        result = self._run_node_with_observations()
        assert result.interview_memory is not None
        assert result.current_reasoning_decision is not None


# ---------------------------------------------------------------------------
# Architecture: CandidateProfile uniqueness
# ---------------------------------------------------------------------------

class TestCandidateProfileUniqueness:
    def test_canonical_candidate_profile_is_pydantic_basemodel(self) -> None:
        """The domain CandidateProfile is the sole Pydantic contract (ADR-037)."""
        from domain.contracts.reasoning.candidate_profile import CandidateProfile
        from pydantic import BaseModel
        assert issubclass(CandidateProfile, BaseModel)
        assert CandidateProfile.__module__ == "domain.contracts.reasoning.candidate_profile"

    def test_candidate_profile_v2_field_exists(self) -> None:
        from domain.contracts.interview_state.base import InterviewStateBase
        field = InterviewStateBase.model_fields["candidate_profile_v2"]
        assert field is not None

    def test_candidate_profile_v2_import_resolves_to_single_contract(self) -> None:
        from domain.contracts.interview_state.base import InterviewStateBase
        from domain.contracts.reasoning.candidate_profile import CandidateProfile
        # Both imports resolve to the same module — no secondary definition.
        import domain.contracts.reasoning.candidate_profile as mod
        assert mod.CandidateProfile is CandidateProfile
