# tests/domain/contracts/test_retrieval_document.py

import pytest
from pydantic import ValidationError

from domain.contracts.retrieval_document import RetrievalDocument


def test_retrieval_document_valid() -> None:
    doc = RetrievalDocument(
        id="doc-1",
        content="Python uses indentation.",
        metadata={"source": "kb"},
    )

    assert doc.id == "doc-1"
    assert doc.metadata["source"] == "kb"


def test_retrieval_document_empty_id_invalid() -> None:
    with pytest.raises(ValidationError):
        RetrievalDocument(
            id="",
            content="text",
        )


def test_retrieval_document_empty_content_invalid() -> None:
    with pytest.raises(ValidationError):
        RetrievalDocument(
            id="doc-1",
            content="",
        )


def test_retrieval_document_is_frozen() -> None:
    doc = RetrievalDocument(
        id="doc-1",
        content="text",
    )

    with pytest.raises(ValidationError):
        doc.content = "modified"
