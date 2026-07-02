# tests/infrastructure/execution/test_execution_limits.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_limits import ExecutionLimits


class TestExecutionLimitsDefaults:
    def test_default_timeout(self):
        limits = ExecutionLimits()
        assert limits.timeout_ms == 5_000

    def test_default_memory(self):
        limits = ExecutionLimits()
        assert limits.memory_limit_mb == 128

    def test_default_max_output(self):
        limits = ExecutionLimits()
        assert limits.max_output_bytes == 1_048_576

    def test_default_max_processes(self):
        limits = ExecutionLimits()
        assert limits.max_processes == 1

    def test_default_max_file_descriptors(self):
        limits = ExecutionLimits()
        assert limits.max_file_descriptors == 32

    def test_network_access_false_by_default(self):
        assert ExecutionLimits().network_access is False

    def test_filesystem_write_false_by_default(self):
        assert ExecutionLimits().filesystem_write is False


class TestExecutionLimitsValidBounds:
    def test_min_timeout(self):
        limits = ExecutionLimits(timeout_ms=100)
        assert limits.timeout_ms == 100

    def test_max_timeout(self):
        limits = ExecutionLimits(timeout_ms=60_000)
        assert limits.timeout_ms == 60_000

    def test_min_memory(self):
        limits = ExecutionLimits(memory_limit_mb=16)
        assert limits.memory_limit_mb == 16

    def test_max_memory(self):
        limits = ExecutionLimits(memory_limit_mb=1024)
        assert limits.memory_limit_mb == 1024

    def test_max_processes_range(self):
        for n in range(1, 9):
            limits = ExecutionLimits(max_processes=n)
            assert limits.max_processes == n


class TestExecutionLimitsValidationErrors:
    def test_timeout_below_min(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(timeout_ms=99)

    def test_timeout_above_max(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(timeout_ms=60_001)

    def test_memory_below_min(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(memory_limit_mb=15)

    def test_memory_above_max(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(memory_limit_mb=1025)

    def test_max_output_below_min(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(max_output_bytes=1023)

    def test_max_output_above_max(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(max_output_bytes=10_485_761)

    def test_max_processes_zero(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(max_processes=0)

    def test_max_processes_above_max(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(max_processes=9)

    def test_network_access_true_raises(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(network_access=True)

    def test_filesystem_write_true_raises(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(filesystem_write=True)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ExecutionLimits(unknown_field="x")


class TestExecutionLimitsSerialization:
    def test_round_trip(self):
        limits = ExecutionLimits(timeout_ms=2000, memory_limit_mb=64)
        restored = ExecutionLimits.model_validate(limits.model_dump())
        assert restored == limits

    def test_frozen(self):
        limits = ExecutionLimits()
        with pytest.raises(ValidationError):
            limits.timeout_ms = 999
