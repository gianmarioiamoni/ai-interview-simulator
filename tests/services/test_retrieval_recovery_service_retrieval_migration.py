# tests/services/test_retrieval_recovery_service_retrieval_migration.py

from datetime import datetime, timezone
import importlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


def _build_question(item_id: str) -> QuestionBankItem:
    return QuestionBankItem(
        id=item_id,
        text="Explain idempotency.",
        interview_type="technical",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        level=SeniorityLevel.MID,
        difficulty=3,
        ingestion_metadata=IngestionMetadata(
            source_name="seed",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp=datetime.now(timezone.utc),
        ),
    )


def _import_recovery_service_module_with_stubs():
    # Keep this test isolated from transitive retrieval/planning imports.
    # We only validate migration wiring in RetrievalRecoveryService.
    stub_runtime_module = types.ModuleType(
        "services.question_corpus.question_retrieval_runtime"
    )

    class StubQuestionRetrievalRuntime:
        def retrieve_questions(self, query, context):
            return []

    stub_runtime_module.QuestionRetrievalRuntime = StubQuestionRetrievalRuntime

    previous_runtime = sys.modules.get("services.question_corpus.question_retrieval_runtime")
    sys.modules["services.question_corpus.question_retrieval_runtime"] = stub_runtime_module

    try:
        module = importlib.import_module("services.replanning.retrieval_recovery_service")
    finally:
        if previous_runtime is None:
            del sys.modules["services.question_corpus.question_retrieval_runtime"]
        else:
            sys.modules["services.question_corpus.question_retrieval_runtime"] = (
                previous_runtime
            )

    return module


def test_retrieval_recovery_service_uses_runtime_adapter_and_mapper(monkeypatch) -> None:
    module = _import_recovery_service_module_with_stubs()

    role_strategy = MagicMock()
    role_strategy.expand.return_value = [RoleType.BACKEND_ENGINEER]
    monkeypatch.setattr(module, "RoleExpansionStrategy", lambda: role_strategy)

    intent = SimpleNamespace(
        query_text="backend systems mid",
        max_candidates=10,
        target_level="mid",
        focus_areas=["backend"],
        required_tags=[],
    )
    intent_builder = MagicMock()
    intent_builder.build.return_value = intent
    monkeypatch.setattr(module, "OrchestrationIntentBuilder", lambda: intent_builder)

    adapter = MagicMock()
    context = object()
    adapter.adapt.return_value = context
    monkeypatch.setattr(module, "OrchestrationIntentAdapter", lambda: adapter)

    runtime = MagicMock()
    runtime.retrieve_questions.return_value = [object()]
    monkeypatch.setattr(module, "QuestionRetrievalRuntime", lambda: runtime)

    mapped_questions = [_build_question("new_1")]
    candidate_mapper = MagicMock()
    candidate_mapper.map.return_value = mapped_questions
    monkeypatch.setattr(module, "RetrievalCandidateMapper", lambda: candidate_mapper)

    monkeypatch.setattr(module, "RetrievalExpansionTelemetry", lambda **kwargs: kwargs)
    monkeypatch.setattr(module, "RecoveryExpansionResult", lambda **kwargs: kwargs)

    service = module.RetrievalRecoveryService()

    original = [_build_question("orig_1")]

    result = service.expand_role_scope(
        items=original,
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
    )

    adapter.adapt.assert_called_once()
    runtime.retrieve_questions.assert_called_once_with(
        query=intent.query_text,
        context=context,
    )
    candidate_mapper.map.assert_called_once()

    _, kwargs = candidate_mapper.map.call_args
    assert isinstance(kwargs["candidates"], list)

    expanded = result["expanded_items"]
    assert isinstance(expanded, list)
    assert all(isinstance(item, QuestionBankItem) for item in expanded)
    assert result["applied_action"] == module.RecoveryAction.EXPAND_ROLE_SCOPE
    assert "telemetry" in result
