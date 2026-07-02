# tests/domain/plugins/feature/updaters/test_coverage_updater.py

import pytest

from domain.contracts.observation.observation_type import ObservationType
from domain.plugins.feature.updaters.coverage_feature_updater import CoverageFeatureUpdater
from tests.domain.plugins.feature.updaters.conftest import make_obs

UPDATER = CoverageFeatureUpdater()


# --- Contract properties ---

def test_updater_id():
    assert UPDATER.updater_id == "coverage_updater"


def test_invocation_order():
    assert UPDATER.invocation_order == 40


def test_observation_type_set():
    expected = {
        "knowledge_demonstrated", "knowledge_gap",
        "knowledge_cross_area_consistent", "knowledge_cross_area_contradictory",
    }
    assert UPDATER.observation_type_set == expected


def test_feature_identity_set():
    assert UPDATER.feature_identity_set == {"coverage_feature"}


# --- Empty / insufficient ---

def test_empty_returns_empty():
    assert UPDATER.produce([]) == []


def test_single_obs_returns_empty():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED)]
    assert UPDATER.produce(obs) == []


def test_non_obs_returns_empty():
    assert UPDATER.produce(["x"]) == []


def test_two_obs_returns_candidate():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED),
    ]
    assert len(UPDATER.produce(obs)) == 1


# --- Candidate structure ---

def test_updater_id_in_candidate():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(3)]
    assert UPDATER.produce(obs)[0].updater_id == "coverage_updater"


def test_feature_type_id():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(3)]
    assert UPDATER.produce(obs)[0].feature_identity.feature_type_id == "coverage_feature"


def test_candidate_value_nonempty():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(3)]
    assert UPDATER.produce(obs)[0].candidate_value != ""


def test_source_ids_nonempty():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(3)]
    assert len(UPDATER.produce(obs)[0].source_observation_ids) >= 1


def test_confidence_in_range():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert 0.0 <= c.candidate_confidence <= 1.0


# --- BROAD logic ---

def test_all_demonstrated_gives_broad():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "BROAD"


def test_all_consistent_gives_broad():
    obs = [make_obs(ObservationType.KNOWLEDGE_CROSS_AREA_CONSISTENT) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "BROAD"


def test_mixed_broad_signals():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED),
        make_obs(ObservationType.KNOWLEDGE_CROSS_AREA_CONSISTENT),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "BROAD"


# --- NARROW logic ---

def test_all_gap_gives_narrow():
    obs = [make_obs(ObservationType.KNOWLEDGE_GAP) for _ in range(5)]
    assert UPDATER.produce(obs)[0].candidate_value == "NARROW"


def test_dominant_gap_gives_narrow():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_GAP, confidence=0.9),
        make_obs(ObservationType.KNOWLEDGE_GAP, confidence=0.9),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, confidence=0.2),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "NARROW"


# --- MIXED logic ---

def test_high_contradictory_gives_mixed():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_CROSS_AREA_CONTRADICTORY, confidence=0.9),
        make_obs(ObservationType.KNOWLEDGE_CROSS_AREA_CONTRADICTORY, confidence=0.9),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, confidence=0.2),
    ]
    assert UPDATER.produce(obs)[0].candidate_value == "MIXED"


def test_all_contradictory_gives_mixed():
    obs = [make_obs(ObservationType.KNOWLEDGE_CROSS_AREA_CONTRADICTORY) for _ in range(4)]
    assert UPDATER.produce(obs)[0].candidate_value == "MIXED"


# --- Determinism ---

def test_same_obs_same_result():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED),
        make_obs(ObservationType.KNOWLEDGE_GAP),
    ]
    r1 = UPDATER.produce(obs)
    r2 = UPDATER.produce(obs)
    assert r1[0].candidate_value == r2[0].candidate_value
    assert r1[0].candidate_confidence == r2[0].candidate_confidence


def test_stateless():
    obs1 = [make_obs(ObservationType.KNOWLEDGE_GAP) for _ in range(5)]
    obs2 = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(5)]
    UPDATER.produce(obs1)
    r2 = UPDATER.produce(obs2)
    assert r2[0].candidate_value == "BROAD"


# --- Source IDs ---

def test_all_obs_in_source_ids():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED),
        make_obs(ObservationType.KNOWLEDGE_GAP),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED),
    ]
    c = UPDATER.produce(obs)[0]
    assert set(c.source_observation_ids) == {str(o.id) for o in obs}


# --- Question index ---

def test_max_question_index():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, question_index=1),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, question_index=6),
    ]
    assert UPDATER.produce(obs)[0].computed_at_question_index == 6


# --- Confidence bounds ---

def test_confidence_not_above_1():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(30)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence <= 1.0


def test_confidence_not_below_0():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, confidence=0.01),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, confidence=0.01),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence >= 0.0


# --- Schema / language ---

def test_schema_version():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(3)]
    assert UPDATER.produce(obs)[0].schema_version == "1.0"


def test_no_language_context():
    obs = [make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED) for _ in range(3)]
    assert UPDATER.produce(obs)[0].language_context is None
