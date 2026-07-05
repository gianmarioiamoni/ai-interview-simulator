# tests/domain/contracts/report/test_scoring_narrative_item.py

import pytest
from pydantic import ValidationError

from domain.contracts.report.scoring_narrative_item import ScoringNarrativeItem


def _valid_kwargs(**overrides) -> dict:
    base = {
        "category": "Communication",
        "description": "Struggled to explain trade-offs clearly.",
        "why_it_matters": "Interviewers assess clarity of thought.",
        "context_detail": None,
    }
    base.update(overrides)
    return base


class TestScoringNarrativeItemConstruction:
    def test_valid_with_context_detail(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail="Had significant impact on overall score."))
        assert item.context_detail == "Had significant impact on overall score."

    def test_valid_without_context_detail(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail=None))
        assert item.context_detail is None

    def test_context_detail_defaults_to_none(self):
        item = ScoringNarrativeItem(
            category="Communication",
            description="description text",
            why_it_matters="matters text",
        )
        assert item.context_detail is None

    def test_all_required_fields_set(self):
        item = ScoringNarrativeItem(**_valid_kwargs())
        assert item.category == "Communication"
        assert item.description == "Struggled to explain trade-offs clearly."
        assert item.why_it_matters == "Interviewers assess clarity of thought."


class TestScoringNarrativeItemFieldValidation:
    def test_empty_category_rejected(self):
        with pytest.raises(ValidationError):
            ScoringNarrativeItem(**_valid_kwargs(category=""))

    def test_empty_description_rejected(self):
        with pytest.raises(ValidationError):
            ScoringNarrativeItem(**_valid_kwargs(description=""))

    def test_empty_why_it_matters_rejected(self):
        with pytest.raises(ValidationError):
            ScoringNarrativeItem(**_valid_kwargs(why_it_matters=""))

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ScoringNarrativeItem(**_valid_kwargs(unknown="extra"))


class TestScoringNarrativeItemImmutability:
    def test_category_assignment_raises(self):
        item = ScoringNarrativeItem(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            item.category = "changed"  # type: ignore[misc]

    def test_description_assignment_raises(self):
        item = ScoringNarrativeItem(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            item.description = "changed"  # type: ignore[misc]

    def test_context_detail_assignment_raises(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail="original"))
        with pytest.raises((TypeError, ValidationError)):
            item.context_detail = "changed"  # type: ignore[misc]


class TestScoringNarrativeItemToDict:
    def test_to_dict_contains_all_keys(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail="impact text"))
        d = item.to_dict()
        assert set(d.keys()) == {"category", "description", "why_it_matters", "context_detail"}

    def test_to_dict_values_match_fields(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail="impact text"))
        d = item.to_dict()
        assert d["category"] == item.category
        assert d["description"] == item.description
        assert d["why_it_matters"] == item.why_it_matters
        assert d["context_detail"] == "impact text"

    def test_to_dict_context_detail_none_when_absent(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail=None))
        d = item.to_dict()
        assert d["context_detail"] is None

    def test_to_dict_does_not_mutate_item(self):
        item = ScoringNarrativeItem(**_valid_kwargs())
        _ = item.to_dict()
        assert item.category == "Communication"


class TestScoringNarrativeItemSerialization:
    def test_round_trip_with_context_detail(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail="some detail"))
        restored = ScoringNarrativeItem.model_validate(item.model_dump())
        assert restored == item

    def test_round_trip_without_context_detail(self):
        item = ScoringNarrativeItem(**_valid_kwargs(context_detail=None))
        restored = ScoringNarrativeItem.model_validate(item.model_dump())
        assert restored == item


class TestScoringNarrativeItemEquality:
    def test_equal_instances(self):
        a = ScoringNarrativeItem(**_valid_kwargs())
        b = ScoringNarrativeItem(**_valid_kwargs())
        assert a == b

    def test_different_category_not_equal(self):
        a = ScoringNarrativeItem(**_valid_kwargs(category="Cat A"))
        b = ScoringNarrativeItem(**_valid_kwargs(category="Cat B"))
        assert a != b

    def test_context_detail_none_vs_value_not_equal(self):
        a = ScoringNarrativeItem(**_valid_kwargs(context_detail=None))
        b = ScoringNarrativeItem(**_valid_kwargs(context_detail="some detail"))
        assert a != b
