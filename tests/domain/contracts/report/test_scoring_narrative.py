# tests/domain/contracts/report/test_scoring_narrative.py

import pytest
from pydantic import ValidationError

from domain.contracts.report.scoring_narrative import ScoringNarrative
from domain.contracts.report.scoring_narrative_item import ScoringNarrativeItem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _item(**overrides) -> ScoringNarrativeItem:
    base = {
        "category": "Communication",
        "description": "Struggled to explain trade-offs.",
        "why_it_matters": "Clarity is essential in interviews.",
        "context_detail": "Had significant impact on score.",
    }
    base.update(overrides)
    return ScoringNarrativeItem(**base)


def _minimal() -> ScoringNarrative:
    return ScoringNarrative(executive_summary="Strong hire — excellent technical depth.")


def _full() -> ScoringNarrative:
    return ScoringNarrative(
        executive_summary="Strong hire — excellent technical depth.",
        went_well=("Good problem decomposition.", "Clear communication."),
        held_you_back=(_item(),),
        knowledge_gaps=(_item(category="System Design", description="Gaps in distributed systems.", context_detail="Relevant to target role."),),
        next_strategy=(_item(category="Practice", description="Mock system design interviews.", context_detail="Expected +10 percentile."),),
        improvement_suggestions=("Practice system design.", "Review distributed consensus."),
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestScoringNarrativeConstruction:
    def test_minimal_construction_with_summary_only(self):
        sn = _minimal()
        assert sn.executive_summary == "Strong hire — excellent technical depth."
        assert sn.went_well == ()
        assert sn.held_you_back == ()
        assert sn.knowledge_gaps == ()
        assert sn.next_strategy == ()
        assert sn.improvement_suggestions == ()
        assert sn.schema_version == "1.0"

    def test_full_construction(self):
        sn = _full()
        assert len(sn.went_well) == 2
        assert len(sn.held_you_back) == 1
        assert len(sn.knowledge_gaps) == 1
        assert len(sn.next_strategy) == 1
        assert len(sn.improvement_suggestions) == 2

    def test_schema_version_default(self):
        sn = _minimal()
        assert sn.schema_version == "1.0"

    def test_custom_schema_version(self):
        sn = ScoringNarrative(executive_summary="summary", schema_version="2.0")
        assert sn.schema_version == "2.0"

    def test_sections_stored_as_tuples(self):
        sn = _full()
        assert isinstance(sn.went_well, tuple)
        assert isinstance(sn.held_you_back, tuple)
        assert isinstance(sn.knowledge_gaps, tuple)
        assert isinstance(sn.next_strategy, tuple)
        assert isinstance(sn.improvement_suggestions, tuple)

    def test_nested_items_accessible(self):
        sn = _full()
        assert sn.held_you_back[0].category == "Communication"
        assert sn.knowledge_gaps[0].category == "System Design"

    def test_context_detail_none_accepted_in_items(self):
        item = _item(context_detail=None)
        sn = ScoringNarrative(executive_summary="summary", held_you_back=(item,))
        assert sn.held_you_back[0].context_detail is None


# ---------------------------------------------------------------------------
# Field validation
# ---------------------------------------------------------------------------


class TestScoringNarrativeFieldValidation:
    def test_empty_executive_summary_rejected(self):
        with pytest.raises(ValidationError):
            ScoringNarrative(executive_summary="")

    def test_empty_schema_version_rejected(self):
        with pytest.raises(ValidationError):
            ScoringNarrative(executive_summary="summary", schema_version="")

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ScoringNarrative(executive_summary="summary", unknown_field="value")


# ---------------------------------------------------------------------------
# Invariants (V-SN-02)
# ---------------------------------------------------------------------------


class TestScoringNarrativeInvariants:
    def test_v_sn_01_non_empty_executive_summary(self):
        with pytest.raises(ValidationError):
            ScoringNarrative(executive_summary="")

    def test_v_sn_02_held_you_back_item_requires_category(self):
        # ScoringNarrativeItem itself enforces min_length=1 on category
        with pytest.raises(ValidationError):
            ScoringNarrativeItem(category="", description="d", why_it_matters="w")

    def test_v_sn_02_knowledge_gap_item_requires_description(self):
        with pytest.raises(ValidationError):
            ScoringNarrativeItem(category="c", description="", why_it_matters="w")

    def test_v_sn_02_next_strategy_item_requires_why_it_matters(self):
        with pytest.raises(ValidationError):
            ScoringNarrativeItem(category="c", description="d", why_it_matters="")

    def test_v_sn_03_schema_version_non_empty(self):
        with pytest.raises(ValidationError):
            ScoringNarrative(executive_summary="summary", schema_version="")


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestScoringNarrativeImmutability:
    def test_executive_summary_assignment_raises(self):
        sn = _minimal()
        with pytest.raises((TypeError, ValidationError)):
            sn.executive_summary = "changed"  # type: ignore[misc]

    def test_went_well_assignment_raises(self):
        sn = _full()
        with pytest.raises((TypeError, ValidationError)):
            sn.went_well = ()  # type: ignore[misc]

    def test_held_you_back_assignment_raises(self):
        sn = _full()
        with pytest.raises((TypeError, ValidationError)):
            sn.held_you_back = ()  # type: ignore[misc]

    def test_schema_version_assignment_raises(self):
        sn = _minimal()
        with pytest.raises((TypeError, ValidationError)):
            sn.schema_version = "2.0"  # type: ignore[misc]

    def test_nested_items_are_frozen(self):
        sn = _full()
        with pytest.raises((TypeError, ValidationError)):
            sn.held_you_back[0].category = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestScoringNarrativeSerialization:
    def test_model_dump_contains_all_keys(self):
        sn = _full()
        data = sn.model_dump()
        expected = {
            "executive_summary", "went_well", "held_you_back",
            "knowledge_gaps", "next_strategy", "improvement_suggestions",
            "schema_version",
        }
        assert expected == set(data.keys())

    def test_round_trip_minimal(self):
        sn = _minimal()
        restored = ScoringNarrative.model_validate(sn.model_dump())
        assert restored == sn

    def test_round_trip_full(self):
        sn = _full()
        restored = ScoringNarrative.model_validate(sn.model_dump())
        assert restored == sn

    def test_round_trip_preserves_nested_item_context_detail(self):
        sn = _full()
        restored = ScoringNarrative.model_validate(sn.model_dump())
        assert restored.held_you_back[0].context_detail == sn.held_you_back[0].context_detail

    def test_empty_sections_serialized_as_empty_sequences(self):
        sn = _minimal()
        data = sn.model_dump()
        assert len(data["went_well"]) == 0
        assert len(data["held_you_back"]) == 0


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------


class TestScoringNarrativeEquality:
    def test_equal_minimal_instances(self):
        a = _minimal()
        b = _minimal()
        assert a == b

    def test_equal_full_instances(self):
        a = _full()
        b = _full()
        assert a == b

    def test_different_executive_summary_not_equal(self):
        a = ScoringNarrative(executive_summary="Summary A")
        b = ScoringNarrative(executive_summary="Summary B")
        assert a != b

    def test_different_went_well_not_equal(self):
        a = ScoringNarrative(executive_summary="s", went_well=("item A",))
        b = ScoringNarrative(executive_summary="s", went_well=("item B",))
        assert a != b

    def test_different_held_you_back_items_not_equal(self):
        item_a = _item(category="Cat A")
        item_b = _item(category="Cat B")
        a = ScoringNarrative(executive_summary="s", held_you_back=(item_a,))
        b = ScoringNarrative(executive_summary="s", held_you_back=(item_b,))
        assert a != b

    def test_empty_vs_populated_sections_not_equal(self):
        a = _minimal()
        b = ScoringNarrative(executive_summary="Strong hire — excellent technical depth.", went_well=("Good work.",))
        assert a != b
