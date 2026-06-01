# tests/services/question_corpus/test_question_retrieval_runtime.py

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
from services.question_corpus.question_retrieval_runtime import QuestionRetrievalRuntime


def _build_context() -> AdaptiveRetrievalContext:

    return AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="senior",
        target_area="technical_case_study",
        target_question_count=3,
        memory=InterviewRetrievalMemory(),
    )


def _build_candidate(document_id: str) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content="Explain eventual consistency.",
            metadata={"document_id": document_id},
        ),
        semantic_score=0.8,
        quality_score=0.9,
        final_score=0.85,
        adaptive_score=0.85,
    )


def test_retrieve_questions_delegates_to_adaptive_retrieval_service() -> None:

    mock_adaptive_service = MagicMock()
    expected = [_build_candidate("q-1")]
    mock_adaptive_service.retrieve.return_value = expected

    runtime = QuestionRetrievalRuntime(
        adaptive_retrieval_service=mock_adaptive_service,
        chroma_retrieval_service=MagicMock(),
    )

    context = _build_context()
    query = "distributed systems scalability"

    results = runtime.retrieve_questions(
        query=query,
        context=context,
    )

    mock_adaptive_service.retrieve.assert_called_once_with(
        query=query,
        context=context,
    )

    assert results == expected


def test_search_delegates_to_chroma_retrieval_service() -> None:

    mock_chroma_service = MagicMock()
    expected = [_build_candidate("q-2")]
    mock_chroma_service.search.return_value = expected

    runtime = QuestionRetrievalRuntime(
        chroma_retrieval_service=mock_chroma_service,
        adaptive_retrieval_service=MagicMock(),
    )

    query = "distributed cache invalidation"

    results = runtime.search(
        query=query,
        k=3,
    )

    mock_chroma_service.search.assert_called_once_with(
        query=query,
        k=3,
    )

    assert results == expected


def test_search_with_filters_delegates_to_chroma_retrieval_service() -> None:

    mock_chroma_service = MagicMock()
    expected = [_build_candidate("q-3")]
    mock_chroma_service.search_with_filters.return_value = expected

    runtime = QuestionRetrievalRuntime(
        chroma_retrieval_service=mock_chroma_service,
        adaptive_retrieval_service=MagicMock(),
    )

    query = "distributed systems scalability"
    filters = RetrievalFilters(
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
    )

    results = runtime.search_with_filters(
        query=query,
        filters=filters,
        k=5,
    )

    mock_chroma_service.search_with_filters.assert_called_once_with(
        query=query,
        filters=filters,
        k=5,
    )

    assert results == expected


def test_retrieve_questions_from_memory_builds_context_and_delegates() -> None:

    mock_adaptive_service = MagicMock()
    mock_context_builder = MagicMock()
    expected = [_build_candidate("q-4")]
    memory = InterviewRetrievalMemory()
    context = _build_context()

    mock_context_builder.build.return_value = context
    mock_adaptive_service.retrieve.return_value = expected

    runtime = QuestionRetrievalRuntime(
        adaptive_retrieval_service=mock_adaptive_service,
        context_builder=mock_context_builder,
        chroma_retrieval_service=MagicMock(),
    )

    query = "distributed systems scalability"

    results = runtime.retrieve_questions_from_memory(
        query=query,
        memory=memory,
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
        question_count=3,
    )

    mock_context_builder.build.assert_called_once_with(
        memory=memory,
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
        question_count=3,
    )

    mock_adaptive_service.retrieve.assert_called_once_with(
        query=query,
        context=context,
    )

    assert results == expected
