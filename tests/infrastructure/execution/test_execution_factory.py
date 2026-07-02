# tests/infrastructure/execution/test_execution_factory.py

import uuid
import pytest

from infrastructure.execution.execution_factory import ExecutionFactory
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.execution_limits import ExecutionLimits
from infrastructure.execution.contracts.execution_environment import ExecutionEnvironment


@pytest.fixture
def factory() -> ExecutionFactory:
    return ExecutionFactory()


class TestBuildRequestBasic:
    def test_build_request_returns_execution_request(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert isinstance(req, ExecutionRequest)

    def test_build_request_sets_execution_id(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-999",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.execution_id == "exec-999"

    def test_build_request_sets_question_id(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="my-question",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.question_id == "my-question"

    def test_build_request_sets_language_id(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.language_id == "python"

    def test_build_request_sets_candidate_code(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="def foo(): pass",
            environment=python_env,
        )
        assert req.candidate_code == "def foo(): pass"

    def test_build_request_sets_environment(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.environment == python_env


class TestBuildRequestDefaults:
    def test_default_limits_applied(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.limits == ExecutionLimits()

    def test_custom_limits_applied(self, factory, python_env, strict_limits):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
            limits=strict_limits,
        )
        assert req.limits == strict_limits

    def test_hidden_test_suite_default_empty(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.hidden_test_suite == ""

    def test_visible_test_suite_default_empty(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.visible_test_suite == ""

    def test_hidden_test_suite_set(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
            hidden_test_suite="assert x == 1",
        )
        assert req.hidden_test_suite == "assert x == 1"

    def test_visible_test_suite_set(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
            visible_test_suite="print('visible')",
        )
        assert req.visible_test_suite == "print('visible')"


class TestBuildRequestValidation:
    def test_language_mismatch_raises(self, factory, js_env):
        with pytest.raises(ValueError, match="language_id"):
            factory.build_request(
                execution_id="exec-1",
                question_id="q-1",
                language_id="python",
                candidate_code="x = 1",
                environment=js_env,
            )

    def test_language_match_succeeds(self, factory, js_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="javascript",
            candidate_code="const x = 1;",
            environment=js_env,
        )
        assert req.language_id == "javascript"


class TestBuildRequestIdGeneration:
    def test_nonempty_execution_id_preserved(self, factory, python_env):
        req = factory.build_request(
            execution_id="explicit-id",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        assert req.execution_id == "explicit-id"

    def test_empty_execution_id_generates_uuid(self, factory, python_env):
        req = factory.build_request(
            execution_id="",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        uuid.UUID(req.execution_id)  # valid uuid

    def test_empty_execution_id_unique(self, factory, python_env):
        r1 = factory.build_request(
            execution_id="", question_id="q-1", language_id="python",
            candidate_code="x = 1", environment=python_env,
        )
        r2 = factory.build_request(
            execution_id="", question_id="q-1", language_id="python",
            candidate_code="x = 1", environment=python_env,
        )
        assert r1.execution_id != r2.execution_id

    def test_result_is_frozen(self, factory, python_env):
        req = factory.build_request(
            execution_id="exec-1",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 1",
            environment=python_env,
        )
        with pytest.raises(Exception):
            req.language_id = "javascript"  # type: ignore
