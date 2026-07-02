# tests/domain/plugins/feature/updaters/test_reasoning_updater.py

import pytest

from domain.contracts.observation.observation_type import ObservationType
from domain.plugins.feature.updaters.reasoning_feature_updater import ReasoningFeatureUpdater
from tests.domain.plugins.feature.updaters.conftest import make_obs

UPDATER = ReasoningFeatureUpdater()


# --- Contract properties ---

def test_updater_id():
    assert UPDATER.updater_id == "reasoning_updater"


def test_invocation_order():
    assert UPDATER.invocation_order == 20


def test_observation_type_set():
    expected = {
        "reasoning_depth_high", "reasoning_depth_low",
        "reasoning_improving", "reasoning_stagnating", "reasoning_contradictory",
    }
    assert UPDATER.observation_type_set == expected


def test_feature_identity_set():
    assert UPDATER.feature_identity_set == {"reasoning_feature"}


# --- Empty ---

def test_empty_returns_empty():
    assert UPDATER.produce([]) == []


def test_non_obs_returns_empty():
    assert UPDATER.produce(["x", None]) == []


# --- Candidate structure ---

def test_returns_one_candidate():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    assert len(UPDATER.produce(obs)) == 1


def test_updater_id_in_candidate():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    assert UPDATER.produce(obs)[0].updater_id == "reasoning_updater"


def test_feature_type_id_in_candidate():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    assert UPDATER.produce(obs)[0].feature_identity.feature_type_id == "reasoning_feature"


def test_candidate_value_nonempty():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    assert UPDATER.produce(obs)[0].candidate_value != ""


def test_source_ids_nonempty():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    assert len(UPDATER.produce(obs)[0].source_observation_ids) >= 1


def test_confidence_in_range():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH) for _ in range(3)]
    c = UPDATER.produce(obs)[0]
    assert 0.0 <= c.candidate_confidence <= 1.0


# --- DEEP logic ---

def test_all_depth_high_gives_deep():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "DEEP"


def test_all_improving_gives_deep():
    obs = [make_obs(ObservationType.REASONING_IMPROVING) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "DEEP"


def test_mixed_deep_signals():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_HIGH),
        make_obs(ObservationType.REASONING_IMPROVING),
        make_obs(ObservationType.REASONING_IMPROVING),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "DEEP"


# --- SHALLOW logic ---

def test_all_depth_low_gives_shallow():
    obs = [make_obs(ObservationType.REASONING_DEPTH_LOW) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "SHALLOW"


def test_all_stagnating_gives_shallow():
    obs = [make_obs(ObservationType.REASONING_STAGNATING) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "SHALLOW"


# --- DEVELOPING logic ---

def test_mixed_gives_developing():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_HIGH),
        make_obs(ObservationType.REASONING_DEPTH_LOW),
        make_obs(ObservationType.REASONING_IMPROVING),
        make_obs(ObservationType.REASONING_STAGNATING),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "DEVELOPING"


def test_only_contradictory_gives_developing():
    obs = [make_obs(ObservationType.REASONING_CONTRADICTORY) for _ in range(3)]
    assert UPDATER.produce(obs)[0].candidate_value == "DEVELOPING"


# --- Determinism ---

def test_same_obs_same_result():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_HIGH),
        make_obs(ObservationType.REASONING_IMPROVING),
    ]
    r1 = UPDATER.produce(obs)
    r2 = UPDATER.produce(obs)
    assert r1[0].candidate_value == r2[0].candidate_value
    assert r1[0].candidate_confidence == r2[0].candidate_confidence


def test_stateless():
    obs1 = [make_obs(ObservationType.REASONING_DEPTH_LOW) for _ in range(5)]
    obs2 = [make_obs(ObservationType.REASONING_DEPTH_HIGH) for _ in range(5)]
    UPDATER.produce(obs1)
    r2 = UPDATER.produce(obs2)
    assert r2[0].candidate_value == "DEEP"


# --- Single observation edge cases ---

def test_single_depth_high():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value in ("DEEP", "DEVELOPING", "SHALLOW")


def test_single_contradictory():
    obs = [make_obs(ObservationType.REASONING_CONTRADICTORY)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "DEVELOPING"


# --- Source IDs traceability ---

def test_all_obs_in_source_ids():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_HIGH),
        make_obs(ObservationType.REASONING_IMPROVING),
    ]
    c = UPDATER.produce(obs)[0]
    assert set(c.source_observation_ids) == {str(o.id) for o in obs}


# --- Question index ---

def test_max_question_index():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_HIGH, question_index=1),
        make_obs(ObservationType.REASONING_IMPROVING, question_index=9),
    ]
    assert UPDATER.produce(obs)[0].computed_at_question_index == 9


# --- Confidence not exceeding bounds ---

def test_confidence_not_above_1():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH) for _ in range(30)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence <= 1.0


def test_confidence_not_below_0():
    obs = [make_obs(ObservationType.REASONING_DEPTH_LOW, confidence=0.01)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence >= 0.0


# --- High confidence signals dominate ---

def test_high_confidence_deep_dominates():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_HIGH, confidence=0.99),
        make_obs(ObservationType.REASONING_DEPTH_LOW, confidence=0.01),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "DEEP"


def test_high_confidence_shallow_dominates():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_LOW, confidence=0.99),
        make_obs(ObservationType.REASONING_DEPTH_HIGH, confidence=0.01),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "SHALLOW"


# --- Schema version ---

def test_schema_version():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    assert UPDATER.produce(obs)[0].schema_version == "1.0"


def test_no_language_context():
    obs = [make_obs(ObservationType.REASONING_DEPTH_HIGH)]
    assert UPDATER.produce(obs)[0].language_context is None
