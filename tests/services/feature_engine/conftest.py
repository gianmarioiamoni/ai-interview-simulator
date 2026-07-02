# tests/services/feature_engine/conftest.py
# Shared test fixtures for FeatureEngine test suite

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_composer import FeatureComposer
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_merge_policy import FeatureMergePolicy
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_replacement_policy import FeatureReplacementPolicy
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from services.feature_engine.feature_engine_context import FeatureEngineContext


# ---------------------------------------------------------------------------
# Minimal concrete FeatureUpdater for testing
# ---------------------------------------------------------------------------


class StubUpdater(FeatureUpdater):
    """Configurable stub that produces a fixed list of FeatureCandidates."""

    def __init__(
        self,
        updater_id: str = "stub_updater",
        invocation_order: int = 1,
        candidates_to_produce: list[FeatureCandidate] | None = None,
        observation_type_set: frozenset[str] | None = None,
        feature_identity_set: frozenset[str] | None = None,
    ) -> None:
        self._updater_id = updater_id
        self._invocation_order = invocation_order
        self._candidates = candidates_to_produce or []
        self._obs_type_set = observation_type_set or frozenset()
        self._feat_id_set = feature_identity_set or frozenset(
            c.feature_identity.feature_type_id for c in self._candidates
        )
        self.produce_call_count = 0
        self.last_observations_received: list[Any] = []

    @property
    def updater_id(self) -> str:
        return self._updater_id

    @property
    def observation_type_set(self) -> frozenset[str]:
        return self._obs_type_set

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return self._feat_id_set

    @property
    def invocation_order(self) -> int:
        return self._invocation_order

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        self.produce_call_count += 1
        self.last_observations_received = list(observations)
        return list(self._candidates)


class ErrorUpdater(FeatureUpdater):
    """Updater that always raises an exception."""

    @property
    def updater_id(self) -> str:
        return "error_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset()

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset()

    @property
    def invocation_order(self) -> int:
        return 99

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        raise RuntimeError("Simulated updater failure")


class EmptyUpdater(FeatureUpdater):
    """Updater that always returns no candidates."""

    def __init__(self, order: int = 1) -> None:
        self._order = order

    @property
    def updater_id(self) -> str:
        return "empty_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset()

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset()

    @property
    def invocation_order(self) -> int:
        return self._order

    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        return []


# ---------------------------------------------------------------------------
# Minimal concrete FeatureComposer for testing
# ---------------------------------------------------------------------------


class PassthroughComposer(FeatureComposer):
    """Composer that turns each candidate directly into a ProfileFeature."""

    def compose(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> list[ProfileFeature]:
        seen: dict[str, ProfileFeature] = {}
        for c in candidates:
            type_id = c.feature_identity.feature_type_id
            if type_id in seen:
                continue  # first-wins for testing simplicity
            prov = FeatureProvenance(
                feature_identity=c.feature_identity,
                source_observation_ids=c.source_observation_ids,
                computed_at_question_index=c.computed_at_question_index,
                feature_engine_version=feature_engine_version,
                updater_id=c.updater_id,
                language_context=c.language_context,
            )
            quality = FeatureQuality(
                confidence=FeatureConfidence(value=c.candidate_confidence),
                stability=FeatureStability(state="emerging"),
                maturity=FeatureMaturity.from_observation_count(
                    max(1, len(c.source_observation_ids))
                ),
            )
            seen[type_id] = ProfileFeature(
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


def make_observation(
    obs_type: ObservationType = ObservationType.REASONING_DEPTH_HIGH,
    question_index: int = 0,
    session_id: str = "sess-001",
    confidence: float = 0.8,
    status: ObservationStatus = ObservationStatus.ACTIVE,
) -> Observation:
    return Observation(
        observation_type=obs_type,
        status=status,
        metadata=ObservationMetadata(
            question_index=question_index,
            session_id=session_id,
            origin=ObservationOrigin.EVIDENCE_SIGNAL,
            source_ref="sig-001",
        ),
        description="Test observation",
        confidence=confidence,
    )


def make_snapshot(
    observations: list[Observation] | None = None,
    session_id: str = "sess-001",
) -> ObservationSnapshot:
    obs = observations or []
    return ObservationSnapshot.from_observations(session_id, obs)


def make_context(
    snapshot: ObservationSnapshot | None = None,
    session_id: str = "sess-001",
    candidate_id: str = "cand-001",
    question_index: int = 0,
    is_replay: bool = False,
) -> FeatureEngineContext:
    snap = snapshot or make_snapshot(session_id=session_id)
    return FeatureEngineContext(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        current_question_index=question_index,
        snapshot=snap,
        is_replay=is_replay,
    )


def make_candidate(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
    confidence: float = 0.8,
    obs_ids: tuple[str, ...] = ("obs-1",),
    question_index: int = 0,
    updater_id: str = "stub_updater",
) -> FeatureCandidate:
    return FeatureCandidate(
        feature_identity=FeatureIdentity.for_type(feature_type),
        candidate_value=value,
        candidate_confidence=confidence,
        source_observation_ids=obs_ids,
        computed_at_question_index=question_index,
        updater_id=updater_id,
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_updater() -> StubUpdater:
    return StubUpdater(
        candidates_to_produce=[make_candidate(FeatureType.REASONING, "HIGH")],
        observation_type_set=frozenset({"reasoning_depth_high"}),
        feature_identity_set=frozenset({"reasoning_feature"}),
    )


@pytest.fixture
def passthrough_composer() -> PassthroughComposer:
    return PassthroughComposer()


@pytest.fixture
def basic_context() -> FeatureEngineContext:
    return make_context()


@pytest.fixture
def context_with_observations() -> FeatureEngineContext:
    obs = [make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=0)]
    snap = make_snapshot(obs)
    return make_context(snapshot=snap)
