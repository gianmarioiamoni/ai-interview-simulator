# tests/services/question_corpus/test_orchestration_intent_adapter.py

from unittest.mock import MagicMock

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.interview_orchestration.orchestration_intent_builder import (
    OrchestrationIntentBuilder,
)
from services.question_corpus.adapters.orchestration_intent_adapter import (
    OrchestrationIntentAdapter,
)
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.adaptive_context_builder import (
    AdaptiveContextBuilder,
)


def _build_intent():
    builder = OrchestrationIntentBuilder()
    return builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
    )


def test_adapt_happy_path_reuses_builder_and_maps_fields() -> None:
    intent = _build_intent()
    memory = InterviewRetrievalMemory(
        covered_domains=["backend"],
        weak_domains=["distributed_systems"],
        average_score=0.9,
        question_count=2,
    )

    adapter = OrchestrationIntentAdapter()

    context = adapter.adapt(
        intent=intent,
        role=RoleType.BACKEND_ENGINEER,
        target_area="technical_case_study",
        memory=memory,
    )

    assert context.current_role == "backend_engineer"
    assert context.seniority == "senior"
    assert context.target_area == "technical_case_study"
    assert context.target_question_count == intent.max_candidates
    assert context.already_used_domains == ["backend"]
    assert context.weak_domains == ["distributed_systems"]
    assert context.target_difficulty == 5
    assert context.memory == memory


def test_adapt_defaults_memory_when_not_provided() -> None:
    intent = _build_intent()
    adapter = OrchestrationIntentAdapter()

    context = adapter.adapt(
        intent=intent,
        role=RoleType.BACKEND_ENGINEER,
        target_area="technical_case_study",
    )

    assert isinstance(context.memory, InterviewRetrievalMemory)
    assert context.memory.question_count == 0


def test_adapt_delegates_to_injected_context_builder() -> None:
    intent = _build_intent()
    expected_context = AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="senior",
        target_area="technical_case_study",
        target_question_count=10,
        memory=InterviewRetrievalMemory(),
    )

    mock_builder = MagicMock(spec=AdaptiveContextBuilder)
    mock_builder.build.return_value = expected_context

    adapter = OrchestrationIntentAdapter(
        context_builder=mock_builder,
    )

    context = adapter.adapt(
        intent=intent,
        role=RoleType.BACKEND_ENGINEER,
        target_area="technical_case_study",
    )

    mock_builder.build.assert_called_once()
    assert context == expected_context
