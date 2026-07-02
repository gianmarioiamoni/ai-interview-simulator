# domain/contracts/observation/extraction/observation_extractor_metrics.py
# ADR-016: Extractor metrics — session-level aggregated telemetry

from pydantic import BaseModel, Field

from domain.contracts.observation.observation_type import ObservationType


class ObservationTypeCount(BaseModel):
    """Count of Observations produced for one ObservationType in a session."""

    observation_type: ObservationType
    count: int = Field(default=0, ge=0)

    model_config = {"frozen": True, "extra": "forbid"}


class ObservationRuleMetric(BaseModel):
    """Aggregated performance metrics for one rule across a session."""

    rule_id: str = Field(..., min_length=1)
    invocations: int = Field(default=0, ge=0)
    skips: int = Field(default=0, ge=0)
    errors: int = Field(default=0, ge=0)
    total_matches: int = Field(default=0, ge=0)

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def match_rate(self) -> float:
        """Fraction of invocations that produced at least one match."""
        effective = self.invocations - self.skips
        if effective == 0:
            return 0.0
        return min(self.total_matches / effective, 1.0)

    @property
    def error_rate(self) -> float:
        """Fraction of invocations that raised an error."""
        if self.invocations == 0:
            return 0.0
        return self.errors / self.invocations


class ObservationExtractorMetrics(BaseModel):
    """Immutable session-level telemetry for ObservationExtractor.

    Aggregated across all extraction cycles for the session.
    Produced by ObservationExtractor.session_metrics() at any point
    during or after the session.

    Invariants:
    - total_cycles >= 0.
    - total_observations_produced >= 0.
    - rule_metrics has one entry per registered rule.
    - type_counts has one entry per ObservationType that was produced ≥ 1 time.
    """

    session_id: str = Field(..., min_length=1)
    total_cycles: int = Field(default=0, ge=0)
    total_observations_produced: int = Field(default=0, ge=0)
    total_rules_evaluated: int = Field(default=0, ge=0)
    total_rules_skipped: int = Field(default=0, ge=0)
    total_rules_errored: int = Field(default=0, ge=0)
    rule_metrics: tuple[ObservationRuleMetric, ...] = Field(default_factory=tuple)
    type_counts: tuple[ObservationTypeCount, ...] = Field(default_factory=tuple)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def average_observations_per_cycle(self) -> float:
        if self.total_cycles == 0:
            return 0.0
        return self.total_observations_produced / self.total_cycles

    @property
    def overall_error_rate(self) -> float:
        denom = self.total_rules_evaluated + self.total_rules_skipped
        if denom == 0:
            return 0.0
        return self.total_rules_errored / denom
