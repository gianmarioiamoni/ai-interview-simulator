# tests/domain/contracts/language/test_execution_policy.py

import pytest
from pydantic import ValidationError

from domain.contracts.language.execution_policy import ExecutionPolicy


def _make_policy(**overrides) -> ExecutionPolicy:
    defaults = dict(language_id="python")
    defaults.update(overrides)
    return ExecutionPolicy(**defaults)


class TestExecutionPolicyConstruction:
    def test_minimal_construction(self):
        p = _make_policy()
        assert p.language_id == "python"
        assert p.timeout_ms == 5000
        assert p.memory_limit_mb == 128
        assert p.max_retry_on_transient_error == 1
        assert p.import_allowlist == []
        assert p.schema_version == "1.0"

    def test_explicit_timeout(self):
        p = _make_policy(timeout_ms=10_000)
        assert p.timeout_ms == 10_000

    def test_explicit_memory(self):
        p = _make_policy(memory_limit_mb=256)
        assert p.memory_limit_mb == 256

    def test_with_allowlist(self):
        p = _make_policy(import_allowlist=["os.path", "math", "collections"])
        assert "math" in p.import_allowlist

    def test_retry_zero_allowed(self):
        p = _make_policy(max_retry_on_transient_error=0)
        assert p.max_retry_on_transient_error == 0

    def test_max_retry_three_allowed(self):
        p = _make_policy(max_retry_on_transient_error=3)
        assert p.max_retry_on_transient_error == 3


class TestExecutionPolicyValidation:
    def test_empty_language_id_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(language_id="")

    def test_timeout_below_minimum_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(timeout_ms=50)

    def test_timeout_above_maximum_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(timeout_ms=120_000)

    def test_memory_below_minimum_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(memory_limit_mb=10)

    def test_memory_above_maximum_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(memory_limit_mb=2048)

    def test_retry_above_maximum_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(max_retry_on_transient_error=5)

    def test_retry_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(max_retry_on_transient_error=-1)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            _make_policy(sandbox_type="docker")


class TestExecutionPolicyImmutability:
    def test_language_id_frozen(self):
        p = _make_policy()
        with pytest.raises((ValidationError, TypeError)):
            p.language_id = "javascript"

    def test_timeout_frozen(self):
        p = _make_policy()
        with pytest.raises((ValidationError, TypeError)):
            p.timeout_ms = 1000


class TestExecutionPolicySerialization:
    def test_roundtrip(self):
        p = _make_policy(timeout_ms=3000, memory_limit_mb=64)
        data = p.model_dump()
        p2 = ExecutionPolicy(**data)
        assert p == p2

    def test_json_roundtrip(self):
        p = _make_policy(import_allowlist=["math"])
        json_str = p.model_dump_json()
        p2 = ExecutionPolicy.model_validate_json(json_str)
        assert p == p2
