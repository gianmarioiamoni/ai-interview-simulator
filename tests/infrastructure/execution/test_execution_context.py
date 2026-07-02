# tests/infrastructure/execution/test_execution_context.py

import uuid
import pytest

from infrastructure.execution.execution_context import ExecutionContext
from infrastructure.execution.contracts.execution_request import ExecutionRequest


class TestExecutionContextCreation:
    def test_from_request_creates_context(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert isinstance(ctx, ExecutionContext)

    def test_from_request_sets_request(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert ctx.request == minimal_request

    def test_from_request_sets_executor_language_id(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert ctx.executor_language_id == minimal_request.language_id

    def test_from_request_generates_dispatch_id(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert ctx.dispatch_id
        uuid.UUID(ctx.dispatch_id)  # must be valid uuid

    def test_from_request_unique_dispatch_ids(self, minimal_request):
        ctx1 = ExecutionContext.from_request(minimal_request)
        ctx2 = ExecutionContext.from_request(minimal_request)
        assert ctx1.dispatch_id != ctx2.dispatch_id

    def test_from_request_routing_metadata_has_language_id(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert ctx.routing_metadata["language_id"] == minimal_request.language_id

    def test_from_request_routing_metadata_has_execution_id(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert ctx.routing_metadata["execution_id"] == minimal_request.execution_id

    def test_from_request_routing_metadata_has_question_id(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert ctx.routing_metadata["question_id"] == minimal_request.question_id


class TestExecutionContextImmutability:
    def test_context_is_frozen(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        with pytest.raises(Exception):
            ctx.executor_language_id = "javascript"  # type: ignore

    def test_context_is_pydantic_model(self, minimal_request):
        from pydantic import BaseModel
        ctx = ExecutionContext.from_request(minimal_request)
        assert isinstance(ctx, BaseModel)


class TestExecutionContextDirectConstruction:
    def test_direct_construction(self, minimal_request):
        ctx = ExecutionContext(
            request=minimal_request,
            executor_language_id="python",
            dispatch_id="fixed-id",
            routing_metadata={"foo": "bar"},
        )
        assert ctx.executor_language_id == "python"
        assert ctx.dispatch_id == "fixed-id"
        assert ctx.routing_metadata == {"foo": "bar"}

    def test_routing_metadata_defaults_to_empty(self, minimal_request):
        ctx = ExecutionContext(
            request=minimal_request,
            executor_language_id="python",
            dispatch_id="id-1",
        )
        assert ctx.routing_metadata == {}

    def test_extra_fields_forbidden(self, minimal_request):
        with pytest.raises(Exception):
            ExecutionContext(
                request=minimal_request,
                executor_language_id="python",
                dispatch_id="id-1",
                unknown_field="x",
            )


class TestExecutionContextMetadata:
    def test_routing_metadata_is_dict_of_strings(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in ctx.routing_metadata.items())

    def test_executor_language_id_matches_request(self, minimal_request):
        ctx = ExecutionContext.from_request(minimal_request)
        assert ctx.executor_language_id == ctx.request.language_id
