# tests/domain/contracts/observation/test_observation_type.py

import pytest

from domain.contracts.observation.observation_type import ObservationType


class TestObservationTypeValues:
    def test_is_str_enum(self):
        assert isinstance(ObservationType.TECHNICAL_CORRECTNESS, str)

    def test_technical_correctness_value(self):
        assert ObservationType.TECHNICAL_CORRECTNESS == "technical_correctness"

    def test_technical_depth_value(self):
        assert ObservationType.TECHNICAL_DEPTH == "technical_depth"

    def test_technical_shallow_value(self):
        assert ObservationType.TECHNICAL_SHALLOW == "technical_shallow"

    def test_technical_gap_value(self):
        assert ObservationType.TECHNICAL_GAP == "technical_gap"

    def test_technical_strength_value(self):
        assert ObservationType.TECHNICAL_STRENGTH == "technical_strength"

    def test_technical_recovered_value(self):
        assert ObservationType.TECHNICAL_RECOVERED == "technical_recovered"

    def test_reasoning_depth_high(self):
        assert ObservationType.REASONING_DEPTH_HIGH == "reasoning_depth_high"

    def test_reasoning_depth_low(self):
        assert ObservationType.REASONING_DEPTH_LOW == "reasoning_depth_low"

    def test_reasoning_improving(self):
        assert ObservationType.REASONING_IMPROVING == "reasoning_improving"

    def test_reasoning_stagnating(self):
        assert ObservationType.REASONING_STAGNATING == "reasoning_stagnating"

    def test_reasoning_contradictory(self):
        assert ObservationType.REASONING_CONTRADICTORY == "reasoning_contradictory"

    def test_communication_clear(self):
        assert ObservationType.COMMUNICATION_CLEAR == "communication_clear"

    def test_communication_weak(self):
        assert ObservationType.COMMUNICATION_WEAK == "communication_weak"

    def test_communication_inconsistent(self):
        assert ObservationType.COMMUNICATION_INCONSISTENT == "communication_inconsistent"

    def test_communication_gap(self):
        assert ObservationType.COMMUNICATION_GAP == "communication_gap"

    def test_confidence_well_calibrated(self):
        assert ObservationType.CONFIDENCE_WELL_CALIBRATED == "confidence_well_calibrated"

    def test_confidence_overconfident(self):
        assert ObservationType.CONFIDENCE_OVERCONFIDENT == "confidence_overconfident"

    def test_confidence_underconfident(self):
        assert ObservationType.CONFIDENCE_UNDERCONFIDENT == "confidence_underconfident"

    def test_confidence_unstable(self):
        assert ObservationType.CONFIDENCE_UNSTABLE == "confidence_unstable"

    def test_confidence_saturated(self):
        assert ObservationType.CONFIDENCE_SATURATED == "confidence_saturated"

    def test_confidence_drop(self):
        assert ObservationType.CONFIDENCE_DROP == "confidence_drop"

    def test_leadership_strong(self):
        assert ObservationType.LEADERSHIP_STRONG == "leadership_strong"

    def test_leadership_emerging(self):
        assert ObservationType.LEADERSHIP_EMERGING == "leadership_emerging"

    def test_leadership_absent(self):
        assert ObservationType.LEADERSHIP_ABSENT == "leadership_absent"

    def test_collaboration_strong(self):
        assert ObservationType.COLLABORATION_STRONG == "collaboration_strong"

    def test_collaboration_effective(self):
        assert ObservationType.COLLABORATION_EFFECTIVE == "collaboration_effective"

    def test_collaboration_deficit(self):
        assert ObservationType.COLLABORATION_DEFICIT == "collaboration_deficit"

    def test_adaptability_high(self):
        assert ObservationType.ADAPTABILITY_HIGH == "adaptability_high"

    def test_adaptability_moderate(self):
        assert ObservationType.ADAPTABILITY_MODERATE == "adaptability_moderate"

    def test_adaptability_low(self):
        assert ObservationType.ADAPTABILITY_LOW == "adaptability_low"

    def test_behavioral_growth(self):
        assert ObservationType.BEHAVIORAL_GROWTH == "behavioral_growth"

    def test_behavioral_instability(self):
        assert ObservationType.BEHAVIORAL_INSTABILITY == "behavioral_instability"

    def test_behavioral_plateau(self):
        assert ObservationType.BEHAVIORAL_PLATEAU == "behavioral_plateau"

    def test_knowledge_gap(self):
        assert ObservationType.KNOWLEDGE_GAP == "knowledge_gap"

    def test_knowledge_demonstrated(self):
        assert ObservationType.KNOWLEDGE_DEMONSTRATED == "knowledge_demonstrated"

    def test_knowledge_cross_area_consistent(self):
        assert ObservationType.KNOWLEDGE_CROSS_AREA_CONSISTENT == "knowledge_cross_area_consistent"

    def test_knowledge_cross_area_contradictory(self):
        assert ObservationType.KNOWLEDGE_CROSS_AREA_CONTRADICTORY == "knowledge_cross_area_contradictory"

    def test_engineering_judgment_high(self):
        assert ObservationType.ENGINEERING_JUDGMENT_HIGH == "engineering_judgment_high"

    def test_engineering_judgment_low(self):
        assert ObservationType.ENGINEERING_JUDGMENT_LOW == "engineering_judgment_low"

    def test_engineering_judgment_articulated(self):
        assert ObservationType.ENGINEERING_JUDGMENT_ARTICULATED == "engineering_judgment_articulated"

    def test_performance_improving(self):
        assert ObservationType.PERFORMANCE_IMPROVING == "performance_improving"

    def test_performance_declining(self):
        assert ObservationType.PERFORMANCE_DECLINING == "performance_declining"

    def test_performance_stable(self):
        assert ObservationType.PERFORMANCE_STABLE == "performance_stable"


class TestObservationTypeMembership:
    def test_lookup_by_value(self):
        assert ObservationType("technical_correctness") is ObservationType.TECHNICAL_CORRECTNESS

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            ObservationType("nonexistent_type")

    def test_all_values_unique(self):
        values = [t.value for t in ObservationType]
        assert len(values) == len(set(values))

    def test_all_values_lowercase(self):
        for t in ObservationType:
            assert t.value == t.value.lower(), f"{t} value is not lowercase"

    def test_at_least_40_types(self):
        assert len(ObservationType) >= 40

    def test_behavioral_adr066_types_present(self):
        behavioral = {
            ObservationType.LEADERSHIP_STRONG,
            ObservationType.LEADERSHIP_EMERGING,
            ObservationType.LEADERSHIP_ABSENT,
            ObservationType.COLLABORATION_STRONG,
            ObservationType.COLLABORATION_EFFECTIVE,
            ObservationType.COLLABORATION_DEFICIT,
            ObservationType.ADAPTABILITY_HIGH,
            ObservationType.ADAPTABILITY_MODERATE,
            ObservationType.ADAPTABILITY_LOW,
        }
        for t in behavioral:
            assert t in ObservationType
