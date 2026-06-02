# tests/services/question_intelligence/test_retrieval_strategy_context_adapter.py

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.adapters.retrieval_strategy_context_adapter import (
    RetrievalStrategyContextAdapter,
)
from services.question_intelligence.retrieval.retrieval_strategy import RetrievalStrategy


def test_adapt_maps_strategy_and_filters_to_adaptive_context() -> None:
    memory = InterviewRetrievalMemory(
        covered_domains=["backend"],
        weak_domains=["distributed_systems"],
        average_score=0.9,
        question_count=2,
    )

    adapter = RetrievalStrategyContextAdapter()

    context = adapter.adapt(
        query="cache invalidation",
        retrieval_strategy=RetrievalStrategy(k=7, fetch_k=28, use_mmr=False),
        role="backend_engineer",
        level="senior",
        area="technical_case_study",
        memory=memory,
    )

    assert context.current_role == "backend_engineer"
    assert context.seniority == "senior"
    assert context.target_area == "technical_case_study"
    assert context.target_question_count == 7
    assert context.already_used_domains == ["backend"]
    assert context.weak_domains == ["distributed_systems"]
    assert context.target_difficulty == 5
    assert context.memory == memory


def test_adapt_resolves_target_area_from_role_when_area_missing() -> None:
    adapter = RetrievalStrategyContextAdapter()

    context = adapter.adapt(
        query="sql tuning",
        retrieval_strategy=RetrievalStrategy(k=3, fetch_k=12),
        role="data_engineer",
        level="mid",
    )

    assert context.target_area == "technical_database"