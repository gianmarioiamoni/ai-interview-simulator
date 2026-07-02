# domain/contracts/observation/extraction/observation_rule_match.py
# ADR-016: Rule match result — immutable evidence output from a single rule

from pydantic import BaseModel, Field, field_validator

from domain.contracts.observation.observation_type import ObservationType


class ObservationRuleMatch(BaseModel):
    """Immutable result produced by a single ObservationRule evaluation.

    A rule match represents the rule's determination that an Observation of
    a specific type should be created, along with the supporting evidence.

    Invariants:
    - rule_id identifies the producing rule; must be non-empty.
    - observation_type specifies which Observation type to create.
    - confidence is in [0.0, 1.0].
    - description is a system-generated label; NEVER contains candidate text
      (ADR-035 security constraint inherited from Observation).
    - tags propagate to the resulting Observation.
    - rationale is an internal diagnostic string for audit/metrics only; never
      surfaced to the candidate.
    """

    rule_id: str = Field(..., min_length=1, description="ID of the rule that produced this match")
    observation_type: ObservationType
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: str = Field(..., min_length=1, max_length=500)
    tags: frozenset[str] = Field(default_factory=frozenset)
    rationale: str = Field(
        default="",
        max_length=1000,
        description="Internal diagnostic; not surfaced to the candidate",
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("description")
    @classmethod
    def _strip_description(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("description must not be blank")
        return stripped

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v: object) -> frozenset[str]:
        if v is None:
            return frozenset()
        if isinstance(v, (list, set, tuple)):
            return frozenset(str(t) for t in v)
        if isinstance(v, frozenset):
            return v
        raise ValueError(f"tags must be a collection of strings, got {type(v)}")
