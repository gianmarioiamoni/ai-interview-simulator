# services/knowledge_pipeline/default_knowledge_pipeline_factory.py
# Factory for the production KnowledgePipeline used in the live session path.
# Wires ObservationStore → FeatureEngine → CandidateProfileBuilder → CandidateProfile.
#
# Configuration: skip_extraction_if_store_populated=True because reasoner_node
# already runs ObservationExtractor before this pipeline is invoked.
# No double extraction.

from __future__ import annotations

from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.observation_store import ObservationStore
from domain.observation.runtime.default_observation_registry import build_default_observation_registry
from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
from domain.plugins.feature.default_feature_composer import DefaultFeatureComposer
from domain.plugins.feature.updaters.confidence_feature_updater import ConfidenceFeatureUpdater
from domain.plugins.feature.updaters.coverage_feature_updater import CoverageFeatureUpdater
from domain.plugins.feature.updaters.reasoning_feature_updater import ReasoningFeatureUpdater
from domain.plugins.feature.updaters.technical_skill_feature_updater import TechnicalSkillFeatureUpdater
from domain.plugins.feature.updaters.trend_feature_updater import TrendFeatureUpdater
from services.feature_engine.incremental_feature_engine import IncrementalFeatureEngine
from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
from services.knowledge_pipeline.knowledge_pipeline_configuration import KnowledgePipelineConfiguration


def build_default_knowledge_pipeline(
    store: ObservationStore,
) -> KnowledgePipeline:
    """Build and return the production KnowledgePipeline for the live session path.

    The extractor is constructed with a dummy frozen registry because
    skip_extraction_if_store_populated=True ensures Stage 1 is never executed
    when the store is already populated.  ObservationExtractor is
    constructed to satisfy the KnowledgePipeline constructor contract; it is
    never called when the store has observations.

    Args:
        store: The session-scoped ObservationStore populated by reasoner_node.

    Returns:
        A configured, ready-to-run KnowledgePipeline instance.
    """
    query_engine = ObservationStoreQueryEngine(store=store)

    extractor = ObservationExtractor(
        registry=build_default_observation_registry(),
        store=store,
    )

    feature_engine = IncrementalFeatureEngine(
        updaters=[
            TechnicalSkillFeatureUpdater(),
            ReasoningFeatureUpdater(),
            ConfidenceFeatureUpdater(),
            CoverageFeatureUpdater(),
            TrendFeatureUpdater(),
        ],
        composer=DefaultFeatureComposer(),
    )

    configuration = KnowledgePipelineConfiguration(
        skip_extraction_if_store_populated=True,
        allow_empty_signal_cycles=True,
    )

    return KnowledgePipeline(
        extractor=extractor,
        store=store,
        query_engine=query_engine,
        feature_engine=feature_engine,
        configuration=configuration,
    )
