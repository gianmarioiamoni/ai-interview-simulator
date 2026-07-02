# tests/domain/plugins/feature/updaters/conftest.py

import pytest

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_type import ObservationType


def make_obs(
    obs_type: ObservationType,
    confidence: float = 0.8,
    weight: float = 1.0,
    question_index: int = 0,
    session_id: str = "test-session",
) -> Observation:
    metadata = ObservationMetadata(
        question_index=question_index,
        session_id=session_id,
        origin=ObservationOrigin.REPLAY,
    )
    return Observation(
        observation_type=obs_type,
        metadata=metadata,
        description="test observation",
        confidence=confidence,
        weight=weight,
    )


@pytest.fixture
def make_observation():
    return make_obs
