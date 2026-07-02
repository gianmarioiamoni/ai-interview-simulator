# tests/services/knowledge_pipeline/conftest.py
# Shared fixtures for KnowledgePipeline test suite

from __future__ import annotations

import uuid
from typing import Any

import pytest

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_composer import FeatureComposer
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.extraction.observation_rule_registry import ObservationRuleRegistry
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_query import ObservationQuery
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
from services.feature_engine.feature_engine import FeatureEngine
from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
from services.knowledge_pipeline.knowledge_pipeline_configuration import KnowledgePipelineConfiguration
from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext


# ---------------------------------------------------------------------------
# In-memory ObservationStore (re-usable across tests)
# ---------------------------------------------------------------------------

class InMemoryObservationStore(ObservationStore):
    def __init__(self, session_id: str = "sess-001") -> None:
        self._session_id = session_id
        self._store: dict[str, Observation] = {}

    def session_id(self) -> str:
        return self._session_id

    def count(self) -> int:
        return len(self._store)

    def append(self, observation: Observation) -> None:
        key = (
            observation.observation_type,
            observation.metadata.origin,
            observation.metadata.question_index,
            observation.metadata.session_id,
        )
        for oid, existing in list(self._store.items()):
            ek = (
                existing.observation_type,
                existing.metadata.origin,
                existing.metadata.question_index,
                existing.metadata.session_id,
            )
            if ek == key and existing.status == ObservationStatus.ACTIVE:
                self._store[oid] = existing.with_status(ObservationStatus.SUPERSEDED)
        self._store[observation.id.value] = observation

    def get(self, observation_id: Any) -> Observation | None:
        return self._store.get(observation_id.value)

    def query(self, observation_query: ObservationQuery) -> list[Observation]:
        return list(self._store.values())

    def snapshot(self) -> ObservationSnapshot:
        return ObservationSnapshot.from_observations(self._session_id, list(self._store.values()))


# ---------------------------------------------------------------------------
# Stub ObservationRule
# ---------------------------------------------------------------------------

class AlwaysMatchRule(ObservationRule):
    def __init__(
        self,
        rule_id: str = "always-match",
        obs_type: ObservationType = ObservationType.TECHNICAL_CORRECTNESS,
        confidence: float = 0.85,
    ) -> None:
        self._rule_id = rule_id
        self._obs_type = obs_type
        self._confidence = confidence

    @property
    def rule_id(self) -> str:
        return self._rule_id

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.NORMAL

    def evaluate(self, context: Any) -> list[ObservationRuleMatch]:
        return [
            ObservationRuleMatch(
                rule_id=self._rule_id,
                observation_type=self._obs_type,
                confidence=self._confidence,
                description="stub match",
            )
        ]


class NeverMatchRule(ObservationRule):
    @property
    def rule_id(self) -> str:
        return "never-match"

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.LOW

    def evaluate(self, context: Any) -> list[ObservationRuleMatch]:
        return []


class ErrorRule(ObservationRule):
    @property
    def rule_id(self) -> str:
        return "error-rule"

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.NORMAL

    def evaluate(self, context: Any) -> list[ObservationRuleMatch]:
        raise RuntimeError("simulated rule error")


# ---------------------------------------------------------------------------
# Stub FeatureUpdater
# ---------------------------------------------------------------------------

class StubUpdater(FeatureUpdater):
    def __init__(
        self,
        candidates: list[FeatureCandidate] | None = None,
        updater_id: str = "stub-updater",
    ) -> None:
        self._candidates = candidates or []
        self._id = updater_id

    @property
    def updater_id(self) -> str:
        return self._id

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset()

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset(c.feature_identity.feature_type_id for c in self._candidates)

    @property
    def invocation_order(self) -> int:
        return 1

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        return list(self._candidates)


class EmptyUpdater(FeatureUpdater):
    @property
    def updater_id(self) -> str:
        return "empty-updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset()

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset()

    @property
    def invocation_order(self) -> int:
        return 1

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        return []


# ---------------------------------------------------------------------------
# PassthroughComposer
# ---------------------------------------------------------------------------

class PassthroughComposer(FeatureComposer):
    def compose(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> list[ProfileFeature]:
        seen: dict[str, ProfileFeature] = {}
        for c in candidates:
            tid = c.feature_identity.feature_type_id
            if tid in seen:
                continue
            prov = FeatureProvenance(
                feature_identity=c.feature_identity,
                source_observation_ids=c.source_observation_ids,
                computed_at_question_index=c.computed_at_question_index,
                feature_engine_version=feature_engine_version,
                updater_id=c.updater_id,
            )
            quality = FeatureQuality(
                confidence=FeatureConfidence(value=c.candidate_confidence),
                stability=FeatureStability(state="emerging"),
                maturity=FeatureMaturity.from_observation_count(
                    max(1, len(c.source_observation_ids))
                ),
            )
            seen[tid] = ProfileFeature(
                feature_identity=c.feature_identity,
                value=c.candidate_value,
                quality=quality,
                provenance=prov,
                computed_at_question_index=c.computed_at_question_index,
                candidate_identity_id=candidate_identity_id,
            )
        return list(seen.values())


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_signal(
    question_index: int = 0,
    session_id: str = "sess-001",
    strength: float = 0.8,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=question_index,
        timestamp_question_index=question_index,
        question_area="algorithms",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.POSITIVE,
        signal_type=EvidenceType.REPEATED_STRENGTH,
        strength=strength,
        source=EvidenceSource.EVALUATION,
    )


def make_candidate(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
    confidence: float = 0.8,
    question_index: int = 0,
    updater_id: str = "stub-updater",
) -> FeatureCandidate:
    return FeatureCandidate(
        feature_identity=FeatureIdentity.for_type(feature_type),
        candidate_value=value,
        candidate_confidence=confidence,
        source_observation_ids=(str(uuid.uuid4()),),
        computed_at_question_index=question_index,
        updater_id=updater_id,
    )


def make_registry(*rules: ObservationRule) -> ObservationRuleRegistry:
    registry = ObservationRuleRegistry()
    for rule in rules:
        registry.register(rule)
    registry.freeze()
    return registry


def make_pipeline(
    session_id: str = "sess-001",
    rules: list[ObservationRule] | None = None,
    candidates: list[FeatureCandidate] | None = None,
    configuration: KnowledgePipelineConfiguration | None = None,
) -> tuple[KnowledgePipeline, InMemoryObservationStore]:
    store = InMemoryObservationStore(session_id=session_id)
    registry = make_registry(*(rules or [AlwaysMatchRule()]))
    extractor = ObservationExtractor(registry=registry, store=store)
    query_engine = ObservationStoreQueryEngine(store=store)
    updater = StubUpdater(candidates=candidates or [make_candidate()])
    feature_engine = FeatureEngine(
        updaters=[updater],
        composer=PassthroughComposer(),
    )
    pipeline = KnowledgePipeline(
        extractor=extractor,
        store=store,
        query_engine=query_engine,
        feature_engine=feature_engine,
        configuration=configuration,
    )
    return pipeline, store


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session_id() -> str:
    return "sess-001"


@pytest.fixture
def candidate_id() -> str:
    return "cand-001"


@pytest.fixture
def signal(session_id: str) -> EvidenceSignal:
    return make_signal(question_index=0, session_id=session_id)


@pytest.fixture
def pipeline_and_store(session_id: str):
    return make_pipeline(session_id=session_id)


@pytest.fixture
def pipeline(pipeline_and_store):
    return pipeline_and_store[0]


@pytest.fixture
def store(session_id: str) -> InMemoryObservationStore:
    return InMemoryObservationStore(session_id=session_id)
