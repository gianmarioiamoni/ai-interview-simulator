# domain/contracts/report/scoring_narrative.py

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.report.scoring_narrative_item import ScoringNarrativeItem


class ScoringNarrative(BaseModel):
    """Immutable LLM-generated hiring-context narrative for a completed session.

    A Projection Artifact (PAT-04): carries all prose previously held by
    InterviewEvaluation (executive_summary, went_well, held_you_back,
    knowledge_gaps, next_strategy, improvement_suggestions).

    Produced by EvaluationNarrativeAssembler via InterviewEvaluationService.
    Not a replacement for Report.narrative (knowledge-pipeline artifact) —
    those two are separate pipelines with distinct semantics.
    """

    model_config = {"frozen": True, "extra": "forbid"}

    executive_summary: str = Field(min_length=1)
    went_well: tuple[str, ...] = Field(default_factory=tuple)
    held_you_back: tuple[ScoringNarrativeItem, ...] = Field(default_factory=tuple)
    knowledge_gaps: tuple[ScoringNarrativeItem, ...] = Field(default_factory=tuple)
    next_strategy: tuple[ScoringNarrativeItem, ...] = Field(default_factory=tuple)
    improvement_suggestions: tuple[str, ...] = Field(default_factory=tuple)
    schema_version: str = Field(default="1.0", min_length=1)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_items_non_empty_fields(self) -> "ScoringNarrative":
        # V-SN-02: each ScoringNarrativeItem in all four sections must have
        # non-empty category, description, why_it_matters.
        # (Field-level min_length=1 on ScoringNarrativeItem already enforces
        # this at item construction; this validator is an aggregate guard.)
        for section_name, items in (
            ("held_you_back", self.held_you_back),
            ("knowledge_gaps", self.knowledge_gaps),
            ("next_strategy", self.next_strategy),
        ):
            for item in items:
                if not item.category or not item.description or not item.why_it_matters:
                    raise ValueError(
                        f"ScoringNarrative.{section_name}: every item must have "
                        f"non-empty category, description, why_it_matters (V-SN-02)"
                    )
        return self
