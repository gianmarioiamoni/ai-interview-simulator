# tests/domain/contracts/narrative/conftest.py
# Shared fixtures for Narrative contract tests

from __future__ import annotations

import pytest

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType


# ---------------------------------------------------------------------------
# Canonical FeatureIdentity helpers
# ---------------------------------------------------------------------------

REASONING_ID = FeatureIdentity.for_type(FeatureType.REASONING)
TECHNICAL_ID = FeatureIdentity.for_type(FeatureType.TECHNICAL_SKILL)
CONFIDENCE_ID = FeatureIdentity.for_type(FeatureType.CONFIDENCE)


def make_section(
    section_type: NarrativeSectionType,
    prose: str = "Test prose.",
    feature_refs: tuple[FeatureIdentity, ...] | None = None,
    confidence_context: str = "High confidence.",
) -> NarrativeSection:
    return NarrativeSection(
        section_type=section_type,
        prose=prose,
        feature_references=feature_refs or (REASONING_ID,),
        confidence_context=confidence_context,
    )


def make_insight(
    insight_type: NarrativeInsightType = NarrativeInsightType.STRENGTH_SIGNAL,
    prose: str = "Candidate showed strong reasoning.",
    source_feature_id: FeatureIdentity | None = None,
    confidence: float = 0.85,
) -> NarrativeInsight:
    return NarrativeInsight(
        insight_type=insight_type,
        prose=prose,
        source_feature_id=source_feature_id or REASONING_ID,
        confidence=confidence,
    )


def make_narrative(
    with_insights: bool = False,
    insights: list[NarrativeInsight] | None = None,
) -> Narrative:
    builder = (
        NarrativeBuilder()
        .with_executive_summary(make_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
        .with_strengths(make_section(NarrativeSectionType.STRENGTHS))
        .with_weaknesses(make_section(NarrativeSectionType.WEAKNESSES))
        .with_growth_areas(make_section(NarrativeSectionType.GROWTH))
        .with_recommendations(make_section(NarrativeSectionType.RECOMMENDATIONS))
    )
    if with_insights or insights:
        for ins in (insights or [make_insight()]):
            builder.with_insight(ins)
    return builder.build()


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def reasoning_id() -> FeatureIdentity:
    return REASONING_ID


@pytest.fixture
def technical_id() -> FeatureIdentity:
    return TECHNICAL_ID


@pytest.fixture
def basic_section() -> NarrativeSection:
    return make_section(NarrativeSectionType.STRENGTHS)


@pytest.fixture
def basic_insight() -> NarrativeInsight:
    return make_insight()


@pytest.fixture
def complete_narrative() -> Narrative:
    return make_narrative()


@pytest.fixture
def narrative_with_insights() -> Narrative:
    return make_narrative(with_insights=True)
