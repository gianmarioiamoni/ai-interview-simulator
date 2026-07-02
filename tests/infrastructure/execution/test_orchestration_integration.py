# tests/infrastructure/execution/test_orchestration_integration.py

import pytest

from infrastructure.execution.language_executor_registry import LanguageExecutorRegistry
from infrastructure.execution.execution_dispatcher import ExecutionDispatcher
from infrastructure.execution.execution_pipeline import ExecutionPipeline
from infrastructure.execution.execution_factory import ExecutionFactory
from infrastructure.execution.execution_context import ExecutionContext
from infrastructure.execution.execution_lifecycle import ExecutionLifecycle, ExecutionPhase
from infrastructure.execution.execution_validator import ExecutionValidator
from infrastructure.execution.execution_routing_result import ExecutionRoutingResult
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_result import ExecutionResult
from infrastructure.execution.contracts.execution_runtime import ExecutionRuntime
from infrastructure.execution.contracts.execution_request import ExecutionRequest
from infrastructure.execution.contracts.language_executor import LanguageExecutor


def make_mock_executor(lang_id: str, runtime: ExecutionRuntime, available: bool = True, status: ExecutionStatus = ExecutionStatus.SUCCESS) -> LanguageExecutor:
    class MockExecutor(LanguageExecutor):
        @property
        def language_id(self) -> str:
            return lang_id

        @property
        def runtime(self) -> ExecutionRuntime:
            return runtime

        def execute(self, request: ExecutionRequest) -> ExecutionResult:
            return ExecutionResult(
                execution_id=request.execution_id,
                language_id=request.language_id,
                question_id=request.question_id,
                status=status,
            )

        def is_available(self) -> bool:
            return available

    return MockExecutor()


@pytest.fixture
def python_runtime(python_env, default_limits) -> ExecutionRuntime:
    return ExecutionRuntime(
        environment=python_env,
        limits=default_limits,
        runtime_label="python-3.12",
    )


@pytest.fixture
def js_runtime(js_env, default_limits) -> ExecutionRuntime:
    return ExecutionRuntime(
        environment=js_env,
        limits=default_limits,
        runtime_label="nodejs-22",
    )


@pytest.fixture
def full_registry(python_runtime, js_runtime) -> LanguageExecutorRegistry:
    registry = LanguageExecutorRegistry()
    registry.register(make_mock_executor("python", python_runtime))
    registry.register(make_mock_executor("javascript", js_runtime))
    return registry


@pytest.fixture
def full_pipeline(full_registry) -> ExecutionPipeline:
    dispatcher = ExecutionDispatcher(full_registry)
    return ExecutionPipeline(dispatcher)


class TestFullPipelineIntegration:
    def test_python_execution_succeeds(self, full_pipeline, minimal_request):
        result = full_pipeline.run(minimal_request)
        assert result.status == ExecutionStatus.SUCCESS

    def test_javascript_execution_succeeds(self, full_pipeline, js_env):
        request = ExecutionRequest(
            execution_id="exec-js-001",
            question_id="q-js",
            language_id="javascript",
            candidate_code="const x = 1;",
            environment=js_env,
        )
        result = full_pipeline.run(request)
        assert result.status == ExecutionStatus.SUCCESS

    def test_unknown_language_returns_internal_error(self, full_pipeline, ts_env):
        request = ExecutionRequest(
            execution_id="exec-ts-001",
            question_id="q-ts",
            language_id="typescript",
            candidate_code="const x: number = 1;",
            environment=ts_env,
        )
        result = full_pipeline.run(request)
        assert result.status == ExecutionStatus.INTERNAL_ERROR

    def test_never_raises_on_unregistered(self, full_pipeline, ts_env):
        request = ExecutionRequest(
            execution_id="exec-ts-001",
            question_id="q-ts",
            language_id="typescript",
            candidate_code="const x: number = 1;",
            environment=ts_env,
        )
        result = full_pipeline.run(request)
        assert isinstance(result, ExecutionResult)


