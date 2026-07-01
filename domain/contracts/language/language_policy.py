# domain/contracts/language/language_policy.py

from pydantic import BaseModel, Field


class LanguagePolicy(BaseModel):
    """Language-specific evaluation configuration artifact.

    Governs idiom recognition, type error classification, and import
    allowlist/blocklist for a specific programming language and policy version.

    Domain invariants (ADR-019):
    - I-13: LanguagePolicy NEVER modifies EvaluationDimension weights.
    - I-21: LanguagePolicy is read-only at runtime. Changes require a new policy_version.
    - I-23: All coding questions must be solvable with standard library imports only.

    LanguagePolicy is a static configuration artifact — not a runtime decision maker.
    It informs EvaluationEngine of language idioms; EvaluationEngine applies the
    policy but never delegates scoring logic to it.
    """

    language_id: str = Field(
        ..., min_length=1, description="Language this policy applies to"
    )
    policy_version: str = Field(
        ..., min_length=1, description="Immutable version identifier; changes require new policy"
    )
    recognised_idioms: list[str] = Field(
        default_factory=list,
        description="Language idioms that the evaluator should recognise as correct (not penalise)"
    )
    type_error_patterns: list[str] = Field(
        default_factory=list,
        description="Language-specific type error patterns to classify (e.g. TypeError in Python)"
    )
    import_allowlist: list[str] = Field(
        default_factory=list,
        description="Standard library modules permitted in candidate solutions"
    )
    import_blocklist: list[str] = Field(
        default_factory=list,
        description="Modules explicitly forbidden (e.g. os, subprocess, socket)"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
