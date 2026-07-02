# domain/contracts/observation/extraction/observation_extraction_diagnostics.py
# ADR-016: Extraction diagnostics — per-rule audit record

from pydantic import BaseModel, Field


class ObservationRuleDiagnostic(BaseModel):
    """Immutable per-rule diagnostic record for one extraction cycle.

    Records whether a rule was evaluated, whether it was skipped (applies_to
    returned False), how many matches it produced, and any error message if
    evaluation raised an exception.
    """

    rule_id: str = Field(..., min_length=1)
    evaluated: bool = Field(default=True)
    skipped: bool = Field(default=False)
    match_count: int = Field(default=0, ge=0)
    error_message: str | None = Field(default=None)

    model_config = {"frozen": True, "extra": "forbid"}


class ObservationExtractionDiagnostics(BaseModel):
    """Immutable diagnostic envelope for one complete extraction cycle.

    Produced by ObservationExtractor alongside the extraction result.
    Contains per-rule diagnostic records and aggregate statistics.

    Used for:
    - Audit: which rules fired, which were skipped, which errored.
    - Debugging: identifying rules that never match or always error.
    - Metrics: input to ObservationExtractorMetrics aggregation.
    """

    question_index: int = Field(..., ge=0)
    session_id: str = Field(..., min_length=1)
    rules_evaluated: int = Field(default=0, ge=0)
    rules_skipped: int = Field(default=0, ge=0)
    rules_errored: int = Field(default=0, ge=0)
    total_matches: int = Field(default=0, ge=0)
    rule_diagnostics: tuple[ObservationRuleDiagnostic, ...] = Field(default_factory=tuple)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_rule_diagnostics(
        cls,
        question_index: int,
        session_id: str,
        diagnostics: list[ObservationRuleDiagnostic],
    ) -> "ObservationExtractionDiagnostics":
        evaluated = sum(1 for d in diagnostics if d.evaluated and not d.skipped)
        skipped = sum(1 for d in diagnostics if d.skipped)
        errored = sum(1 for d in diagnostics if d.error_message is not None)
        matches = sum(d.match_count for d in diagnostics)
        return cls(
            question_index=question_index,
            session_id=session_id,
            rules_evaluated=evaluated,
            rules_skipped=skipped,
            rules_errored=errored,
            total_matches=matches,
            rule_diagnostics=tuple(diagnostics),
        )
