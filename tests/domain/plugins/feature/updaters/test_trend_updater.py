# tests/domain/plugins/feature/updaters/test_trend_updater.py

import pytest

from domain.contracts.observation.observation_type import ObservationType
from domain.plugins.feature.updaters.trend_feature_updater import TrendFeatureUpdater
from tests.domain.plugins.feature.updaters.conftest import make_obs

UPDATER = TrendFeatureUpdater()


# --- Contract properties ---

def test_updater_id():
    assert UPDATER.updater_id == "trend_updater"


def test_invocation_order():
    assert UPDATER.invocation_order == 50


def test_observation_type_set():
    expected = {
        "performance_improving", "performance_declining",
        "performance_stable", "behavioral_growth", "behavioral_plateau",
    }
    assert UPDATER.observation_type_set == expected


def test_feature_identity_set():
    assert UPDATER.feature_identity_set == {"trend_feature"}


# --- Empty / insufficient ---

def test_empty_returns_empty():
    assert UPDATER.produce([]) == []


def test_single_obs_returns_empty():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING)]
    assert UPDATER.produce(obs) == []


def test_non_obs_returns_empty():
    assert UPDATER.produce(["x", None]) == []


def test_two_obs_returns_candidate():
    obs = [
        make_obs(ObservationType.PERFORMANCE_IMPROVING),
        make_obs(ObservationType.PERFORMANCE_IMPROVING),
    ]
    assert len(UPDATER.produce(obs)) == 1


# --- Candidate structure ---

def test_updater_id_in_candidate():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(3)]
    assert UPDATER.produce(obs)[0].updater_id == "trend_updater"


def test_feature_type_id():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(3)]
    assert UPDATER.produce(obs)[0].feature_identity.feature_type_id == "trend_feature"


def test_candidate_value_nonempty():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(3)]
    assert UPDATER.produce(obs)[0].candidate_value != ""


def test_source_ids_nonempty():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(3)]
    assert len(UPDATER.produce(obs)[0].source_observation_ids) >= 1


def test_confidence_in_range():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert 0.0 <= c.candidate_confidence <= 1.0


# --- IMPROVING logic ---

def test_all_improving_gives_improving():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "IMPROVING"


def test_all_behavioral_growth_gives_improving():
    obs = [make_obs(ObservationType.BEHAVIORAL_GROWTH) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "IMPROVING"


def test_mixed_improving_signals():
    obs = [
        make_obs(ObservationType.PERFORMANCE_IMPROVING),
        make_obs(ObservationType.BEHAVIORAL_GROWTH),
        make_obs(ObservationType.BEHAVIORAL_GROWTH),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "IMPROVING"


# --- DECLINING logic ---

def test_all_declining_gives_declining():
    obs = [make_obs(ObservationType.PERFORMANCE_DECLINING) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "DECLINING"


def test_dominant_declining():
    obs = [
        make_obs(ObservationType.PERFORMANCE_DECLINING, confidence=0.9),
        make_obs(ObservationType.PERFORMANCE_DECLINING, confidence=0.9),
        make_obs(ObservationType.PERFORMANCE_STABLE, confidence=0.3),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "DECLINING"


# --- STABLE logic ---

def test_all_stable_gives_stable():
    obs = [make_obs(ObservationType.PERFORMANCE_STABLE) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "STABLE"


# --- PLATEAU logic ---

def test_all_plateau_gives_plateau():
    obs = [make_obs(ObservationType.BEHAVIORAL_PLATEAU) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "PLATEAU"


# --- Determinism ---

def test_same_obs_same_result():
    obs = [
        make_obs(ObservationType.PERFORMANCE_IMPROVING),
        make_obs(ObservationType.PERFORMANCE_IMPROVING),
    ]
    r1 = UPDATER.produce(obs)
    r2 = UPDATER.produce(obs)
    assert r1[0].candidate_value == r2[0].candidate_value
    assert r1[0].candidate_confidence == r2[0].candidate_confidence


def test_stateless():
    obs1 = [make_obs(ObservationType.PERFORMANCE_DECLINING) for _ in range(5)]
    obs2 = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(5)]
    UPDATER.produce(obs1)
    r2 = UPDATER.produce(obs2)
    assert r2[0].candidate_value == "IMPROVING"


# --- Source IDs ---

def test_all_obs_in_source_ids():
    obs = [
        make_obs(ObservationType.PERFORMANCE_IMPROVING),
        make_obs(ObservationType.BEHAVIORAL_GROWTH),
    ]
    c = UPDATER.produce(obs)[0]
    assert set(c.source_observation_ids) == {str(o.id) for o in obs}


# --- Question index ---

def test_max_question_index():
    obs = [
        make_obs(ObservationType.PERFORMANCE_IMPROVING, question_index=2),
        make_obs(ObservationType.PERFORMANCE_IMPROVING, question_index=10),
    ]
    assert UPDATER.produce(obs)[0].computed_at_question_index == 10


# --- Confidence bounds ---

def test_confidence_not_above_1():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(30)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence <= 1.0


def test_confidence_not_below_0():
    obs = [
        make_obs(ObservationType.PERFORMANCE_IMPROVING, confidence=0.01),
        make_obs(ObservationType.PERFORMANCE_IMPROVING, confidence=0.01),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence >= 0.0


# --- Schema / language ---

def test_schema_version():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(3)]
    assert UPDATER.produce(obs)[0].schema_version == "1.0"


def test_no_language_context():
    obs = [make_obs(ObservationType.PERFORMANCE_IMPROVING) for _ in range(3)]
    assert UPDATER.produce(obs)[0].language_context is None
