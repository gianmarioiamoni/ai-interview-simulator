# tests/domain/contracts/feature/test_feature_identity.py

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType


class TestFeatureIdentityConstruction:
    def test_minimal_valid(self) -> None:
        fi = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="analytical_reasoning")
        assert fi.feature_type_id == "reasoning_feature"
        assert fi.semantic_category == "analytical_reasoning"
        assert fi.schema_version == "1.0"

    def test_custom_schema_version(self) -> None:
        fi = FeatureIdentity(
            feature_type_id="reasoning_feature",
            semantic_category="analytical_reasoning",
            schema_version="2.0",
        )
        assert fi.schema_version == "2.0"

    def test_empty_feature_type_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FeatureIdentity(feature_type_id="", semantic_category="cat")

    def test_empty_semantic_category_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="")

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FeatureIdentity(
                feature_type_id="reasoning_feature",
                semantic_category="cat",
                unknown_field="x",
            )

    def test_immutability(self) -> None:
        fi = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="cat")
        with pytest.raises(ValidationError):
            fi.feature_type_id = "other"  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        a = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="cat")
        b = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="cat")
        assert a == b

    def test_inequality_different_type_id(self) -> None:
        a = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="cat")
        b = FeatureIdentity(feature_type_id="trend_feature", semantic_category="cat")
        assert a != b

    def test_inequality_different_category(self) -> None:
        a = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="cat_a")
        b = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="cat_b")
        assert a != b

    def test_hashable(self) -> None:
        fi = FeatureIdentity(feature_type_id="reasoning_feature", semantic_category="cat")
        {fi}  # should not raise


class TestFeatureIdentityRegistry:
    """for_type() factory returns canonical V1.2 identities."""

    @pytest.mark.parametrize("ft", list(FeatureType))
    def test_for_type_returns_identity_for_all_types(self, ft: FeatureType) -> None:
        fi = FeatureIdentity.for_type(ft)
        assert isinstance(fi, FeatureIdentity)
        assert fi.feature_type_id == ft.value

    def test_reasoning_canonical_category(self) -> None:
        fi = FeatureIdentity.for_type(FeatureType.REASONING)
        assert fi.semantic_category == "analytical_reasoning"

    def test_technical_skill_canonical_category(self) -> None:
        fi = FeatureIdentity.for_type(FeatureType.TECHNICAL_SKILL)
        assert fi.semantic_category == "technical_knowledge"

    def test_language_capability_canonical_category(self) -> None:
        fi = FeatureIdentity.for_type(FeatureType.LANGUAGE_CAPABILITY)
        assert fi.semantic_category == "language_idiomatic_proficiency"

    def test_for_type_returns_same_object_each_call(self) -> None:
        a = FeatureIdentity.for_type(FeatureType.TREND)
        b = FeatureIdentity.for_type(FeatureType.TREND)
        assert a == b

    def test_schema_evolution_invariant_feature_type_id_stable(self) -> None:
        """ADR-020 §F: schema evolution must never change FeatureIdentity."""
        fi = FeatureIdentity.for_type(FeatureType.COVERAGE)
        assert fi.feature_type_id == "coverage_feature"

    def test_all_registered_type_ids_match_enum_values(self) -> None:
        for ft in FeatureType:
            fi = FeatureIdentity.for_type(ft)
            assert fi.feature_type_id == ft.value
