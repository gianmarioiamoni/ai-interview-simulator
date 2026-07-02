# tests/infrastructure/execution/test_execution_runtime.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
from infrastructure.execution.contracts.execution_limits import ExecutionLimits


class TestExecutionRuntimeConstruction:
    def test_minimal_valid(self, python_env):
        rt = ExecutionRuntime(
            environment=python_env,
            runtime_label="python-3.12-subprocess",
        )
        assert rt.runtime_label == "python-3.12-subprocess"
        assert rt.supports_compilation is False
        assert rt.supports_coverage is False

    def test_defaults(self, python_env):
        rt = ExecutionRuntime(
            environment=python_env,
            runtime_label="python-3.12-subprocess",
        )
        assert rt.limits == ExecutionLimits()
        assert rt.schema_version == "1.0"

    def test_typescript_compilation_flag(self, ts_env):
        rt = ExecutionRuntime(
            environment=ts_env,
            runtime_label="ts-5.4-nodejs-22",
            supports_compilation=True,
        )
        assert rt.supports_compilation is True

    def test_custom_limits_accepted(self, python_env):
        limits = ExecutionLimits(timeout_ms=10_000)
        rt = ExecutionRuntime(
            environment=python_env,
            limits=limits,
            runtime_label="python-3.12-subprocess",
        )
        assert rt.limits.timeout_ms == 10_000


class TestExecutionRuntimeProperties:
    def test_language_id_property(self, python_runtime):
        assert python_runtime.language_id == "python"

    def test_runtime_id_property(self, python_runtime):
        assert python_runtime.runtime_id == "cpython-3.12"


class TestExecutionRuntimeValidation:
    def test_empty_runtime_label_rejected(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRuntime(
                environment=python_env,
                runtime_label="",
            )

    def test_extra_fields_forbidden(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRuntime(
                environment=python_env,
                runtime_label="label",
                unknown="x",
            )

    def test_frozen(self, python_runtime):
        with pytest.raises(ValidationError):
            python_runtime.runtime_label = "changed"


class TestExecutionRuntimeSerialization:
    def test_round_trip(self, python_runtime):
        restored = ExecutionRuntime.model_validate(python_runtime.model_dump())
        assert restored == python_runtime

    def test_json_round_trip(self, python_runtime):
        restored = ExecutionRuntime.model_validate_json(python_runtime.model_dump_json())
        assert restored == python_runtime
