# tests/services/question_corpus/test_adaptive_retrieval_service.py

from unittest.mock import MagicMock

from langchain_core.documents import Document

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.retrieval.adaptive_retrieval_policy import (
    AdaptiveRetrievalPolicy,
)
from services.question_corpus.retrieval.adaptive_retrieval_service import (
    AdaptiveRetrievalService,
)
from services.question_corpus.retrieval.coverage_penalty_engine import (
    CoveragePenaltyEngine,
)
from services.question_corpus.retrieval.question_repetition_filter import (
    QuestionRepetitionFilter,
)
from services.question_corpus.retrieval.weak_domain_boost_engine import (
    WeakDomainBoostEngine,
)


def _build_context(
    target_area: str = "technical_background",
    target_question_count: int = 1,
    asked_question_ids: list[str] | None = None,
) -> AdaptiveRetrievalContext:

    # Stage-progression tests use non-fresh memory so the background
    # fresh-start minimum-pool rule does not alter stage-success criteria.
    return AdaptiveRetrievalContext(
        current_role="fullstack_engineer",
        seniority="mid",
        target_area=target_area,
        target_question_count=target_question_count,
        memory=InterviewRetrievalMemory(
            asked_question_ids=(
                asked_question_ids
                if asked_question_ids is not None
                else ["prior-question"]
            ),
        ),
    )


def _build_candidate(
    document_id: str,
    area: str,
) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content="Sample question text.",
            metadata={
                "document_id": document_id,
                "area": area,
            },
        ),
        semantic_score=0.8,
        quality_score=0.9,
        final_score=0.85,
        adaptive_score=0.85,
    )


def _build_service(
    mock_retrieval: MagicMock,
) -> AdaptiveRetrievalService:

    coverage_engine = CoveragePenaltyEngine()
    weak_domain_engine = WeakDomainBoostEngine()
    repetition_filter = QuestionRepetitionFilter()

    return AdaptiveRetrievalService(
        retrieval=mock_retrieval,
        policy=AdaptiveRetrievalPolicy(),
        coverage_engine=coverage_engine,
        weak_domain_engine=weak_domain_engine,
        repetition_filter=repetition_filter,
    )


def _stage_filters(context: AdaptiveRetrievalContext) -> list[RetrievalFilters]:

    return AdaptiveRetrievalPolicy().build_relaxation_stages(
        context,
    )


def test_strict_retrieval_success_stage_1() -> None:

    context = _build_context()
    stages = _stage_filters(context)
    candidate = _build_candidate("bg-1", context.target_area)

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [candidate],
        [],
        [],
        [],
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="background experience",
        context=context,
    )

    assert len(results) == 1
    assert results[0].document.metadata["area"] == context.target_area
    assert mock_retrieval.search_with_filters.call_count == 1
    assert mock_retrieval.search_with_filters.call_args_list[0].kwargs["filters"] == stages[0]
    mock_retrieval.search.assert_not_called()


def test_stage_2_retrieval_success() -> None:

    context = _build_context()
    stages = _stage_filters(context)
    candidate = _build_candidate("bg-2", context.target_area)

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [],
        [candidate],
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="background experience",
        context=context,
    )

    assert len(results) == 1
    assert results[0].document.metadata["area"] == context.target_area
    assert mock_retrieval.search_with_filters.call_count == 2
    assert mock_retrieval.search_with_filters.call_args_list[1].kwargs["filters"] == stages[1]
    mock_retrieval.search.assert_not_called()


def test_stage_3_retrieval_success() -> None:

    context = _build_context()
    stages = _stage_filters(context)
    candidate = _build_candidate("bg-3", context.target_area)

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [],
        [],
        [candidate],
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="background experience",
        context=context,
    )

    assert len(results) == 1
    assert mock_retrieval.search_with_filters.call_count == 3
    assert mock_retrieval.search_with_filters.call_args_list[2].kwargs["filters"] == stages[2]
    mock_retrieval.search.assert_not_called()


def test_stage_4_retrieval_success() -> None:

    context = _build_context()
    stages = _stage_filters(context)
    candidate = _build_candidate("bg-4", context.target_area)

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [],
        [],
        [],
        [candidate],
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="background experience",
        context=context,
    )

    assert len(results) == 1
    assert mock_retrieval.search_with_filters.call_count == 4
    assert mock_retrieval.search_with_filters.call_args_list[3].kwargs["filters"] == stages[3]
    assert stages[3].area == context.target_area
    assert stages[3].role is None
    assert stages[3].seniority == context.seniority
    assert stages[3].min_difficulty is None
    assert stages[3].max_difficulty is None
    mock_retrieval.search.assert_not_called()


def test_all_stages_empty_returns_empty_list() -> None:

    context = _build_context()

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [],
        [],
        [],
        [],
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="background experience",
        context=context,
    )

    assert results == []
    assert mock_retrieval.search_with_filters.call_count == 4
    mock_retrieval.search.assert_not_called()


def test_background_fresh_start_micro_pool_advances_stage() -> None:

    context = _build_context(asked_question_ids=[])
    candidates_big = [
        _build_candidate(f"bg-rich-{index}", context.target_area)
        for index in range(6)
    ]

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [_build_candidate("bg-micro", context.target_area)],
        candidates_big,
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="background experience",
        context=context,
    )

    assert len(results) >= 1
    assert mock_retrieval.search_with_filters.call_count == 2
    returned_ids = {
        item.document.metadata["document_id"] for item in results
    }
    assert "bg-micro" not in returned_ids


def test_background_fresh_start_falls_back_to_largest_micro_pool() -> None:

    context = _build_context(asked_question_ids=[])

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [_build_candidate("bg-a", context.target_area)],
        [
            _build_candidate("bg-b", context.target_area),
            _build_candidate("bg-c", context.target_area),
        ],
        [],
        [],
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="background experience",
        context=context,
    )

    assert len(results) == 1
    assert mock_retrieval.search_with_filters.call_count == 4
    assert results[0].document.metadata["document_id"] in {"bg-b", "bg-c"}


def test_non_background_area_keeps_non_empty_stage_success() -> None:

    context = _build_context(
        target_area="technical_case_study",
        asked_question_ids=[],
    )

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.side_effect = [
        [_build_candidate("cs-1", context.target_area)],
    ]

    service = _build_service(mock_retrieval)

    results = service.retrieve(
        query="case study",
        context=context,
    )

    assert len(results) == 1
    assert mock_retrieval.search_with_filters.call_count == 1


def test_build_relaxation_stages_preserves_area_across_stages() -> None:

    context = _build_context(
        target_area="technical_technical_knowledge",
    )

    stages = _stage_filters(context)

    assert len(stages) == 4

    for stage in stages:
        assert stage.area == "technical_technical_knowledge"
