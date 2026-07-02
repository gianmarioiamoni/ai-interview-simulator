# tests/infrastructure/execution/test_execution_environment.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment


class TestExecutionEnvironmentConstruction:
    def test_minimal_valid(self):
        env = ExecutionEnvironment(
            language_id="python",
            runtime_id="cpython-3.12",
            runtime_version="3.12.0",
            sandbox_type="subprocess",
        )
        assert env.language_id == "python"
        assert env.runtime_id == "cpython-3.12"
        assert env.runtime_version == "3.12.0"
        assert env.sandbox_type == "subprocess"

    def test_defaults(self):
        env = ExecutionEnvironment(
            language_id="javascript",
            runtime_id="nodejs-22",
            runtime_version="22.0.0",
            sandbox_type="subprocess",
        )
        assert env.import_allowlist == []
        assert env.import_blocklist == []
        assert env.env_vars == {}
        assert env.schema_version == "1.0"

    def test_allowlist_accepted(self):
        env = ExecutionEnvironment(
            language_id="python",
            runtime_id="cpython-3.12",
            runtime_version="3.12.0",
            sandbox_type="subprocess",
            import_allowlist=["math", "collections"],
        )
        assert env.import_allowlist == ["math", "collections"]

    def test_blocklist_accepted(self):
        env = ExecutionEnvironment(
            language_id="python",
            runtime_id="cpython-3.12",
            runtime_version="3.12.0",
            sandbox_type="subprocess",
            import_blocklist=["os", "subprocess"],
        )
        assert env.import_blocklist == ["os", "subprocess"]

    def test_env_vars_accepted(self):
        env = ExecutionEnvironment(
            language_id="python",
            runtime_id="cpython-3.12",
            runtime_version="3.12.0",
            sandbox_type="subprocess",
            env_vars={"PYTHONPATH": "/app"},
        )
        assert env.env_vars == {"PYTHONPATH": "/app"}


class TestExecutionEnvironmentValidation:
    def test_empty_language_id_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionEnvironment(
                language_id="",
                runtime_id="cpython-3.12",
                runtime_version="3.12.0",
                sandbox_type="subprocess",
            )

    def test_empty_runtime_id_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionEnvironment(
                language_id="python",
                runtime_id="",
                runtime_version="3.12.0",
                sandbox_type="subprocess",
            )

    def test_allowlist_blocklist_overlap_raises(self):
        with pytest.raises(ValidationError):
            ExecutionEnvironment(
                language_id="python",
                runtime_id="cpython-3.12",
                runtime_version="3.12.0",
                sandbox_type="subprocess",
                import_allowlist=["os", "math"],
                import_blocklist=["os"],
            )

    def test_disjoint_allowlist_blocklist_accepted(self):
        env = ExecutionEnvironment(
            language_id="python",
            runtime_id="cpython-3.12",
            runtime_version="3.12.0",
            sandbox_type="subprocess",
            import_allowlist=["math"],
            import_blocklist=["os"],
        )
        assert env.import_allowlist == ["math"]
        assert env.import_blocklist == ["os"]

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ExecutionEnvironment(
                language_id="python",
                runtime_id="cpython-3.12",
                runtime_version="3.12.0",
                sandbox_type="subprocess",
                unknown="x",
            )


class TestExecutionEnvironmentSerialization:
    def test_round_trip(self, python_env):
        restored = ExecutionEnvironment.model_validate(python_env.model_dump())
        assert restored == python_env

    def test_json_round_trip(self, python_env):
        restored = ExecutionEnvironment.model_validate_json(python_env.model_dump_json())
        assert restored == python_env

    def test_frozen(self, python_env):
        with pytest.raises(ValidationError):
            python_env.language_id = "javascript"