class TestFactoryToRegistryToDispatcher:
    def test_factory_request_dispatched_correctly(self, full_registry, python_env):
        factory = ExecutionFactory()
        dispatcher = ExecutionDispatcher(full_registry)
        pipeline = ExecutionPipeline(dispatcher)

        request = factory.build_request(
            execution_id="exec-f-001",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 42",
            environment=python_env,
        )
        result = pipeline.run(request)
        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_id == "exec-f-001"

    def test_factory_generates_id_dispatched(self, full_registry, python_env):
        factory = ExecutionFactory()
        dispatcher = ExecutionDispatcher(full_registry)
        pipeline = ExecutionPipeline(dispatcher)

        request = factory.build_request(
            execution_id="",
            question_id="q-1",
            language_id="python",
            candidate_code="x = 42",
            environment=python_env,
        )
        result = pipeline.run(request)
        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_id  # non-empty generated id


class TestContextAndLifecycleIntegration:
    def test_context_from_request_matches_registry_language(self, minimal_request, full_registry):
        ctx = ExecutionContext.from_request(minimal_request)
        assert full_registry.is_supported(ctx.executor_language_id)

    def test_lifecycle_full_run(self, minimal_request):
        lifecycle = ExecutionLifecycle()
        lifecycle.start()
        lifecycle.transition(ExecutionPhase.DISPATCH)
        result = ExecutionResult(
            execution_id=minimal_request.execution_id,
            language_id=minimal_request.language_id,
            question_id=minimal_request.question_id,
            status=ExecutionStatus.SUCCESS,
        )
        lifecycle.complete(result)
        assert lifecycle.current_phase == ExecutionPhase.COMPLETE
        assert lifecycle.is_complete

    def test_lifecycle_fail_path(self, minimal_request):
        lifecycle = ExecutionLifecycle()
        lifecycle.start()
        lifecycle.fail("test failure")
        assert lifecycle.current_phase == ExecutionPhase.FAILED
        assert lifecycle.is_complete


class TestValidatorAndRegistryIntegration:
    def test_validated_request_routed_correctly(self, full_registry, minimal_request):
        validator = ExecutionValidator()
        errors = validator.validate(minimal_request)
        assert errors == []

        dispatcher = ExecutionDispatcher(full_registry)
        result = dispatcher.dispatch(minimal_request)
        assert result.status == ExecutionStatus.SUCCESS


class TestRoutingResultIntegration:
    def test_routing_result_success(self, full_registry):
        lang = "python"
        executor = full_registry.get_or_none(lang)
        available = executor.is_available() if executor else False
        routing = ExecutionRoutingResult(
            success=executor is not None and available,
            language_id=lang,
            executor_available=available,
        )
        assert routing.success is True
        assert routing.executor_available is True

    def test_routing_result_failure_for_unknown(self, full_registry):
        lang = "ruby"
        executor = full_registry.get_or_none(lang)
        routing = ExecutionRoutingResult(
            success=False,
            language_id=lang,
            executor_available=False,
            routing_errors=[f"No executor for {lang}"],
        )
        assert routing.success is False
        assert len(routing.routing_errors) == 1

    def test_end_to_end_multiple_languages(self, full_pipeline, python_env, js_env):
        factory = ExecutionFactory()
        py_req = factory.build_request(
            execution_id="py-001", question_id="q-1", language_id="python",
            candidate_code="x = 1", environment=python_env,
        )
        js_req = factory.build_request(
            execution_id="js-001", question_id="q-2", language_id="javascript",
            candidate_code="const x = 1;", environment=js_env,
        )
        py_result = full_pipeline.run(py_req)
        js_result = full_pipeline.run(js_req)
        assert py_result.status == ExecutionStatus.SUCCESS
        assert js_result.status == ExecutionStatus.SUCCESS
