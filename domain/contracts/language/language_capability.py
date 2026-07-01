# domain/contracts/language/language_capability.py

from pydantic import BaseModel, Field


class LanguageCapability(BaseModel):
    """Language-specific ability summary for a candidate within one session.

    Represents the candidate's demonstrated competence in a specific language
    during this session — derived from coding evaluation signals for that language.

    In V1.2, LanguageCapability is session-scoped and derived. It is the
    precursor to LanguageCapabilityFeature (ProfileFeature layer, ADR-018 §D).

    Domain invariants:
    - language_id references a registered ProgrammingLanguage (ADR-019 I-20).
    - score is language-agnostic: it uses the same EvaluationDimension rubric
      regardless of language (ADR-019 I-06).
    - Capability does NOT alter dimension weights.
    """

    language_id: str = Field(
        ..., min_length=1, description="Language this capability describes"
    )
    questions_answered_in_language: int = Field(
        default=0, ge=0,
        description="Number of coding questions answered in this language in the session"
    )
    # Normalised [0.0, 1.0] composite score across all dimension evaluations
    # for questions in this language. Language-agnostic rubric (ADR-019 I-06).
    composite_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Normalised composite score across dimension evaluations for this language"
    )
    idiomatic_usage_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Score for language-idiomatic construct usage (LanguagePolicy-informed)"
    )
    type_error_rate: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Rate of type errors observed; lower is better"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
