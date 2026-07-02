# tests/domain/contracts/observation/extraction/test_observation_extractor_metrics.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.extraction.observation_extractor_metrics import (
    ObservationExtractorMetrics,
    ObservationRuleMetric,
    ObservationTypeCount,
)
from domain.contracts.observation.observation_type import ObservationType


class TestObservationTypeCountDefaults:
    def test_count_default_zero(self):
        c = ObservationTypeCount(observation_type=ObservationType.TECHNICAL_CORRECTNESS)
        assert c.count == 0

    def test_frozen(self):
        c = ObservationTypeCount(observation_type=ObservationType.TECHNICAL_CORRECTNESS)
        with pytest.raises(ValidationError):
            c.count = 5

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationTypeCount(
                observation_type=ObservationType.TECHNICAL_CORRECTNESS,
                extra="x",  # type: ignore[call-arg]
            )

    def test_negative_count_raises(self):
        with pytest.raises(ValidationError):
            ObservationTypeCount(
                observation_type=ObservationType.TECHNICAL_CORRECTNESS,
                count=-1,
            )


class TestObservationRuleMetricDefaults:
    def test_all_defaults_zero(self):
        m = ObservationRuleMetric(rule_id="r")
        assert m.invocations == 0
        assert m.skips == 0
        assert m.errors == 0
        assert m.total_matches == 0

    def test_frozen(self):
        m = ObservationRuleMetric(rule_id="r")
        with pytest.raises(ValidationError):
            m.invocations = 5

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationRuleMetric(rule_id="r", extra="x")  # type: ignore[call-arg]

    def test_negative_invocations_raises(self):
        with pytest.raises(ValidationError):
            ObservationRuleMetric(rule_id="r", invocations=-1)


class TestObservationRuleMetricProperties:
    def test_match_rate_zero_invocations(self):
        m = ObservationRuleMetric(rule_id="r")
        assert m.match_rate == 0.0

    def test_match_rate_all_skipped(self):
        m = ObservationRuleMetric(rule_id="r", invocations=5, skips=5)
        assert m.match_rate == 0.0

    def test_match_rate_normal(self):
        m = ObservationRuleMetric(rule_id="r", invocations=10, skips=0, total_matches=7)
        assert m.match_rate == pytest.approx(0.7)

    def test_match_rate_capped_at_one(self):
        # More matches than invocations (e.g. multi-match rules)
        m = ObservationRuleMetric(rule_id="r", invocations=2, skips=0, total_matches=10)
        assert m.match_rate == pytest.approx(1.0)

    def test_error_rate_zero_invocations(self):
        m = ObservationRuleMetric(rule_id="r")
        assert m.error_rate == 0.0

    def test_error_rate_normal(self):
        m = ObservationRuleMetric(rule_id="r", invocations=10, errors=3)
        assert m.error_rate == pytest.approx(0.3)

    def test_error_rate_all_errors(self):
        m = ObservationRuleMetric(rule_id="r", invocations=5, errors=5)
        assert m.error_rate == pytest.approx(1.0)


class TestObservationExtractorMetricsDefaults:
    def test_all_counts_default_zero(self):
        m = ObservationExtractorMetrics(session_id="s")
        assert m.total_cycles == 0
        assert m.total_observations_produced == 0
        assert m.total_rules_evaluated == 0
        assert m.total_rules_skipped == 0
        assert m.total_rules_errored == 0

    def test_schema_version_default(self):
        m = ObservationExtractorMetrics(session_id="s")
        assert m.schema_version == "1.0"

    def test_frozen(self):
        m = ObservationExtractorMetrics(session_id="s")
        with pytest.raises(ValidationError):
            m.total_cycles = 5

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationExtractorMetrics(session_id="s", extra="x")  # type: ignore[call-arg]


class TestObservationExtractorMetricsProperties:
    def test_average_observations_zero_cycles(self):
        m = ObservationExtractorMetrics(session_id="s")
        assert m.average_observations_per_cycle == 0.0

    def test_average_observations_normal(self):
        m = ObservationExtractorMetrics(
            session_id="s",
            total_cycles=4,
            total_observations_produced=12,
        )
        assert m.average_observations_per_cycle == pytest.approx(3.0)

    def test_overall_error_rate_zero(self):
        m = ObservationExtractorMetrics(session_id="s")
        assert m.overall_error_rate == 0.0

    def test_overall_error_rate_normal(self):
        m = ObservationExtractorMetrics(
            session_id="s",
            total_rules_evaluated=8,
            total_rules_skipped=2,
            total_rules_errored=2,
        )
        assert m.overall_error_rate == pytest.approx(0.2)
