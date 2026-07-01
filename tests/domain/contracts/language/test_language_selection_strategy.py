# tests/domain/contracts/language/test_language_selection_strategy.py

import pytest
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy


class TestLanguageSelectionStrategy:
    def test_deterministic_alternating_exists(self):
        assert LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING == "deterministic_alternating"

    def test_reserved_strategies_exist(self):
        assert LanguageSelectionStrategy.WEIGHTED_RANDOM == "weighted_random"
        assert LanguageSelectionStrategy.CANDIDATE_PREFERENCE == "candidate_preference"
        assert LanguageSelectionStrategy.ADAPTIVE == "adaptive"

    def test_is_str_enum(self):
        assert isinstance(LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING, str)

    def test_all_values_unique(self):
        values = [s.value for s in LanguageSelectionStrategy]
        assert len(values) == len(set(values))

    def test_v12_default_is_deterministic(self):
        # V1.2 only supports DETERMINISTIC_ALTERNATING for mixed sessions
        assert LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING.value == "deterministic_alternating"
