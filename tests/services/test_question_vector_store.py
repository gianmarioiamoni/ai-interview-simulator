# tests/services/test_question_vector_store.py

from datetime import datetime, timezone
from unittest.mock import MagicMock

from langchain_core.documents import Document

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.question_intelligence.question_vector_store import QuestionVectorStore


def create_sample_item() -> QuestionBankItem:
    return QuestionBankItem(
        id="q1",
        text="Explain ACID properties.",
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        difficulty=3,
        ingestion_metadata=IngestionMetadata(
            source_name="test_dataset",
            source_type="manual",
            dataset_version="v1",
            ingestion_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )


def test_add_items_converts_to_documents():
    mock_store = MagicMock()
    adapter = QuestionVectorStore(mock_store)

    item = create_sample_item()

    adapter.add_items([item])

    assert mock_store.add_documents.called

    args, _ = mock_store.add_documents.call_args
    documents = args[0]

    assert isinstance(documents[0], Document)
    assert documents[0].page_content == "Explain ACID properties."

    metadata = documents[0].metadata

    assert metadata["id"] == "q1"
    assert metadata["interview_type"] == "technical"
    assert metadata["role"] == "backend_engineer"
    assert metadata["area"] == "technical_database"
    assert metadata["level"] == "mid"
    assert metadata["difficulty"] == 3
    assert metadata["source_name"] == "test_dataset"
    assert metadata["source_type"] == "manual"
    assert metadata["dataset_version"] == "v1"


def test_similarity_search_passes_parameters():
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = []

    adapter = QuestionVectorStore(mock_store)

    adapter.similarity_search(
        query="database consistency",
        k=5,
        metadata_filter={"role": "backend_engineer"},
    )

    mock_store.similarity_search.assert_called_with(
        query="database consistency",
        k=5,
        filter={"role": "backend_engineer"},
    )


def test_max_marginal_relevance_search_passes_parameters():
    mock_store = MagicMock()
    mock_store.max_marginal_relevance_search.return_value = []

    adapter = QuestionVectorStore(mock_store)

    adapter.max_marginal_relevance_search(
        query="indexes",
        k=3,
        fetch_k=12,
        metadata_filter={"area": "technical_database"},
    )

    mock_store.max_marginal_relevance_search.assert_called_with(
        query="indexes",
        k=3,
        fetch_k=12,
        filter={"area": "technical_database"},
    )
