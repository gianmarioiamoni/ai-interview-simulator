# tests/domain/contracts/feature/test_feature_type.py

import pytest

from domain.contracts.feature.feature_type import FeatureType


class TestFeatureTypeTaxonomy:
    """ADR-018 §D — V1.2 frozen taxonomy of 11 feature types."""

    def test_all_eleven_types_present(self) -> None:
        members = set(FeatureType)
        assert len(members) == 11

    def test_technical_skill_value(self) -> None:
        assert FeatureType.TECHNICAL_SKILL == "technical_skill_feature"

    def test_reasoning_value(self) -> None:
        assert FeatureType.REASONING == "reasoning_feature"

    def test_communication_value(self) -> None:
        assert FeatureType.COMMUNICATION == "communication_feature"

    def test_leadership_value(self) -> None:
        assert FeatureType.LEADERSHIP == "leadership_feature"

    def test_collaboration_value(self) -> None:
        assert FeatureType.COLLABORATION == "collaboration_feature"

    def test_adaptability_value(self) -> None:
        assert FeatureType.ADAPTABILITY == "adaptability_feature"

    def test_learning_value(self) -> None:
        assert FeatureType.LEARNING == "learning_feature"

    def test_confidence_value(self) -> None:
        assert FeatureType.CONFIDENCE == "confidence_feature"

    def test_language_capability_value(self) -> None:
        assert FeatureType.LANGUAGE_CAPABILITY == "language_capability_feature"

    def test_coverage_value(self) -> None:
        assert FeatureType.COVERAGE == "coverage_feature"

    def test_trend_value(self) -> None:
        assert FeatureType.TREND == "trend_feature"

    def test_is_str_enum(self) -> None:
        for ft in FeatureType:
            assert isinstance(ft.value, str)

    def test_no_language_name_in_any_type_id(self) -> None:
        """ADR-018 §C invariant: no type ID may reference a programming language."""
        forbidden = {"python", "java", "javascript", "typescript", "go", "rust", "csharp"}
        for ft in FeatureType:
            for lang in forbidden:
                assert lang not in ft.value.lower(), (
                    f"FeatureType '{ft.value}' references language '{lang}' — "
                    "violates ADR-018 §C language-independence invariant"
                )

    def test_all_values_end_with_feature_suffix(self) -> None:
        for ft in FeatureType:
            assert ft.value.endswith("_feature"), (
                f"FeatureType '{ft.value}' does not follow *_feature naming convention"
            )

    def test_feature_type_from_string_lookup(self) -> None:
        assert FeatureType("reasoning_feature") is FeatureType.REASONING

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValueError):
            FeatureType("nonexistent_feature")

    def test_unique_values(self) -> None:
        values = [ft.value for ft in FeatureType]
        assert len(values) == len(set(values))
