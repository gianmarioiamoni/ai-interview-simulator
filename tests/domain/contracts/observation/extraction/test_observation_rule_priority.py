# tests/domain/contracts/observation/extraction/test_observation_rule_priority.py

import pytest

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority


class TestObservationRulePriorityValues:
    def test_critical_is_10(self):
        assert ObservationRulePriority.CRITICAL == 10

    def test_high_is_20(self):
        assert ObservationRulePriority.HIGH == 20

    def test_normal_is_50(self):
        assert ObservationRulePriority.NORMAL == 50

    def test_low_is_80(self):
        assert ObservationRulePriority.LOW == 80

    def test_fallback_is_100(self):
        assert ObservationRulePriority.FALLBACK == 100

    def test_is_int_enum(self):
        assert isinstance(ObservationRulePriority.NORMAL, int)

    def test_exactly_five_levels(self):
        assert len(ObservationRulePriority) == 5

    def test_all_values_unique(self):
        values = [p.value for p in ObservationRulePriority]
        assert len(values) == len(set(values))


class TestObservationRulePriorityOrdering:
    def test_critical_lt_high(self):
        assert ObservationRulePriority.CRITICAL < ObservationRulePriority.HIGH

    def test_high_lt_normal(self):
        assert ObservationRulePriority.HIGH < ObservationRulePriority.NORMAL

    def test_normal_lt_low(self):
        assert ObservationRulePriority.NORMAL < ObservationRulePriority.LOW

    def test_low_lt_fallback(self):
        assert ObservationRulePriority.LOW < ObservationRulePriority.FALLBACK

    def test_sorted_ascending(self):
        levels = sorted(ObservationRulePriority)
        assert list(levels) == [
            ObservationRulePriority.CRITICAL,
            ObservationRulePriority.HIGH,
            ObservationRulePriority.NORMAL,
            ObservationRulePriority.LOW,
            ObservationRulePriority.FALLBACK,
        ]

    def test_usable_as_sort_key(self):
        priorities = [
            ObservationRulePriority.FALLBACK,
            ObservationRulePriority.CRITICAL,
            ObservationRulePriority.NORMAL,
        ]
        sorted_p = sorted(priorities)
        assert sorted_p[0] == ObservationRulePriority.CRITICAL
        assert sorted_p[-1] == ObservationRulePriority.FALLBACK
