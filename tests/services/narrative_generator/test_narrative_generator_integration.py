# tests/services/narrative_generator/test_narrative_generator_integration.py
# Integration tests — end-to-end generation with varied inputs

from __future__ import annotations

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from services.narrative_generator.narrative_generator import NarrativeGenerator
from tests.services.narrative_generator.conftest import (
    make_context,
    make_feature,
    make_feature_collection,
    make_language_profile,
    make_profile,
)


@pytest.fixture
def generator() -> NarrativeGenerator:
    return NarrativeGenerator()


class TestEndToEndGeneration:
    def test_full_run_with_all_inputs(self, generator: NarrativeGenerator) -> None:
        features = make_feature_collection([
            make_feature(FeatureType.REASONING, "HIGH", confidence=0.9),
            make_feature(FeatureType.TECHNICAL_SKILL, "HIGH", confidence=0.75),
            make_feature(FeatureType.CONFIDENCE, "LOW", confidence=0.2),
            make_feature(FeatureType.TREND, "STABLE", confidence=0.5),
        ])
        ctx = make_context(
            features=features,
            profile=make_profile(questions_answered=10, areas_covered=["algorithms", "data-structures", "system-design"]),
            knowledge_gap_areas=("dynamic programming", "graph traversal"),
            evaluation_summary={"technical_depth": "HIGH", "problem_solving": "MODERATE"},
            interview_metadata={"topic": "backend", "level": "senior"},
            language_profile=make_language_profile(),
        )
        result = generator.generate(ctx)

        assert result.is_successful
        assert result.has_narrative
        assert result.narrative.is_complete
        assert result.narrative.insight_count == 4
        assert result.diagnostics.is_successful

    def test_single_feature_session(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(
            features=make_feature_collection([make_feature(FeatureType.REASONING)]),
        )
        result = generator.generate(ctx)
        assert result.is_successful
        assert result.narrative.insight_count == 1

    def test_all_feature_types_handled(self, generator: NarrativeGenerator) -> None:
        features = make_feature_collection([
            make_feature(ft, "MODERATE", confidence=0.5) for ft in FeatureType
        ])
        ctx = make_context(features=features)
        result = generator.generate(ctx)
        assert result.is_successful
        assert result.narrative.insight_count == len(list(FeatureType))

    def test_empty_areas_covered_handled(self, generator: NarrativeGenerator) -> None:
        profile = make_profile(questions_answered=1, areas_covered=[])
        ctx = make_context(
            profile=profile,
            features=make_feature_collection([make_feature()]),
            # override the default profile by passing it explicitly
        )
        result = generator.generate(ctx)
        assert result.is_successful
        # When areas_covered is empty, fallback text is "general topics"
        assert "general topics" in result.narrative.executive_summary.prose

    def test_empty_knowledge_gaps_handled(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            knowledge_gap_areas=(),
        )
        result = generator.generate(ctx)
        assert result.is_successful
        assert "none identified" in result.narrative.growth_areas.prose

    def test_empty_evaluation_summary_handled(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            evaluation_summary={},
        )
        result = generator.generate(ctx)
        assert result.is_successful

    def test_no_language_profile_handled(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            language_profile=None,
        )
        result = generator.generate(ctx)
        assert result.is_successful

    def test_with_language_profile(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(
            features=make_feature_collection([make_feature()]),
            language_profile=make_language_profile(),
        )
        result = generator.generate(ctx)
        assert result.is_successful

    def test_narrative_invariants_satisfied(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        narrative = result.narrative

        # ADR-023: all five sections must be present and in correct slots
        assert narrative.executive_summary.section_type == NarrativeSectionType.EXECUTIVE_SUMMARY
        assert narrative.strengths.section_type == NarrativeSectionType.STRENGTHS
        assert narrative.weaknesses.section_type == NarrativeSectionType.WEAKNESSES
        assert narrative.growth_areas.section_type == NarrativeSectionType.GROWTH
        assert narrative.recommendations.section_type == NarrativeSectionType.RECOMMENDATIONS

    def test_schema_version_present(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        assert result.narrative.schema_version == "1.0"
        assert result.schema_version == "1.0"
