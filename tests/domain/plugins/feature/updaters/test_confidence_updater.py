# tests/domain/plugins/feature/updaters/test_confidence_updater.py

import pytest

from domain.contracts.observation.observation_type import ObservationType
from domain.plugins.feature.updaters.confidence_feature_updater import ConfidenceFeatureUpdater
from tests.domain.plugins.feature.updaters.conftest import make_obs

UPDATER = ConfidenceFeatureUpdater()


# --- Contract properties ---

def test_updater_id():
    assert UPDATER.updater_id == "confidence_updater"


def test_invocation_order():
    assert UPDATER.invocation_order == 30


def test_observation_type_set():
    expected = {
        "confidence_well_calibrated", "confidence_overconfident",
        "confidence_underconfident", "confidence_unstable",
        "confidence_saturated", "confidence_drop",
    }
    assert UPDATER.observation_type_set == expected


def test_feature_identity_set():
    assert UPDATER.feature_identity_set == {"confidence_feature"}


# --- Empty ---

def test_empty_returns_empty():
    assert UPDATER.produce([]) == []


def test_non_obs_returns_empty():
    assert UPDATER.produce(["x", 1]) == []


# --- Candidate structure ---

def test_returns_one_candidate():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    assert len(UPDATER.produce(obs)) == 1


def test_updater_id_in_candidate():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    assert UPDATER.produce(obs)[0].updater_id == "confidence_updater"


def test_feature_type_id():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    assert UPDATER.produce(obs)[0].feature_identity.feature_type_id == "confidence_feature"


def test_candidate_value_nonempty():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    assert UPDATER.produce(obs)[0].candidate_value != ""


def test_source_ids_nonempty():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    assert len(UPDATER.produce(obs)[0].source_observation_ids) >= 1


def test_confidence_in_range():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert 0.0 <= c.candidate_confidence <= 1.0


# --- CALIBRATED logic ---

def test_all_calibrated_gives_calibrated():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "CALIBRATED"


def test_dominant_calibrated_gives_calibrated():
    obs = [
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.9),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.9),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.9),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT, confidence=0.3),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "CALIBRATED"


# --- OVERCONFIDENT logic ---

def test_all_overconfident_gives_overconfident():
    obs = [make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "OVERCONFIDENT"


def test_dominant_overconfident():
    obs = [
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT, confidence=0.9),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT, confidence=0.9),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.2),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "OVERCONFIDENT"


# --- UNDERCONFIDENT logic ---

def test_all_underconfident_gives_underconfident():
    obs = [make_obs(ObservationType.CONFIDENCE_UNDERCONFIDENT) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "UNDERCONFIDENT"


# --- UNSTABLE logic ---

def test_all_unstable_gives_unstable():
    obs = [make_obs(ObservationType.CONFIDENCE_UNSTABLE) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "UNSTABLE"


def test_all_drop_gives_unstable():
    obs = [make_obs(ObservationType.CONFIDENCE_DROP) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "UNSTABLE"


def test_all_saturated_gives_unstable():
    obs = [make_obs(ObservationType.CONFIDENCE_SATURATED) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "UNSTABLE"


def test_dominant_unstable_signals():
    obs = [
        make_obs(ObservationType.CONFIDENCE_UNSTABLE, confidence=0.9),
        make_obs(ObservationType.CONFIDENCE_DROP, confidence=0.9),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.1),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "UNSTABLE"


# --- DEVELOPING logic (mixed) ---

def test_mixed_gives_developing():
    obs = [
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT),
        make_obs(ObservationType.CONFIDENCE_UNDERCONFIDENT),
        make_obs(ObservationType.CONFIDENCE_UNSTABLE),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "DEVELOPING"


# --- Determinism ---

def test_same_obs_same_result():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED) for _ in range(3)]
    r1 = UPDATER.produce(obs)
    r2 = UPDATER.produce(obs)
    assert r1[0].candidate_value == r2[0].candidate_value
    assert r1[0].candidate_confidence == r2[0].candidate_confidence


def test_stateless():
    obs1 = [make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT) for _ in range(5)]
    obs2 = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED) for _ in range(5)]
    UPDATER.produce(obs1)
    r2 = UPDATER.produce(obs2)
    assert r2[0].candidate_value == "CALIBRATED"


# --- Single observation ---

def test_single_well_calibrated():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value in ("CALIBRATED", "OVERCONFIDENT", "UNDERCONFIDENT", "UNSTABLE", "DEVELOPING")


# --- Source IDs ---

def test_all_obs_in_source_ids():
    obs = [
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT),
    ]
    c = UPDATER.produce(obs)[0]
    assert set(c.source_observation_ids) == {str(o.id) for o in obs}


# --- Question index ---

def test_max_question_index():
    obs = [
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, question_index=3),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT, question_index=8),
    ]
    assert UPDATER.produce(obs)[0].computed_at_question_index == 8


# --- Confidence bounds ---

def test_confidence_not_above_1():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED) for _ in range(30)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence <= 1.0


def test_confidence_not_below_0():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.01)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence >= 0.0


# --- Schema / language ---

def test_schema_version():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    assert UPDATER.produce(obs)[0].schema_version == "1.0"


def test_no_language_context():
    obs = [make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED)]
    assert UPDATER.produce(obs)[0].language_context is None


# --- Weight effects ---

def test_weight_affects_dominance():
    obs = [
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.9, weight=0.1),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT, confidence=0.9, weight=1.0),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT, confidence=0.9, weight=1.0),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "OVERCONFIDENT"


# --- High-confidence signals dominate ---

def test_high_confidence_calibrated_wins():
    obs = [
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.99),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, confidence=0.99),
        make_obs(ObservationType.CONFIDENCE_OVERCONFIDENT, confidence=0.1),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "CALIBRATED"
