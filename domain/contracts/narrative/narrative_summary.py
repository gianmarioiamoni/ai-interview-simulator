# domain/contracts/narrative/narrative_summary.py
# ADR-023 — NarrativeSummary (lightweight read-only view of a Narrative)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType


class NarrativeSummary(BaseModel):
    """Lightweight, immutable summary view of a Narrative.

    Provides key aggregate properties without carrying full prose or feature
    reference payloads. Suitable for display, logging, and monitoring.

    Constraints:
    - No LLM, no CandidateProfile mutation, no Coaching, no Report.
    - Immutable after construction (frozen=True).
    """

    schema_version: str = Field(default="1.0")

    # Section presence
    sections_present: frozenset[NarrativeSectionType] = Field(default_factory=frozenset)
    total_sections: int = Field(default=0, ge=0)

    # Insight summary
    total_insights: int = Field(default=0, ge=0)
    insight_types_present: frozenset[NarrativeInsightType] = Field(default_factory=frozenset)

    # Feature coverage
    unique_feature_ids_referenced: int = Field(default=0, ge=0)

    # Completeness
    is_complete: bool = Field(default=False)

    # Confidence envelope (from insights, if any)
    mean_insight_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    narrative_schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_narrative(cls, narrative: Narrative) -> "NarrativeSummary":
        sections = narrative.all_sections
        insights = narrative.insights

        unique_ids = frozenset(
            fi.feature_type_id
            for s in sections
            for fi in s.feature_references
        ) | frozenset(i.source_feature_id.feature_type_id for i in insights)

        confidences = [i.confidence for i in insights]
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return cls(
            sections_present=frozenset(s.section_type for s in sections),
            total_sections=len(sections),
            total_insights=len(insights),
            insight_types_present=frozenset(i.insight_type for i in insights),
            unique_feature_ids_referenced=len(unique_ids),
            is_complete=narrative.is_complete,
            mean_insight_confidence=mean_conf,
            narrative_schema_version=narrative.schema_version,
        )
