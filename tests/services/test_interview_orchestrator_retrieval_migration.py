# tests/services/test_interview_orchestrator_retrieval_migration.py

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


def _build_question(item_id: str = "q1") -> QuestionBankItem:
    return QuestionBankItem(
        id=item_id,
        text="Design a resilient queue.",
        interview_type="technical",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_CASE_STUDY,
        level=SeniorityLevel.SENIOR,
        difficulty=4,
        ingestion_metadata=IngestionMetadata(
            source_name="seed",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp=datetime.now(timezone.utc),
        ),
    )


def _import_orchestrator_module_with_stubs():
    # The orchestrator imports RecoveryReplanner at module import time.
    # RecoveryReplanner pulls retrieval/planning modules that may import heavy ML deps.
    # Stub only that import boundary so this test validates migration wiring only.
    stub_replanner_module = types.ModuleType("services.replanning.recovery_replanner")

    class StubRecoveryReplanner:
        def replan(self, items, constraints, role, level):
            return SimpleNamespace(
                final_planning_result=SimpleNamespace(selected_questions=[]),
                final_validation_result=SimpleNamespace(),
            )

    stub_replanner_module.RecoveryReplanner = StubRecoveryReplanner

    previous_replanner = sys.modules.get("services.replanning.recovery_replanner")
    sys.modules["services.replanning.recovery_replanner"] = stub_replanner_module

    try:
        module = importlib.import_module(
            "services.interview_orchestration.interview_orchestrator"
        )
    finally:
        if previous_replanner is None:
            del sys.modules["services.replanning.recovery_replanner"]
        else:
            sys.modules["services.replanning.recovery_replanner"] = previous_replanner

    return module


def test_orchestrator_uses_runtime_adapter_and_candidate_mapper(monkeypatch) -> None:
    module = _import_orchestrator_module_with_stubs()

    adapter = MagicMock()
    runtime = MagicMock()
    mapper = MagicMock()
    context = object()
    mapped_questions = [_build_question()]
    adapter.adapt.return_value = context
    runtime.retrieve_questions.return_value = [object()]
    mapper.map.return_value = mapped_questions

    monkeypatch.setattr(module, "RetrievalSessionMemory", lambda: object())
    monkeypatch.setattr(module, "MemoryAwareRetrievalPipeline", lambda memory: MagicMock())
    monkeypatch.setattr(module, "PlannerRetrievalService", lambda: MagicMock())
    monkeypatch.setattr(module, "RetrievalRuntimeMapper", lambda: MagicMock())
    monkeypatch.setattr(module, "OrchestrationIntentAdapter", lambda: adapter)
    monkeypatch.setattr(module, "QuestionRetrievalRuntime", lambda: runtime)
    monkeypatch.setattr(module, "RetrievalCandidateMapper", lambda: mapper)

    intent = SimpleNamespace(
        query_text="distributed systems senior",
        max_candidates=15,
        target_level="senior",
        focus_areas=["distributed_systems"],
        required_tags=["distributed_systems"],
    )
    intent_builder = MagicMock()
    intent_builder.build.return_value = intent
    monkeypatch.setattr(module, "OrchestrationIntentBuilder", lambda: intent_builder)

    pool = SimpleNamespace(
        eligible_questions=mapped_questions,
        rejected_questions=[],
        total_candidates=1,
        eligible_count=1,
        rejected_count=0,
    )
    pool_builder = MagicMock()
    pool_builder.build.return_value = pool
    monkeypatch.setattr(module, "CandidatePoolBuilder", lambda: pool_builder)

    policy = SimpleNamespace(
        preferred_areas=[InterviewArea.TECH_CASE_STUDY],
        max_questions_per_area=2,
        target_average_difficulty=3.0,
    )
    policy_factory = MagicMock()
    policy_factory.build.return_value = policy
    monkeypatch.setattr(module, "PolicyFactory", lambda: policy_factory)

    replanning_result = SimpleNamespace(
        final_planning_result=SimpleNamespace(selected_questions=[]),
        final_validation_result=SimpleNamespace(),
    )
    replanner = MagicMock()
    replanner.replan.return_value = replanning_result
    monkeypatch.setattr(module, "RecoveryReplanner", lambda: replanner)

    assembly_result = SimpleNamespace(questions=[])
    assembler = MagicMock()
    assembler.assemble.return_value = assembly_result
    monkeypatch.setattr(module, "AdaptiveInterviewAssembler", lambda: assembler)

    monkeypatch.setattr(module, "OrchestrationResult", lambda **kwargs: kwargs)

    orchestrator = module.InterviewOrchestrator()

    result = orchestrator.orchestrate(
        items=[],
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
        max_questions=5,
    )

    adapter.adapt.assert_called_once()
    runtime.retrieve_questions.assert_called_once_with(
        query=intent.query_text,
        context=context,
    )
    mapper.map.assert_called_once()

    _, kwargs = pool_builder.build.call_args
    assert isinstance(kwargs["items"], list)
    assert all(isinstance(item, QuestionBankItem) for item in kwargs["items"])

    assert "candidate_pool" in result
    assert "planning_result" in result
    assert "validation_result" in result
    assert "replanning_result" in result
    assert "assembly_result" in result
