# tests/infrastructure/execution/test_execution_request.py

import pytest
from pydantic import ValidationError
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_limits import ExecutionLimits


class TestExecutionRequestConstruction:
    def test_minimal_valid(self, minimal_request):
        assert minimal_request.execution_id == "exec-001"
        assert minimal_request.question_id == "q-abc"
        assert minimal_request.language_id == "python"
        assert minimal_request.candidate_code == "def solution(): pass"

    def test_defaults(self, minimal_request):
        assert minimal_request.hidden_test_suite == ""
        assert minimal_request.visible_test_suite == ""
        assert minimal_request.schema_version == "1.0"

    def test_limits_defaults_applied(self, minimal_request):
        assert minimal_request.limits == ExecutionLimits()

    def test_custom_limits(self, python_env):
        limits = ExecutionLimits(timeout_ms=2000, memory_limit_mb=64)
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="python",
            candidate_code="pass",
            environment=python_env,
            limits=limits,
        )
        assert req.limits.timeout_ms == 2000

    def test_with_hidden_tests(self, python_env):
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="python",
            candidate_code="def f(): return 1",
            hidden_test_suite="assert f() == 1",
            environment=python_env,
        )
        assert req.hidden_test_suite == "assert f() == 1"

    def test_with_visible_tests(self, python_env):
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="python",
            candidate_code="def f(): return 1",
            visible_test_suite="assert f() == 1",
            environment=python_env,
        )
        assert req.visible_test_suite == "assert f() == 1"


class TestExecutionRequestValidation:
    def test_empty_execution_id_rejected(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRequest(
                execution_id="",
                question_id="q-x",
                language_id="python",
                candidate_code="pass",
                environment=python_env,
            )

    def test_empty_question_id_rejected(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRequest(
                execution_id="exec-x",
                question_id="",
                language_id="python",
                candidate_code="pass",
                environment=python_env,
            )

    def test_empty_candidate_code_rejected(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRequest(
                execution_id="exec-x",
                question_id="q-x",
                language_id="python",
                candidate_code="",
                environment=python_env,
            )

    def test_language_mismatch_raises(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRequest(
                execution_id="exec-x",
                question_id="q-x",
                language_id="javascript",
                candidate_code="pass",
                environment=python_env,
            )

    def test_language_match_accepted(self, js_env):
        req = ExecutionRequest(
            execution_id="exec-x",
            question_id="q-x",
            language_id="javascript",
            candidate_code="function f() {}",
            environment=js_env,
        )
        assert req.language_id == "javascript"

    def test_extra_fields_forbidden(self, python_env):
        with pytest.raises(ValidationError):
            ExecutionRequest(
                execution_id="exec-x",
                question_id="q-x",
                language_id="python",
                candidate_code="pass",
                environment=python_env,
                unknown="x",
            )


class TestExecutionRequestSerialization:
    def test_round_trip(self, minimal_request):
        restored = ExecutionRequest.model_validate(minimal_request.model_dump())
        assert restored == minimal_request

    def test_json_round_trip(self, minimal_request):
        restored = ExecutionRequest.model_validate_json(minimal_request.model_dump_json())
        assert restored == minimal_request

    def test_frozen(self, minimal_request):
        with pytest.raises(ValidationError):
            minimal_request.candidate_code = "modified"
