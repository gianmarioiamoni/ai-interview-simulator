# Tests for EmbeddingService

from unittest.mock import MagicMock, patch

from services.question_intelligence.embedding_service import EmbeddingService


def test_embed_texts_delegates_to_model():
    mock_model = MagicMock()
    mock_model.embed_documents.return_value = [[0.1, 0.2]]

    with patch(
        "services.question_intelligence.embedding_service.get_embedding_model",
        return_value=mock_model,
    ):
        service = EmbeddingService()
        result = service.embed_texts(["test text"])

        assert result == [[0.1, 0.2]]
        mock_model.embed_documents.assert_called_with(["test text"])


def test_embed_query_delegates_to_model():
    mock_model = MagicMock()
    mock_model.embed_query.return_value = [0.5, 0.6]

    with patch(
        "services.question_intelligence.embedding_service.get_embedding_model",
        return_value=mock_model,
    ):
        service = EmbeddingService()
        result = service.embed_query("query")

        assert result == [0.5, 0.6]
        mock_model.embed_query.assert_called_with("query")
