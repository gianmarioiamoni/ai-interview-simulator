# tests/infrastructure/execution/test_execution_metrics.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_metrics import ExecutionMetrics


class TestExecutionMetricsDefaults:
    def test_all_defaults_zero(self):
        m = ExecutionMetrics()
        assert m.duration_ms == 0
        assert m.cpu_time_ms == 0
        assert m.peak_memory_kb == 0
        assert m.stdout_bytes == 0
        assert m.stderr_bytes == 0
        assert m.tests_total == 0
        assert m.tests_passed == 0
        assert m.tests_failed == 0
        assert m.tests_errored == 0
        assert m.retry_count == 0


class TestExecutionMetricsValidation:
    def test_valid_counts(self):
        m = ExecutionMetrics(
            duration_ms=100,
            tests_total=5,
            tests_passed=3,
            tests_failed=1,
            tests_errored=1,
        )
        assert m.tests_total == 5

    def test_count_mismatch_raises(self):
        with pytest.raises(ValidationError):
            ExecutionMetrics(
                tests_total=5,
                tests_passed=3,
                tests_failed=1,
                tests_errored=0,
            )

    def test_zero_total_allows_zero_components(self):
        m = ExecutionMetrics(
            tests_total=0,
            tests_passed=0,
            tests_failed=0,
            tests_errored=0,
        )
        assert m.tests_total == 0

    def test_negative_duration_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionMetrics(duration_ms=-1)

    def test_negative_cpu_time_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionMetrics(cpu_time_ms=-1)

    def test_negative_memory_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionMetrics(peak_memory_kb=-1)

    def test_negative_retry_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionMetrics(retry_count=-1)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ExecutionMetrics(unknown=1)


class TestExecutionMetricsProperties:
    def test_pass_rate_all_pass(self):
        m = ExecutionMetrics(
            tests_total=4,
            tests_passed=4,
            tests_failed=0,
            tests_errored=0,
        )
        assert m.pass_rate == 1.0

    def test_pass_rate_none_pass(self):
        m = ExecutionMetrics(
            tests_total=4,
            tests_passed=0,
            tests_failed=4,
            tests_errored=0,
        )
        assert m.pass_rate == 0.0

    def test_pass_rate_partial(self):
        m = ExecutionMetrics(
            tests_total=4,
            tests_passed=2,
            tests_failed=2,
            tests_errored=0,
        )
        assert m.pass_rate == pytest.approx(0.5)

    def test_pass_rate_zero_total(self):
        assert ExecutionMetrics().pass_rate == 0.0

    def test_memory_limit_ratio_zero(self):
        assert ExecutionMetrics().memory_limit_ratio == 0.0

    def test_memory_limit_ratio_capped_at_one(self):
        m = ExecutionMetrics(peak_memory_kb=10_000_000)
        assert m.memory_limit_ratio == 1.0

    def test_memory_limit_ratio_partial(self):
        m = ExecutionMetrics(peak_memory_kb=524_288)
        assert m.memory_limit_ratio == pytest.approx(0.5)


class TestExecutionMetricsSerialization:
    def test_round_trip(self, success_metrics):
        restored = ExecutionMetrics.model_validate(success_metrics.model_dump())
        assert restored == success_metrics

    def test_json_round_trip(self, success_metrics):
        restored = ExecutionMetrics.model_validate_json(success_metrics.model_dump_json())
        assert restored == success_metrics

    def test_frozen(self):
        m = ExecutionMetrics()
        with pytest.raises(ValidationError):
            m.duration_ms = 100
