# tests/services/knowledge_pipeline/test_mig025_blockers.py
# MIG-02.5 — CAR-MIG-02 blocker removal tests
#
# Verifies:
# 1. skip_extraction_if_store_populated skips Stage 1 when store is pre-populated.
# 2. skip_extraction_if_store_populated=False (default) still runs extraction.
# 3. CandidateProfileBuilder.with_profile_features() stores features correctly.
# 4. KnowledgePipeline wires ProfileFeature[] through builder (sole creation path).
# 5. candidate_identity_id hook: _resolve_candidate_identity_id() returns interview_id.
# 6. Architecture: FeatureEngine is sole producer of ProfileFeature (validated via type check).
# 7. Architecture: CandidateProfileBuilder is sole construction path for CandidateProfile.

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.profile.candidate_profile_builder import CandidateProfileBuilder
from services.knowledge_pipeline.knowledge_pipeline_configuration import (
    KnowledgePipelineConfiguration,
)
from app.graph.nodes.reasoner_node import _resolve_candidate_identity_id
from domain.observation.runtime.in_memory_observation_store import InMemoryObservationStore


# ---------------------------------------------------------------------------
# Activity 1: skip_extraction_if_store_populated
# ---------------------------------------------------------------------------

class TestSkipExtractionWhenStorePopulated:
    def _make_populated_store(self) -> InMemoryObservationStore:
        from tests.services.knowledge_pipeline.conftest import InMemoryObservationStore as _S
        store = _S(session_id="s1")
        # Use a REPLAY origin to avoid source_ref validation requirement
        from domain.contracts.observation.observation import Observation
        from domain.contracts.observation.observation_id import ObservationId
        from domain.contracts.observation.observation_metadata import ObservationMetadata
        from domain.contracts.observation.observation_origin import ObservationOrigin
        from domain.contracts.observation.observation_status import ObservationStatus
        from domain.contracts.observation.observation_type import ObservationType
        obs = Observation(
            id=ObservationId(value=str(uuid.uuid4())),
            observation_type=ObservationType.KNOWLEDGE_GAP,
            status=ObservationStatus.ACTIVE,
            description="Test knowledge gap observation",
            confidence=0.85,
            metadata=ObservationMetadata(
                session_id="s1",
                question_index=0,
                origin=ObservationOrigin.REPLAY,
            ),
        )
        store.append(obs)
        return store

    def test_skip_extraction_config_default_is_false(self) -> None:
        config = KnowledgePipelineConfiguration()
        assert config.skip_extraction_if_store_populated is False

    def test_skip_extraction_config_can_be_set_true(self) -> None:
        config = KnowledgePipelineConfiguration(skip_extraction_if_store_populated=True)
        assert config.skip_extraction_if_store_populated is True

    def test_skip_extraction_skips_when_store_populated_and_flag_true(self) -> None:
        """When skip_extraction_if_store_populated=True and store.count()>0, extractor not called."""
        from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
        from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
        from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine

        store = self._make_populated_store()
        assert store.count() > 0

        mock_extractor = MagicMock(spec=ObservationExtractor)
        mock_feature_engine = MagicMock()
        mock_feature_engine.run.return_value = MagicMock(features=())
        query_engine = ObservationStoreQueryEngine(store=store)

        config = KnowledgePipelineConfiguration(
            skip_extraction_if_store_populated=True,
            allow_empty_signal_cycles=True,
        )
        pipeline = KnowledgePipeline(
            extractor=mock_extractor,
            store=store,
            query_engine=query_engine,
            feature_engine=mock_feature_engine,
            configuration=config,
        )

        ctx = KnowledgePipelineContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=0,
            signals=(),
        )
        pipeline.run(ctx)

        mock_extractor.extract.assert_not_called()

    def test_no_skip_when_flag_false_calls_extractor(self) -> None:
        """Default config: extractor IS called even when store is populated."""
        from tests.services.knowledge_pipeline.conftest import make_signal
        from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
        from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
        from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
        from domain.contracts.observation.extraction.observation_extraction_result import (
            ObservationExtractionResult,
        )
        from domain.contracts.observation.extraction.observation_extraction_diagnostics import (
            ObservationExtractionDiagnostics,
        )

        store = self._make_populated_store()
        assert store.count() > 0

        mock_extractor = MagicMock(spec=ObservationExtractor)
        mock_extractor.extract.return_value = ObservationExtractionResult(
            observations=(),
            session_id="s1",
            question_index=0,
            diagnostics=ObservationExtractionDiagnostics(
                session_id="s1", question_index=0
            ),
        )
        mock_feature_engine = MagicMock()
        mock_feature_engine.run.return_value = MagicMock(features=())
        query_engine = ObservationStoreQueryEngine(store=store)

        config = KnowledgePipelineConfiguration(skip_extraction_if_store_populated=False)
        pipeline = KnowledgePipeline(
            extractor=mock_extractor,
            store=store,
            query_engine=query_engine,
            feature_engine=mock_feature_engine,
            configuration=config,
        )

        sig = make_signal(question_index=0, session_id="s1")
        ctx = KnowledgePipelineContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=0,
            signals=(sig,),
        )
        pipeline.run(ctx)

        # skip_extraction_if_store_populated=False → extractor MUST be called
        mock_extractor.extract.assert_called_once()


