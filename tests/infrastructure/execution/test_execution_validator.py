# tests/infrastructure/execution/test_execution_validator.py

import pytest

from infrastructure.execution.execution_validator import ExecutionValidator
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment
from infrastructure.execution.contracts.execution_limits import ExecutionLimits


@pytest.fixture
def validator() -> ExecutionValidator:
    return ExecutionValidator()


def make_request(
    execution_id: str = "exec-1",
    question_id: str = "q-1",
    language_id: str = "python",
    candidate_code: str = "x = 1",
    env: ExecutionEnvironment | None = None,
    limits: ExecutionLimits | None = None,
) -> ExecutionRequest:
    if env is None:
        env = ExecutionEnvironment(
            language_id=language_id,
            runtime_id="cpython-3.12",
            runtime_version="3.12",
            sandbox_type="subprocess",
        )
    if limits is None:
        limits = ExecutionLimits()
    return ExecutionRequest(
        execution_id=execution_id,
        question_id=question_id,
        language_id=language_id,
        candidate_code=candidate_code,
        environment=env,
        limits=limits,
    )


class TestValidatorValidRequest:
    def test_valid_request_no_errors(self, validator, minimal_request):
        errors = validator.validate(minimal_request)
        assert errors == []

    def test_valid_request_returns_list(self, validator, minimal_request):
        errors = validator.validate(minimal_request)
        assert isinstance(errors, list)

    def test_valid_request_with_test_suites(self, validator, python_env):
        req = ExecutionRequest(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            hidden_test_suite="assert x == 1",
            visible_test_suite="print(x)",
            environment=python_env,
        )
        assert validator.validate(req) == []


class TestValidatorCandidateCode:
    def test_note_tested_here_code_empty_caught_by_pydantic(self, validator, python_env):
        """ExecutionRequest rejects empty code via pydantic - validate sees only valid requests."""
        with pytest.raises(Exception):
            ExecutionRequest(
                execution_id="exec-1",
                question_id="q-1",
                language_id="python",
                candidate_code="   ",
                environment=python_env,
            )


class TestValidatorLimits:
    def test_valid_limits_no_errors(self, validator, python_env):
        limits = ExecutionLimits(timeout_ms=5000, memory_limit_mb=128)
        req = make_request(limits=limits)
        assert validator.validate(req) == []

    def test_network_access_must_be_false(self, validator, python_env):
        """Pydantic enforces network_access=False at construction. Additional coverage."""
        with pytest.raises(Exception):
            ExecutionLimits(network_access=True)

    def test_filesystem_write_must_be_false(self, validator, python_env):
        with pytest.raises(Exception):
            ExecutionLimits(filesystem_write=True)


class TestValidatorLanguageId:
    def test_valid_language_id_no_errors(self, validator, minimal_request):
        errors = validator.validate(minimal_request)
        assert not any("language_id" in e for e in errors)

    def test_language_matches_environment(self, validator, python_env):
        req = make_request(language_id="python", env=python_env)
        assert validator.validate(req) == []


class TestValidatorExecutionId:
    def test_valid_execution_id_no_errors(self, validator, minimal_request):
        errors = validator.validate(minimal_request)
        assert errors == []


class TestValidatorReturnType:
    def test_returns_list_of_strings(self, validator, minimal_request):
        errors = validator.validate(minimal_request)
        assert isinstance(errors, list)
        assert all(isinstance(e, str) for e in errors)

    def test_empty_means_valid(self, validator, minimal_request):
        errors = validator.validate(minimal_request)
        assert len(errors) == 0


class TestValidatorMultipleErrors:
    def test_multiple_valid_requests(self, validator, python_env, js_env):
        py_req = make_request(language_id="python", env=python_env)
        js_req = make_request(language_id="javascript", env=js_env, candidate_code="const x = 1;")
        assert validator.validate(py_req) == []
        assert validator.validate(js_req) == []

    def test_deterministic_validation(self, validator, minimal_request):
        r1 = validator.validate(minimal_request)
        r2 = validator.validate(minimal_request)
        assert r1 == r2


class TestValidatorBoundaryLimits:
    def test_min_timeout_valid(self, validator, python_env):
        limits = ExecutionLimits(timeout_ms=100)
        req = make_request(limits=limits)
        assert validator.validate(req) == []

    def test_max_timeout_valid(self, validator, python_env):
        limits = ExecutionLimits(timeout_ms=60_000)
        req = make_request(limits=limits)
        assert validator.validate(req) == []

    def test_min_memory_valid(self, validator, python_env):
        limits = ExecutionLimits(memory_limit_mb=16)
        req = make_request(limits=limits)
        assert validator.validate(req) == []

    def test_max_memory_valid(self, validator, python_env):
        limits = ExecutionLimits(memory_limit_mb=1024)
        req = make_request(limits=limits)
        assert validator.validate(req) == []

    def test_min_output_bytes_valid(self, validator, python_env):
        limits = ExecutionLimits(max_output_bytes=1024)
        req = make_request(limits=limits)
        assert validator.validate(req) == []

    def test_max_output_bytes_valid(self, validator, python_env):
        limits = ExecutionLimits(max_output_bytes=10_485_760)
        req = make_request(limits=limits)
        assert validator.validate(req) == []
