# tests/infrastructure/execution/test_execution_routing_result.py

import pytest
from pydantic import BaseModel

from infrastructure.execution.execution_routing_result import ExecutionRoutingResult


class TestExecutionRoutingResultCreation:
    def test_create_success_routing(self):
        result = ExecutionRoutingResult(
            success=True,
            language_id="python",
            executor_available=True,
        )
        assert result.success is True
        assert result.language_id == "python"
        assert result.executor_available is True

    def test_create_failed_routing(self):
        result = ExecutionRoutingResult(
            success=False,
            language_id="ruby",
            executor_available=False,
            routing_errors=["No executor for ruby"],
        )
        assert result.success is False
        assert result.executor_available is False
        assert len(result.routing_errors) == 1

    def test_defaults_applied(self):
        result = ExecutionRoutingResult(
            success=True,
            language_id="python",
            executor_available=True,
        )
        assert result.routing_errors == []
        assert result.routing_metadata == {}

    def test_routing_metadata_stored(self):
        result = ExecutionRoutingResult(
            success=True,
            language_id="python",
            executor_available=True,
            routing_metadata={"key": "value"},
        )
        assert result.routing_metadata["key"] == "value"

    def test_routing_errors_stored(self):
        result = ExecutionRoutingResult(
            success=False,
            language_id="python",
            executor_available=False,
            routing_errors=["err1", "err2"],
        )
        assert result.routing_errors == ["err1", "err2"]


class TestExecutionRoutingResultImmutability:
    def test_is_frozen(self):
        result = ExecutionRoutingResult(
            success=True,
            language_id="python",
            executor_available=True,
        )
        with pytest.raises(Exception):
            result.success = False  # type: ignore

    def test_is_pydantic_model(self):
        result = ExecutionRoutingResult(
            success=True,
            language_id="python",
            executor_available=True,
        )
        assert isinstance(result, BaseModel)

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            ExecutionRoutingResult(
                success=True,
                language_id="python",
                executor_available=True,
                unknown="x",
            )


class TestExecutionRoutingResultFields:
    def test_language_id_stored(self):
        result = ExecutionRoutingResult(
            success=True,
            language_id="typescript",
            executor_available=True,
        )
        assert result.language_id == "typescript"

    def test_executor_available_false(self):
        result = ExecutionRoutingResult(
            success=False,
            language_id="python",
            executor_available=False,
        )
        assert result.executor_available is False

    def test_multiple_routing_errors(self):
        errors = ["err1", "err2", "err3"]
        result = ExecutionRoutingResult(
            success=False,
            language_id="python",
            executor_available=False,
            routing_errors=errors,
        )
        assert result.routing_errors == errors

    def test_empty_routing_errors(self):
        result = ExecutionRoutingResult(
            success=True,
            language_id="python",
            executor_available=True,
            routing_errors=[],
        )
        assert result.routing_errors == []

    def test_routing_metadata_multiple_entries(self):
        meta = {"a": "1", "b": "2", "c": "3"}
        result = ExecutionRoutingResult(
            success=True,
            language_id="python",
            executor_available=True,
            routing_metadata=meta,
        )
        assert result.routing_metadata == meta
