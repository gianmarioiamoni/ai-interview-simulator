# tests/services/narrative_generator/test_narrative_generator_behavior.py
# Behavior tests — NarrativeGenerator section/insight assembly

from __future__ import annotations

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from services.narrative_generator.narrative_generator import NarrativeGenerator
from tests.services.narrative_generator.conftest import (
    make_context,
    make_feature,
    make_feature_collection,
    make_profile,
)


@pytest.fixture
def generator() -> NarrativeGenerator:
    return NarrativeGenerator()


class TestSectionAssembly:
    def test_all_five_sections_present(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        assert result.is_successful
        types = {s.section_type for s in result.narrative.all_sections}
        assert types == set(NarrativeSectionType)

    def test_sections_have_non_empty_prose(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        for section in result.narrative.all_sections:
            assert len(section.prose) > 0

    def test_sections_have_feature_references(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        for section in result.narrative.all_sections:
            assert len(section.feature_references) >= 1

    def test_executive_summary_contains_question_count(self, generator: NarrativeGenerator) -> None:
        profile = make_profile(questions_answered=7, areas_covered=["algorithms"])
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            profile=profile,
        )
        result = generator.generate(ctx)
        assert "7" in result.narrative.executive_summary.prose

    def test_executive_summary_contains_area(self, generator: NarrativeGenerator) -> None:
        profile = make_profile(questions_answered=3, areas_covered=["system-design"])
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            profile=profile,
        )
        result = generator.generate(ctx)
        assert "system-design" in result.narrative.executive_summary.prose

    def test_growth_section_contains_knowledge_gap(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            knowledge_gap_areas=("graph-traversal",),
        )
        result = generator.generate(ctx)
        assert "graph-traversal" in result.narrative.growth_areas.prose

    def test_recommendations_contain_evaluation_summary(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            evaluation_summary={"problem_solving": "LOW"},
        )
        result = generator.generate(ctx)
        assert "problem_solving" in result.narrative.recommendations.prose

    def test_strengths_section_references_high_confidence_features(
        self, generator: NarrativeGenerator
    ) -> None:
        high = make_feature(FeatureType.REASONING, "HIGH", confidence=0.9)
        low = make_feature(FeatureType.CONFIDENCE, "LOW", confidence=0.2)
        ctx = make_context(features=make_feature_collection([high, low]))
        result = generator.generate(ctx)
        strength_ids = {fi.feature_type_id for fi in result.narrative.strengths.feature_references}
        assert "reasoning_feature" in strength_ids

    def test_sentinel_identity_used_when_no_features(
        self, generator: NarrativeGenerator, empty_context
    ) -> None:
        result = generator.generate(empty_context)
        assert result.is_successful
        for section in result.narrative.all_sections:
            assert len(section.feature_references) >= 1


class TestInsightAssembly:
    def test_high_confidence_yields_strength_signal(self, generator: NarrativeGenerator) -> None:
        f = make_feature(FeatureType.REASONING, "HIGH", confidence=0.85)
        ctx = make_context(features=make_feature_collection([f]))
        result = generator.generate(ctx)
        types = {i.insight_type for i in result.narrative.insights}
        assert NarrativeInsightType.STRENGTH_SIGNAL in types

    def test_low_confidence_yields_risk_signal(self, generator: NarrativeGenerator) -> None:
        f = make_feature(FeatureType.CONFIDENCE, "LOW", confidence=0.2)
        ctx = make_context(features=make_feature_collection([f]))
        result = generator.generate(ctx)
        types = {i.insight_type for i in result.narrative.insights}
        assert NarrativeInsightType.RISK_SIGNAL in types

    def test_medium_confidence_yields_growth_opportunity(self, generator: NarrativeGenerator) -> None:
        f = make_feature(FeatureType.TECHNICAL_SKILL, "MODERATE", confidence=0.5)
        ctx = make_context(features=make_feature_collection([f]))
        result = generator.generate(ctx)
        types = {i.insight_type for i in result.narrative.insights}
        assert NarrativeInsightType.GROWTH_OPPORTUNITY in types

    def test_insight_count_matches_feature_count(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        assert result.narrative.insight_count == rich_context.features.size

    def test_zero_insights_when_empty_features(
        self, generator: NarrativeGenerator, empty_context
    ) -> None:
        result = generator.generate(empty_context)
        assert result.narrative.insight_count == 0

    def test_every_insight_has_source_feature(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        for insight in result.narrative.insights:
            assert insight.is_traceable
            assert insight.source_feature_id is not None

    def test_insight_confidence_inherits_from_feature(self, generator: NarrativeGenerator) -> None:
        f = make_feature(FeatureType.REASONING, "HIGH", confidence=0.77)
        ctx = make_context(features=make_feature_collection([f]))
        result = generator.generate(ctx)
        assert result.narrative.insights[0].confidence == pytest.approx(0.77)
