# domain/contracts/narrative/narrative_section_type.py
# ADR-023 Section C — NarrativeSectionType taxonomy (frozen)

from enum import Enum


class NarrativeSectionType(str, Enum):
    """Deterministic section taxonomy for a Narrative (ADR-023 §C).

    Section existence and type are determined by the algorithm, not the LLM.
    All five types are mandatory in every complete Narrative.
    """

    EXECUTIVE_SUMMARY = "executive_summary"
    STRENGTHS = "strengths"
    WEAKNESSES = "weaknesses"
    GROWTH = "growth"
    RECOMMENDATIONS = "recommendations"
