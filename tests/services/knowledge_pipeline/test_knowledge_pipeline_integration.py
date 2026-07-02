# tests/services/knowledge_pipeline/test_knowledge_pipeline_integration.py
# Integration tests: end-to-end pipeline with real domain components

from __future__ import annotations

import uuid

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.extraction.observation_rule_registry import ObservationRuleRegistry
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
from domain.plugins.feature.updaters.confidence_feature_updater import ConfidenceFeatureUpdater
from domain.plugins.feature.updaters.reasoning_feature_updater import ReasoningFeatureUpdater
from domain.plugins.observation.rules.repeated_strength_observation_rule import RepeatedStrengthObservationRule
from services.feature_engine.feature_engine import FeatureEngine
from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
from tests.services.knowledge_pipeline.conftest import (
    InMemoryObservationStore,
    PassthroughComposer,
    make_signal,
)


def make_full_pipeline(session_id: str = "integ-sess") -> KnowledgePipeline:
    store = InMemoryObservationStore(session_id=session_id)

    registry = ObservationRuleRegistry()
    registry.register(RepeatedStrengthObservationRule())
    registry.freeze()

    extractor = ObservationExtractor(registry=registry, store=store)
    query_engine = ObservationStoreQueryEngine(store=store)

    feature_engine = FeatureEngine(
        updaters=[
            ReasoningFeatureUpdater(),
            ConfidenceFeatureUpdater(),
        ],
        composer=PassthroughComposer(),
    )

    return KnowledgePipeline(
        extractor=extractor,
        store=store,
        query_engine=query_engine,
        feature_engine=feature_engine,
    )


def make_ctx(
    question_index: int = 0,
    session_id: str = "integ-sess",
    prior_profile: CandidateProfile | None = None,
) -> KnowledgePipelineContext:
    return KnowledgePipelineContext(
        session_id=session_id,
        candidate_identity_id="cand-integ-001",
        question_index=question_index,
        signals=(make_signal(question_index=question_index, session_id=session_id),),
        prior_profile=prior_profile,
    )


class TestEndToEndPipeline:
    def test_single_cycle_produces_valid_profile(self):
        pipeline = make_full_pipeline()
        result = pipeline.run(make_ctx())

        assert result.is_successful is True
        assert result.profile is not None
        assert isinstance(result.profile, CandidateProfile)
        assert result.profile.questions_answered == 1
        assert result.profile.last_updated_at_question_index == 0

    def test_three_cycles_profile_progresses(self):
        pipeline = make_full_pipeline()
        prior = None
        for q in range(3):
            ctx = make_ctx(question_index=q, prior_profile=prior)
            result = pipeline.run(ctx)
            assert result.is_successful is True
            prior = result.profile

        assert prior is not None
        assert prior.questions_answered == 3
        assert prior.last_updated_at_question_index == 2

    def test_diagnostics_records_all_stages(self):
        from services.knowledge_pipeline.knowledge_pipeline_diagnostics import PipelineStage
        pipeline = make_full_pipeline()
        result = pipeline.run(make_ctx())

        stage_set = {r.stage for r in result.diagnostics.stage_records}
        assert PipelineStage.EXTRACTION in stage_set
        assert PipelineStage.STORE_APPEND in stage_set
        assert PipelineStage.QUERY_ENGINE in stage_set
        assert PipelineStage.FEATURE_ENGINE in stage_set
        assert PipelineStage.PROFILE_BUILD in stage_set

    def test_metrics_populated(self):
        pipeline = make_full_pipeline()
        result = pipeline.run(make_ctx())
        m = result.diagnostics.metrics
        assert m.signals_received == 1
        assert m.total_duration_ms >= 0.0

    def test_pipeline_result_is_immutable(self):
        pipeline = make_full_pipeline()
        result = pipeline.run(make_ctx())
        with pytest.raises(Exception):
            result.is_successful = False  # type: ignore[misc]

    def test_profile_is_immutable(self):
        pipeline = make_full_pipeline()
        result = pipeline.run(make_ctx())
        assert result.profile is not None
        with pytest.raises(Exception):
            result.profile.questions_answered = 99  # type: ignore[misc]