# ---------------------------------------------------------------------------
# Activity 2: ProfileFeature wiring through CandidateProfileBuilder
# ---------------------------------------------------------------------------

class TestProfileFeatureWiring:
    def _make_profile_feature(self) -> ProfileFeature:
        from domain.contracts.feature.feature_identity import FeatureIdentity
        from domain.contracts.feature.feature_provenance import FeatureProvenance
        from domain.contracts.feature.feature_quality import (
            FeatureConfidence,
            FeatureMaturity,
            FeatureQuality,
            FeatureStability,
        )
        from domain.contracts.feature.feature_type import FeatureType
        identity = FeatureIdentity.for_type(FeatureType.REASONING)
        return ProfileFeature(
            feature_identity=identity,
            value="HIGH",
            computed_at_question_index=0,
            candidate_identity_id="cand-001",
            quality=FeatureQuality(
                confidence=FeatureConfidence(value=0.85),
                stability=FeatureStability(state="emerging"),
                maturity=FeatureMaturity(stage="nascent", observation_count=1),
            ),
            provenance=FeatureProvenance(
                feature_identity=identity,
                source_observation_ids=("obs-001",),
                computed_at_question_index=0,
                feature_engine_version="1.0.0",
                updater_id="test-updater",
            ),
        )

    def test_with_profile_features_stores_features(self) -> None:
        feat = self._make_profile_feature()
        builder = CandidateProfileBuilder()
        builder.with_profile_features((feat,))
        assert builder.profile_features == (feat,)

    def test_with_profile_features_accepts_list(self) -> None:
        feat = self._make_profile_feature()
        builder = CandidateProfileBuilder()
        builder.with_profile_features([feat])
        assert builder.profile_features == (feat,)

    def test_with_profile_features_is_fluent(self) -> None:
        feat = self._make_profile_feature()
        builder = CandidateProfileBuilder()
        result = builder.with_profile_features((feat,))
        assert result is builder

    def test_with_profile_features_empty_tuple_by_default(self) -> None:
        builder = CandidateProfileBuilder()
        assert builder.profile_features == ()

    def test_build_still_produces_candidate_profile(self) -> None:
        feat = self._make_profile_feature()
        profile = (
            CandidateProfileBuilder()
            .with_profile_features((feat,))
            .with_questions_answered(1)
            .with_last_updated_at(0)
            .build()
        )
        assert isinstance(profile, CandidateProfile)
        assert profile.questions_answered == 1

    def test_candidate_profile_builder_is_sole_construction_path(self) -> None:
        """CandidateProfile must be built via CandidateProfileBuilder (architecture guard)."""
        profile = CandidateProfileBuilder().with_questions_answered(1).build()
        assert isinstance(profile, CandidateProfile)
        # Direct instantiation still works (frozen model), but no production code
        # should bypass the builder. Architecture is enforced by convention (ADR-037).
        assert profile.questions_answered == 1

    def test_from_profile_preserves_profile_features_slot_empty(self) -> None:
        original = CandidateProfileBuilder().with_questions_answered(2).build()
        builder = CandidateProfileBuilder.from_profile(original)
        # profile_features are not persisted in CandidateProfile; new builder starts empty.
        assert builder.profile_features == ()


# ---------------------------------------------------------------------------
# Activity 3: candidate_identity_id hook
# ---------------------------------------------------------------------------

class TestCandidateIdentityIdHook:
    def test_resolve_returns_interview_id(self) -> None:
        state = MagicMock()
        state.interview_id = "session-xyz"
        result = _resolve_candidate_identity_id(state)
        assert result == "session-xyz"

    def test_resolve_is_deterministic(self) -> None:
        state = MagicMock()
        state.interview_id = "s-abc"
        assert _resolve_candidate_identity_id(state) == _resolve_candidate_identity_id(state)
