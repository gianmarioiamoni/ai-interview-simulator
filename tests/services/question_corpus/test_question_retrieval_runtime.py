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
