# tests/infrastructure/test_chroma_question_store.py

# Tests for ChromaQuestionStore

from unittest.mock import MagicMock, patch

from infrastructure.vector_store.chroma_question_store import (
    ChromaQuestionStore,
)


def test_store_initializes_with_correct_parameters():
    mock_embedding = MagicMock()

    with (
        patch(
            "infrastructure.vector_store.chroma_question_store.get_embedding_model",
            return_value=mock_embedding,
        ),
        patch(
            "infrastructure.vector_store.chroma_question_store.Chroma"
        ) as mock_chroma,
    ):

        store = ChromaQuestionStore()

        mock_chroma.assert_called_once()

        _, kwargs = mock_chroma.call_args

        assert kwargs["collection_name"] == "question_bank"
        assert kwargs["embedding_function"] == mock_embedding


def test_add_documents_delegates_to_chroma():
    mock_store_instance = MagicMock()

    with (
        patch(
            "infrastructure.vector_store.chroma_question_store.get_embedding_model",
            return_value=MagicMock(),
        ),
        patch(
            "infrastructure.vector_store.chroma_question_store.Chroma",
            return_value=mock_store_instance,
        ),
    ):
        store = ChromaQuestionStore()

        store.add_documents([])

        mock_store_instance.add_documents.assert_called_once()


def test_similarity_search_delegates():
    mock_store_instance = MagicMock()
    mock_store_instance.similarity_search.return_value = []

    with (
        patch(
            "infrastructure.vector_store.chroma_question_store.get_embedding_model",
            return_value=MagicMock(),
        ),
        patch(
            "infrastructure.vector_store.chroma_question_store.Chroma",
            return_value=mock_store_instance,
        ),
    ):
        store = ChromaQuestionStore()

        store.similarity_search("query", 5, {"role": "backend"})

        mock_store_instance.similarity_search.assert_called_with(
            query="query",
            k=5,
            filter={"role": "backend"},
        )
