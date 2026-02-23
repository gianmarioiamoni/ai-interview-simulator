# Tests for QuestionRetrievalService

from unittest.mock import MagicMock

from langchain_core.documents import Document

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)


def create_mock_document():
    return Document(
        page_content="Explain ACID properties.",
        metadata={
            "id": "q1",
            "interview_type": "technical",
            "role": "backend",
            "area": "databases",
            "level": "mid",
            "difficulty": 3,
        },
    )


def test_retrieve_builds_filter_and_returns_domain_objects():
    mock_vector_store = MagicMock()
    mock_vector_store.similarity_search.return_value = [create_mock_document()]

    service = QuestionRetrievalService(mock_vector_store)

    results = service.retrieve(
        query="database consistency",
        k=5,
        role="backend",
        level="mid",
        interview_type="technical",
        area="databases",
    )

    mock_vector_store.similarity_search.assert_called_once()

    assert len(results) == 1
    assert results[0].id == "q1"
    assert results[0].role == "backend"
    assert results[0].area == "databases"


def test_retrieve_without_filters_passes_none():
    mock_vector_store = MagicMock()
    mock_vector_store.similarity_search.return_value = []

    service = QuestionRetrievalService(mock_vector_store)

    service.retrieve(query="test", k=3)

    _, kwargs = mock_vector_store.similarity_search.call_args

    assert kwargs["metadata_filter"] is None
