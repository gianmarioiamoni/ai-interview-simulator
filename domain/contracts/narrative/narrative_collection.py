# domain/contracts/narrative/narrative_collection.py
# ADR-023 — NarrativeCollection (runtime container for NarrativeInsight[])

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType


class NarrativeCollection(BaseModel):
    """Ordered, immutable container for NarrativeInsight objects.

    Provides filtering and grouping without exposing mutable state.
    No business logic; pure runtime container.

    Constraints:
    - Immutable after construction (frozen=True).
    - No LLM, no CandidateProfile mutation, no Coaching, no Report.
    """

    insights: tuple[NarrativeInsight, ...] = Field(default_factory=tuple)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_list(cls, insights: list[NarrativeInsight]) -> "NarrativeCollection":
        return cls(insights=tuple(insights))

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self.insights)

    @property
    def is_empty(self) -> bool:
        return len(self.insights) == 0

    def by_type(self, insight_type: NarrativeInsightType) -> "NarrativeCollection":
        return NarrativeCollection(
            insights=tuple(i for i in self.insights if i.insight_type == insight_type)
        )

    def with_min_confidence(self, min_confidence: float) -> "NarrativeCollection":
        return NarrativeCollection(
            insights=tuple(i for i in self.insights if i.confidence >= min_confidence)
        )

    def by_feature_type_id(self, feature_type_id: str) -> "NarrativeCollection":
        return NarrativeCollection(
            insights=tuple(
                i for i in self.insights
                if i.source_feature_id.feature_type_id == feature_type_id
            )
        )

    def insight_types(self) -> frozenset[NarrativeInsightType]:
        return frozenset(i.insight_type for i in self.insights)
