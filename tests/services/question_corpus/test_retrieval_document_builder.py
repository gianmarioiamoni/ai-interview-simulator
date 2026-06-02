# tests/services/question_corpus/test_retrieval_document_builder.py

from unittest.mock import MagicMock, patch

from domain.contracts.corpus.curated_question import CuratedQuestion
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.builders.retrieval_document_builder import RetrievalDocumentBuilder
from services.question_corpus.repositories.retrieval_embedding_repository import (
    RetrievalEmbeddingRepository,
)


def _build_question() -> CuratedQuestion:

    return CuratedQuestion(
        id="test_doc_id_001",
        question="How would you design a rate limiter?",
        role=RoleType.BACKEND_ENGINEER,
        seniority=SeniorityLevel.SENIOR,
        area=InterviewArea.TECH_CASE_STUDY,
        domains=["technical_case_study"],
        difficulty=4,
        source="test_seed",
        quality_score=0.8,
        tags=["design"],
        expected_topics=["rate limiting"],
    )


@patch(
    "services.question_corpus.builders.retrieval_document_builder.get_embedding_model",
)
def test_build_with_embedding_calls_embed_and_stores(
    mock_get_embedding_model: MagicMock,
) -> None:

    mock_embedding_model = MagicMock()
    mock_embedding_model.embed_query.return_value = [0.1, 0.2, 0.3]
    mock_get_embedding_model.return_value = mock_embedding_model

    RetrievalEmbeddingRepository._embeddings.clear()

    builder = RetrievalDocumentBuilder(
        skip_embedding=False,
    )

    document = builder.build(
        _build_question(),
    )

    mock_embedding_model.embed_query.assert_called_once()

    assert document.embedding == [0.1, 0.2, 0.3]

    assert (
        RetrievalEmbeddingRepository.get(
            document_id="test_doc_id_001",
        )
        == [0.1, 0.2, 0.3]
    )

    assert document.metadata["area"] == "technical_case_study"
    assert document.metadata["role"] == "backend_engineer"
    assert document.metadata["seniority"] == "senior"
    assert document.metadata["difficulty"] == 4
    assert document.metadata["source"] == "test_seed"
    assert document.document_id == "test_doc_id_001"


@patch(
    "services.question_corpus.builders.retrieval_document_builder.get_embedding_model",
)
def test_build_skip_embedding_does_not_call_embed(
    mock_get_embedding_model: MagicMock,
) -> None:

    RetrievalEmbeddingRepository._embeddings.clear()

    builder = RetrievalDocumentBuilder(
        skip_embedding=True,
    )

    document = builder.build(
        _build_question(),
    )

    mock_get_embedding_model.assert_not_called()

    assert document.embedding == []

    assert (
        RetrievalEmbeddingRepository.get(
            document_id="test_doc_id_001",
        )
        is None
    )

    assert document.metadata["area"] == "technical_case_study"
    assert document.document_id == "test_doc_id_001"
