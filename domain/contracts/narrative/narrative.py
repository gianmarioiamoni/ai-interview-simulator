# domain/contracts/narrative/narrative.py
# ADR-023 Section C — Narrative (root output object)

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType


_MANDATORY_SECTIONS = frozenset(NarrativeSectionType)


class Narrative(BaseModel):
    """Root output of NarrativeGenerator — one per session (ADR-023 §C).

    All five section types are mandatory. Structure is deterministic.
    prose inside each section is LLM-generated (variable).

    ADR-023 invariants enforced here:
    - N-01, N-02: never mutates CandidateProfile or any upstream knowledge object.
    - N-04: terminal; nothing downstream writes back.
    - N-08: immutable after construction (frozen=True).
    - C-04: schema_version always present.

    Five mandatory sections enforce Principle 3 (deterministic structure).
    """

    overview_section: NarrativeSection = Field(
        ..., description="Mandatory overview section (renamed from executive_summary — ADR-033)"
    )
    strengths: NarrativeSection = Field(
        ..., description="Mandatory strengths section"
    )
    weaknesses: NarrativeSection = Field(
        ..., description="Mandatory weaknesses section"
    )
    growth_areas: NarrativeSection = Field(
        ..., description="Mandatory growth areas section"
    )
    recommendations: NarrativeSection = Field(
        ..., description="Mandatory high-level recommendations section (C-03)"
    )
    insights: tuple[NarrativeInsight, ...] = Field(
        default_factory=tuple,
        description="Zero or more atomic findings (0..N)"
    )
    schema_version: str = Field(
        default="1.0",
        description="Narrative schema version for ADR-022 KnowledgeSnapshot compatibility (C-04)"
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _section_type_invariant(self) -> "Narrative":
        """Each mandatory section must carry its declared section_type."""
        checks = [
            (self.overview_section, NarrativeSectionType.EXECUTIVE_SUMMARY, "overview_section"),
            (self.strengths, NarrativeSectionType.STRENGTHS, "strengths"),
            (self.weaknesses, NarrativeSectionType.WEAKNESSES, "weaknesses"),
            (self.growth_areas, NarrativeSectionType.GROWTH, "growth_areas"),
            (self.recommendations, NarrativeSectionType.RECOMMENDATIONS, "recommendations"),
        ]
        for section, expected_type, slot_name in checks:
            if section.section_type != expected_type:
                raise ValueError(
                    f"Section in slot '{slot_name}' has "
                    f"section_type='{section.section_type.value}' "
                    f"but expected '{expected_type.value}'."
                )
        return self

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    @property
    def all_sections(self) -> tuple[NarrativeSection, ...]:
        """All five mandatory sections in canonical order."""
        return (
            self.overview_section,
            self.strengths,
            self.weaknesses,
            self.growth_areas,
            self.recommendations,
        )

    @property
    def insight_count(self) -> int:
        return len(self.insights)

    @property
    def is_complete(self) -> bool:
        """True when all five mandatory sections are present (always True for valid Narrative)."""
        return True
