# Tests for QuestionIndexer

from unittest.mock import MagicMock

from services.question_intelligence.question_indexer import (
    QuestionIndexer,
)


def test_sync_returns_zero_when_no_items():
    mock_repo = MagicMock()
    mock_repo.list_all.return_value = []

    mock_vector_store = MagicMock()

    indexer = QuestionIndexer(mock_repo, mock_vector_store)

    result = indexer.sync()

    assert result == 0
    mock_vector_store.add_items.assert_not_called()


def test_sync_indexes_all_items():
    mock_repo = MagicMock()
    mock_repo.list_all.return_value = ["item1", "item2"]

    mock_vector_store = MagicMock()

    indexer = QuestionIndexer(mock_repo, mock_vector_store)

    result = indexer.sync()

    assert result == 2
    mock_vector_store.add_items.assert_called_once_with(["item1", "item2"])
