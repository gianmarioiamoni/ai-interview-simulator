# tests/domain/observation/runtime/conftest.py
# Shared fixtures for Observation Runtime tests.

from __future__ import annotations

import pytest

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType


SESSION = "test-session"


def make_obs(
    question_index: int = 0,
    observation_type: ObservationType = ObservationType.TECHNICAL_CORRECTNESS,
    confidence: float = 0.8,
    weight: float = 1.0,
    origin: ObservationOrigin = ObservationOrigin.EVALUATION,
    session_id: str = SESSION,
    status: ObservationStatus = ObservationStatus.ACTIVE,
    tags: frozenset[str] | None = None,
) -> Observation:
    meta = ObservationMetadata(
        question_index=question_index,
        session_id=session_id,
        origin=origin,
        source_ref="src-ref",
    )
    obs = Observation(
        observation_type=observation_type,
        metadata=meta,
        description="test observation",
        confidence=confidence,
        weight=weight,
        tags=tags or frozenset(),
    )
    if status != ObservationStatus.ACTIVE:
        obs = obs.with_status(status)
    return obs


@pytest.fixture()
def three_obs() -> list[Observation]:
    return [
        make_obs(0, ObservationType.TECHNICAL_CORRECTNESS, confidence=0.9),
        make_obs(1, ObservationType.KNOWLEDGE_GAP, confidence=0.5),
        make_obs(2, ObservationType.REASONING_IMPROVING, confidence=0.7),
    ]


@pytest.fixture()
def five_obs() -> list[Observation]:
    return [make_obs(i, confidence=0.1 * (i + 1)) for i in range(5)]
