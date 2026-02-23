# Tests for QuestionVectorStore adapter

from unittest.mock import MagicMock

from langchain_core.documents import Document

from domain.contracts.question_bank_item import QuestionBankItem
from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)


def create_sample_item() -> QuestionBankItem:
    return QuestionBankItem(
        id="q1",
        text="Explain ACID properties.",
        interview_type="technical",
        role="backend",
        area="databases",
        level="mid",
        difficulty=3,
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
    assert documents[0].metadata["role"] == "backend"


def test_similarity_search_passes_parameters():
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = []

    adapter = QuestionVectorStore(mock_store)

    adapter.similarity_search(
        query="database consistency",
        k=5,
        metadata_filter={"role": "backend"},
    )

    mock_store.similarity_search.assert_called_with(
        query="database consistency",
        k=5,
        filter={"role": "backend"},
    )
