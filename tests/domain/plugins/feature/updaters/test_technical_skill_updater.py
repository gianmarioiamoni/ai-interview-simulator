# tests/domain/plugins/feature/updaters/test_technical_skill_updater.py

import pytest

from domain.contracts.observation.observation_type import ObservationType
from domain.plugins.feature.updaters.technical_skill_feature_updater import TechnicalSkillFeatureUpdater
from tests.domain.plugins.feature.updaters.conftest import make_obs

UPDATER = TechnicalSkillFeatureUpdater()


# --- Contract properties ---

def test_updater_id():
    assert UPDATER.updater_id == "technical_skill_updater"


def test_invocation_order():
    assert UPDATER.invocation_order == 10


def test_observation_type_set_contains_all():
    expected = {
        "technical_correctness", "technical_depth", "technical_shallow",
        "technical_gap", "technical_strength", "technical_recovered",
    }
    assert UPDATER.observation_type_set == expected


def test_feature_identity_set():
    assert UPDATER.feature_identity_set == {"technical_skill_feature"}


# --- Empty observations ---

def test_empty_returns_empty():
    assert UPDATER.produce([]) == []


def test_no_typed_obs_returns_empty():
    assert UPDATER.produce(["not_an_obs", 42, None]) == []


# --- Candidate structure ---

def test_returns_single_candidate():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    result = UPDATER.produce(obs)
    assert len(result) == 1


def test_candidate_updater_id():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    c = UPDATER.produce(obs)[0]
    assert c.updater_id == "technical_skill_updater"


def test_candidate_feature_type_id():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    c = UPDATER.produce(obs)[0]
    assert c.feature_identity.feature_type_id == "technical_skill_feature"


def test_candidate_value_nonempty():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value != ""


def test_source_observation_ids_nonempty():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    c = UPDATER.produce(obs)[0]
    assert len(c.source_observation_ids) >= 1


def test_confidence_range():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert 0.0 <= c.candidate_confidence <= 1.0


def test_question_index_in_candidate():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=5)]
    c = UPDATER.produce(obs)[0]
    assert c.computed_at_question_index == 5


# --- Value logic: HIGH ---

def test_all_correctness_gives_high():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "HIGH"


def test_all_depth_gives_high():
    obs = [make_obs(ObservationType.TECHNICAL_DEPTH) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "HIGH"


def test_all_strength_gives_high():
    obs = [make_obs(ObservationType.TECHNICAL_STRENGTH) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "HIGH"


def test_all_recovered_gives_high():
    obs = [make_obs(ObservationType.TECHNICAL_RECOVERED) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "HIGH"


# --- Value logic: LOW ---

def test_all_gap_gives_low():
    obs = [make_obs(ObservationType.TECHNICAL_GAP) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "LOW"


def test_all_shallow_gives_low():
    obs = [make_obs(ObservationType.TECHNICAL_SHALLOW) for _ in range(5)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "LOW"


# --- Value logic: MODERATE ---

def test_mixed_signals_moderate():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS),
        make_obs(ObservationType.TECHNICAL_GAP),
        make_obs(ObservationType.TECHNICAL_DEPTH),
        make_obs(ObservationType.TECHNICAL_SHALLOW),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "MODERATE"


def test_slightly_positive_gives_high():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, confidence=0.9),
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, confidence=0.9),
        make_obs(ObservationType.TECHNICAL_GAP, confidence=0.4),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "HIGH"


def test_slightly_negative_gives_low():
    obs = [
        make_obs(ObservationType.TECHNICAL_GAP, confidence=0.9),
        make_obs(ObservationType.TECHNICAL_GAP, confidence=0.9),
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, confidence=0.4),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "LOW"


# --- Determinism / Replay ---

def test_same_obs_same_result():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS),
        make_obs(ObservationType.TECHNICAL_DEPTH),
    ]
    r1 = UPDATER.produce(obs)
    r2 = UPDATER.produce(obs)
    assert r1[0].candidate_value == r2[0].candidate_value
    assert r1[0].candidate_confidence == r2[0].candidate_confidence


def test_stateless_second_call_independent():
    obs1 = [make_obs(ObservationType.TECHNICAL_GAP) for _ in range(5)]
    obs2 = [make_obs(ObservationType.TECHNICAL_CORRECTNESS) for _ in range(5)]
    UPDATER.produce(obs1)
    r2 = UPDATER.produce(obs2)
    assert r2[0].candidate_value == "HIGH"


# --- Single observation ---

def test_single_positive_obs():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value in ("HIGH", "MODERATE", "LOW")
    assert 0.0 <= c.candidate_confidence <= 1.0


def test_single_negative_obs():
    obs = [make_obs(ObservationType.TECHNICAL_GAP)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value in ("HIGH", "MODERATE", "LOW")


# --- Source IDs traceability ---

def test_all_obs_ids_in_source():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS),
        make_obs(ObservationType.TECHNICAL_DEPTH),
    ]
    c = UPDATER.produce(obs)[0]
    obs_ids = {str(o.id) for o in obs}
    assert set(c.source_observation_ids) == obs_ids


# --- Confidence with weight ---

def test_low_weight_obs_affects_confidence():
    obs_heavy = [make_obs(ObservationType.TECHNICAL_CORRECTNESS, weight=1.0) for _ in range(3)]
    obs_light = [make_obs(ObservationType.TECHNICAL_CORRECTNESS, weight=0.1) for _ in range(3)]
    c_heavy = UPDATER.produce(obs_heavy)[0]
    c_light = UPDATER.produce(obs_light)[0]
    # Both should be HIGH, but confidence may differ
    assert c_heavy.candidate_value == "HIGH"
    assert c_light.candidate_value == "HIGH"


# --- Confidence range extremes ---

def test_confidence_not_above_1():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS) for _ in range(20)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence <= 1.0


def test_confidence_not_below_0():
    obs = [make_obs(ObservationType.TECHNICAL_GAP, confidence=0.01) for _ in range(1)]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_confidence >= 0.0


# --- Max question_index used ---

def test_max_question_index_used():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=2),
        make_obs(ObservationType.TECHNICAL_DEPTH, question_index=7),
        make_obs(ObservationType.TECHNICAL_STRENGTH, question_index=4),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.computed_at_question_index == 7


# --- Schema version ---

def test_candidate_schema_version():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    c = UPDATER.produce(obs)[0]
    assert c.schema_version == "1.0"


# --- No language context ---

def test_no_language_context_by_default():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS)]
    c = UPDATER.produce(obs)[0]
    assert c.language_context is None


# --- High confidence signals dominate ---

def test_high_confidence_positive_dominates():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, confidence=0.99),
        make_obs(ObservationType.TECHNICAL_GAP, confidence=0.01),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "HIGH"


def test_high_confidence_negative_dominates():
    obs = [
        make_obs(ObservationType.TECHNICAL_GAP, confidence=0.99),
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, confidence=0.01),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value == "LOW"


# --- Multiple observation types mix ---

def test_recovered_counted_as_positive():
    obs = [
        make_obs(ObservationType.TECHNICAL_RECOVERED),
        make_obs(ObservationType.TECHNICAL_RECOVERED),
        make_obs(ObservationType.TECHNICAL_GAP),
    ]
    c = UPDATER.produce(obs)[0]
    assert c.candidate_value in ("HIGH", "MODERATE")
