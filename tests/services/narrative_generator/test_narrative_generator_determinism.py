# tests/services/narrative_generator/test_narrative_generator_determinism.py
# Determinism tests — same inputs always produce same output

from __future__ import annotations

import pytest

from domain.contracts.feature.feature_type import FeatureType
from services.narrative_generator.narrative_generator import NarrativeGenerator
from tests.services.narrative_generator.conftest import (
    make_context,
    make_feature,
    make_feature_collection,
)


@pytest.fixture
def generator() -> NarrativeGenerator:
    return NarrativeGenerator()


class TestDeterminism:
    def test_same_context_same_narrative_structure(self, generator: NarrativeGenerator, rich_context) -> None:
        r1 = generator.generate(rich_context)
        r2 = generator.generate(rich_context)
        assert r1.narrative.executive_summary.prose == r2.narrative.executive_summary.prose
        assert r1.narrative.strengths.prose == r2.narrative.strengths.prose
        assert r1.narrative.weaknesses.prose == r2.narrative.weaknesses.prose
        assert r1.narrative.growth_areas.prose == r2.narrative.growth_areas.prose
        assert r1.narrative.recommendations.prose == r2.narrative.recommendations.prose

    def test_same_context_same_section_types(self, generator: NarrativeGenerator, rich_context) -> None:
        r1 = generator.generate(rich_context)
        r2 = generator.generate(rich_context)
        types1 = [s.section_type for s in r1.narrative.all_sections]
        types2 = [s.section_type for s in r2.narrative.all_sections]
        assert types1 == types2

    def test_same_context_same_insight_count(self, generator: NarrativeGenerator, rich_context) -> None:
        r1 = generator.generate(rich_context)
        r2 = generator.generate(rich_context)
        assert r1.narrative.insight_count == r2.narrative.insight_count

    def test_same_context_same_feature_references(self, generator: NarrativeGenerator, rich_context) -> None:
        r1 = generator.generate(rich_context)
        r2 = generator.generate(rich_context)
        for s1, s2 in zip(r1.narrative.all_sections, r2.narrative.all_sections):
            assert s1.feature_references == s2.feature_references

    def test_feature_order_does_not_affect_output(self, generator: NarrativeGenerator) -> None:
        fa = make_feature(FeatureType.REASONING, "HIGH", confidence=0.8)
        fb = make_feature(FeatureType.TECHNICAL_SKILL, "MODERATE", confidence=0.55)

        ctx1 = make_context(features=make_feature_collection([fa, fb]))
        ctx2 = make_context(features=make_feature_collection([fb, fa]))

        r1 = generator.generate(ctx1)
        r2 = generator.generate(ctx2)

        # Sections and insights are built in stable sorted order by type_id
        assert r1.narrative.executive_summary.prose == r2.narrative.executive_summary.prose
        assert r1.narrative.insight_count == r2.narrative.insight_count

    def test_empty_features_deterministic(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(features=make_feature_collection([]))
        r1 = generator.generate(ctx)
        r2 = generator.generate(ctx)
        assert r1.narrative.executive_summary.prose == r2.narrative.executive_summary.prose

    def test_multiple_invocations_same_generator_instance(self, generator: NarrativeGenerator, rich_context) -> None:
        results = [generator.generate(rich_context) for _ in range(5)]
        prose_set = {r.narrative.executive_summary.prose for r in results}
        assert len(prose_set) == 1
