# domain/contracts/feature/feature_quality.py
# Feature quality envelope — confidence, stability, maturity (ADR-018 §J, ADR-020 §I)

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Module-level constants (Pydantic BaseModel does not allow class-level str attrs)
# ---------------------------------------------------------------------------

STABILITY_STABLE = "stable"
STABILITY_UNSTABLE = "unstable"
STABILITY_EMERGING = "emerging"
_VALID_STABILITY_STATES: frozenset[str] = frozenset({STABILITY_STABLE, STABILITY_UNSTABLE, STABILITY_EMERGING})

MATURITY_NASCENT = "nascent"
MATURITY_DEVELOPING = "developing"
MATURITY_MATURE = "mature"
_VALID_MATURITY_STAGES: frozenset[str] = frozenset({MATURITY_NASCENT, MATURITY_DEVELOPING, MATURITY_MATURE})


class FeatureConfidence(BaseModel):
    """Feature certainty in [0.0, 1.0] (ADR-018 §J).

    Below 0.3 is considered low-confidence.
    Recomputed on every FeatureEngine cycle — never stored across cycles.
    """

    value: float = Field(..., ge=0.0, le=1.0, description="Confidence in [0.0, 1.0]")
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def is_low(self) -> bool:
        """True when confidence is below the low-confidence threshold (< 0.3)."""
        return self.value < 0.3


class FeatureStability(BaseModel):
    """Cycle-over-cycle value consistency (ADR-018 §J, ADR-020 §I).

    STABLE   — unchanged direction across last N cycles (default N = 3).
    UNSTABLE — value direction has oscillated across recent cycles.
    EMERGING — fewer than N prior cycles available (early in session).
    """

    state: str = Field(
        ...,
        description="One of: 'stable', 'unstable', 'emerging'",
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    def model_post_init(self, __context: object) -> None:
        if self.state not in _VALID_STABILITY_STATES:
            raise ValueError(
                f"FeatureStability.state must be one of {sorted(_VALID_STABILITY_STATES)}; got '{self.state}'"
            )


class FeatureMaturity(BaseModel):
    """Evidence-accumulation stage (ADR-018 §J, ADR-020 §I).

    NASCENT    — 1–2 source Observations.
    DEVELOPING — 3–5 source Observations.
    MATURE     — 6+ source Observations with consistent direction.
    """

    stage: str = Field(
        ...,
        description="One of: 'nascent', 'developing', 'mature'",
    )
    observation_count: int = Field(..., ge=1, description="Number of source Observations")
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    def model_post_init(self, __context: object) -> None:
        if self.stage not in _VALID_MATURITY_STAGES:
            raise ValueError(
                f"FeatureMaturity.stage must be one of {sorted(_VALID_MATURITY_STAGES)}; got '{self.stage}'"
            )

    @classmethod
    def from_observation_count(cls, count: int) -> "FeatureMaturity":
        """Derive maturity stage from observation count per ADR-018 §J milestones."""
        if count <= 0:
            raise ValueError("observation_count must be >= 1")
        if count <= 2:
            stage = MATURITY_NASCENT
        elif count <= 5:
            stage = MATURITY_DEVELOPING
        else:
            stage = MATURITY_MATURE
        return cls(stage=stage, observation_count=count)


class FeatureQuality(BaseModel):
    """Composite quality envelope attached to every ProfileFeature (ADR-018 §J).

    Carries confidence, stability, and maturity as computed by FeatureEngine.
    All properties are derived — none stored independently across cycles.
    """

    confidence: FeatureConfidence
    stability: FeatureStability
    maturity: FeatureMaturity
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
