# domain/contracts/narrative/narrative_builder.py
# ADR-023 — NarrativeBuilder (sole constructor path for Narrative)

from __future__ import annotations

from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType


class NarrativeBuilder:
    """Sole permitted constructor path for Narrative (ADR-023 §C).

    Fluent builder enforcing all structural invariants before build().

    Constraints (ADR-023):
    - All five mandatory sections must be set before build().
    - Sections must carry the correct NarrativeSectionType.
    - No LLM, no CandidateProfile mutation, no Coaching, no Report.
    - build() raises if any mandatory section is missing.

    Usage::

        narrative = (
            NarrativeBuilder()
            .with_executive_summary(exec_section)
            .with_strengths(str_section)
            .with_weaknesses(weak_section)
            .with_growth_areas(growth_section)
            .with_recommendations(rec_section)
            .with_insight(insight1)
            .build()
        )
    """

    def __init__(self) -> None:
        self._executive_summary: NarrativeSection | None = None
        self._strengths: NarrativeSection | None = None
        self._weaknesses: NarrativeSection | None = None
        self._growth_areas: NarrativeSection | None = None
        self._recommendations: NarrativeSection | None = None
        self._insights: list[NarrativeInsight] = []
        self._schema_version: str = "1.0"

    # ------------------------------------------------------------------
    # Fluent setters — mandatory sections
    # ------------------------------------------------------------------

    def with_executive_summary(self, section: NarrativeSection) -> "NarrativeBuilder":
        self._validate_section_type(section, NarrativeSectionType.EXECUTIVE_SUMMARY)
        self._executive_summary = section
        return self

    def with_strengths(self, section: NarrativeSection) -> "NarrativeBuilder":
        self._validate_section_type(section, NarrativeSectionType.STRENGTHS)
        self._strengths = section
        return self

    def with_weaknesses(self, section: NarrativeSection) -> "NarrativeBuilder":
        self._validate_section_type(section, NarrativeSectionType.WEAKNESSES)
        self._weaknesses = section
        return self

    def with_growth_areas(self, section: NarrativeSection) -> "NarrativeBuilder":
        self._validate_section_type(section, NarrativeSectionType.GROWTH)
        self._growth_areas = section
        return self

    def with_recommendations(self, section: NarrativeSection) -> "NarrativeBuilder":
        self._validate_section_type(section, NarrativeSectionType.RECOMMENDATIONS)
        self._recommendations = section
        return self

    # ------------------------------------------------------------------
    # Fluent setters — optional insights
    # ------------------------------------------------------------------

    def with_insight(self, insight: NarrativeInsight) -> "NarrativeBuilder":
        self._insights.append(insight)
        return self

    def with_insights(self, insights: list[NarrativeInsight]) -> "NarrativeBuilder":
        self._insights.extend(insights)
        return self

    def with_schema_version(self, version: str) -> "NarrativeBuilder":
        self._schema_version = version
        return self

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------

    def build(self) -> Narrative:
        """Produce an immutable Narrative. Sole creation path.

        Raises:
            ValueError: if any mandatory section is missing.
        """
        missing = []
        if self._executive_summary is None:
            missing.append("executive_summary")
        if self._strengths is None:
            missing.append("strengths")
        if self._weaknesses is None:
            missing.append("weaknesses")
        if self._growth_areas is None:
            missing.append("growth_areas")
        if self._recommendations is None:
            missing.append("recommendations")

        if missing:
            raise ValueError(
                f"NarrativeBuilder is missing mandatory sections: {missing}. "
                "All five NarrativeSectionTypes are required (ADR-023 §C)."
            )

        return Narrative(
            executive_summary=self._executive_summary,
            strengths=self._strengths,
            weaknesses=self._weaknesses,
            growth_areas=self._growth_areas,
            recommendations=self._recommendations,
            insights=tuple(self._insights),
            schema_version=self._schema_version,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_section_type(
        section: NarrativeSection,
        expected: NarrativeSectionType,
    ) -> None:
        if section.section_type != expected:
            raise ValueError(
                f"Section has section_type='{section.section_type.value}' "
                f"but expected '{expected.value}' for this builder slot."
            )
