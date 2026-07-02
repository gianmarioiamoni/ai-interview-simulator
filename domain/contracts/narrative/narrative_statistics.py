# domain/contracts/narrative/narrative_statistics.py
# ADR-023 — NarrativeStatistics (aggregate metrics over a Narrative)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType


class InsightTypeCount(BaseModel):
    insight_type: NarrativeInsightType
    count: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}


class NarrativeStatistics(BaseModel):
    """Aggregate metrics for a Narrative or NarrativeCollection.

    Immutable snapshot of statistical properties.
    Pure computation — no LLM, no CandidateProfile mutation.
    """

    total_sections: int = Field(default=0, ge=0)
    total_insights: int = Field(default=0, ge=0)
    total_feature_references: int = Field(default=0, ge=0)

    # Unique ProfileFeature identities referenced across all sections/insights
    unique_feature_ids: frozenset[str] = Field(default_factory=frozenset)

    # Per-type insight counts
    insight_type_counts: tuple[InsightTypeCount, ...] = Field(default_factory=tuple)

    # Confidence distribution
    mean_insight_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    min_insight_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    max_insight_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Section coverage
    sections_present: frozenset[NarrativeSectionType] = Field(default_factory=frozenset)
    is_complete: bool = Field(
        default=False,
        description="True when all 5 mandatory NarrativeSectionTypes are present"
    )

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_narrative(cls, narrative: "Narrative") -> "NarrativeStatistics":  # type: ignore[name-defined]
        from domain.contracts.narrative.narrative import Narrative  # noqa: PLC0415

        sections = narrative.all_sections
        insights = narrative.insights

        total_feature_refs = sum(len(s.feature_references) for s in sections)
        unique_ids = frozenset(
            fi.feature_type_id
            for s in sections
            for fi in s.feature_references
        ) | frozenset(i.source_feature_id.feature_type_id for i in insights)

        type_counts_map: dict[NarrativeInsightType, int] = {}
        for insight in insights:
            type_counts_map[insight.insight_type] = (
                type_counts_map.get(insight.insight_type, 0) + 1
            )
        type_counts = tuple(
            InsightTypeCount(insight_type=t, count=c)
            for t, c in sorted(type_counts_map.items(), key=lambda kv: kv[0].value)
        )

        confidences = [i.confidence for i in insights]
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
        min_conf = min(confidences) if confidences else 0.0
        max_conf = max(confidences) if confidences else 0.0

        sections_present = frozenset(s.section_type for s in sections)
        is_complete = sections_present == frozenset(NarrativeSectionType)

        return cls(
            total_sections=len(sections),
            total_insights=len(insights),
            total_feature_references=total_feature_refs,
            unique_feature_ids=unique_ids,
            insight_type_counts=type_counts,
            mean_insight_confidence=mean_conf,
            min_insight_confidence=min_conf,
            max_insight_confidence=max_conf,
            sections_present=sections_present,
            is_complete=is_complete,
        )
