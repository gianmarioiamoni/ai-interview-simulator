# tests/domain/contracts/observation/extraction/conftest.py
# Shared fixtures and builders for extraction layer tests

from __future__ import annotations

import uuid

import pytest

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.extraction.observation_rule_registry import ObservationRuleRegistry
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
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


# ---------------------------------------------------------------------------
# EvidenceSignal builder
# ---------------------------------------------------------------------------

def make_signal(
    question_index: int = 0,
    strength: float = 0.8,
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE,
    signal_type: EvidenceType = EvidenceType.REPEATED_STRENGTH,
    dimension: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    source: EvidenceSource = EvidenceSource.EVALUATION,
    question_area: str = "algorithms",
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=question_index,
        timestamp_question_index=question_index,
        question_area=question_area,
        dimension=dimension,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
        source=source,
    )


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def make_context(
    question_index: int = 0,
    session_id: str = "test-session",
    signals: list[EvidenceSignal] | None = None,
) -> ObservationExtractionContext:
    if signals is None:
        signals = [make_signal(question_index=question_index)]
    return ObservationExtractionContext(
        signals=tuple(signals),
        question_index=question_index,
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# In-memory ObservationStore
# ---------------------------------------------------------------------------

class InMemoryObservationStore(ObservationStore):
    def __init__(self, session_id: str = "test-session") -> None:
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

    def get(self, observation_id: ObservationId) -> Observation | None:
        return self._store.get(observation_id.value)

    def query(self, observation_query: ObservationQuery) -> list[Observation]:
        return list(self._store.values())

    def snapshot(self) -> ObservationSnapshot:
        return ObservationSnapshot.from_observations(self._session_id, list(self._store.values()))


# ---------------------------------------------------------------------------
# Concrete stub rules
# ---------------------------------------------------------------------------

class AlwaysMatchRule(ObservationRule):
    """Rule that always emits one match."""

    def __init__(
        self,
        rule_id: str = "always-match",
        priority: ObservationRulePriority = ObservationRulePriority.NORMAL,
        observation_type: ObservationType = ObservationType.TECHNICAL_CORRECTNESS,
        confidence: float = 0.9,
    ) -> None:
        self._rule_id = rule_id
        self._priority = priority
        self._observation_type = observation_type
        self._confidence = confidence

    @property
    def rule_id(self) -> str:
        return self._rule_id

    @property
    def priority(self) -> ObservationRulePriority:
        return self._priority

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        return [
            ObservationRuleMatch(
                rule_id=self._rule_id,
                observation_type=self._observation_type,
                confidence=self._confidence,
                description="always match rule fired",
            )
        ]


class NeverMatchRule(ObservationRule):
    """Rule that never emits a match."""

    def __init__(
        self,
        rule_id: str = "never-match",
        priority: ObservationRulePriority = ObservationRulePriority.LOW,
    ) -> None:
        self._rule_id = rule_id
        self._priority = priority

    @property
    def rule_id(self) -> str:
        return self._rule_id

    @property
    def priority(self) -> ObservationRulePriority:
        return self._priority

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        return []


class SkipRule(ObservationRule):
    """Rule whose applies_to always returns False."""

    def __init__(self, rule_id: str = "skip-rule") -> None:
        self._rule_id = rule_id

    @property
    def rule_id(self) -> str:
        return self._rule_id

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.NORMAL

    def applies_to(self, context: ObservationExtractionContext) -> bool:
        return False

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        raise AssertionError("evaluate should never be called when applies_to returns False")


class ErrorRule(ObservationRule):
    """Rule that raises during evaluate()."""

    def __init__(self, rule_id: str = "error-rule") -> None:
        self._rule_id = rule_id

    @property
    def rule_id(self) -> str:
        return self._rule_id

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.NORMAL

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        raise RuntimeError("simulated rule failure")


class AppliesErrorRule(ObservationRule):
    """Rule that raises during applies_to()."""

    def __init__(self, rule_id: str = "applies-error-rule") -> None:
        self._rule_id = rule_id

    @property
    def rule_id(self) -> str:
        return self._rule_id

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.NORMAL

    def applies_to(self, context: ObservationExtractionContext) -> bool:
        raise RuntimeError("simulated applies_to failure")

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        return []


class MultiMatchRule(ObservationRule):
    """Rule that emits multiple matches per evaluation."""

    def __init__(
        self,
        rule_id: str = "multi-match",
        matches: list[tuple[ObservationType, float]] | None = None,
    ) -> None:
        self._rule_id = rule_id
        self._matches = matches or [
            (ObservationType.TECHNICAL_CORRECTNESS, 0.9),
            (ObservationType.COMMUNICATION_CLEAR, 0.7),
        ]

    @property
    def rule_id(self) -> str:
        return self._rule_id

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.NORMAL

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        return [
            ObservationRuleMatch(
                rule_id=self._rule_id,
                observation_type=otype,
                confidence=conf,
                description=f"multi-match: {otype.value}",
            )
            for otype, conf in self._matches
        ]


# ---------------------------------------------------------------------------
# Registry + extractor factories
# ---------------------------------------------------------------------------

def make_registry(*rules: ObservationRule) -> ObservationRuleRegistry:
    registry = ObservationRuleRegistry()
    for rule in rules:
        registry.register(rule)
    registry.freeze()
    return registry


def make_extractor(
    *rules: ObservationRule,
    session_id: str = "test-session",
) -> tuple[ObservationExtractor, InMemoryObservationStore]:
    store = InMemoryObservationStore(session_id=session_id)
    registry = make_registry(*rules)
    extractor = ObservationExtractor(registry=registry, store=store)
    return extractor, store


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store() -> InMemoryObservationStore:
    return InMemoryObservationStore()


@pytest.fixture()
def empty_registry() -> ObservationRuleRegistry:
    r = ObservationRuleRegistry()
    r.freeze()
    return r


@pytest.fixture()
def context() -> ObservationExtractionContext:
    return make_context()
