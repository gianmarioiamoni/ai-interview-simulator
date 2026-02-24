# tests/domain/contracts/test_retrieval_document.py

import pytest
from pydantic import ValidationError

from domain.contracts.retrieval_document import RetrievalDocument
from domain.contracts.retrieval_metadata import RetrievalMetadata
from domain.contracts.role import Role
from domain.contracts.interview_area import InterviewArea


def test_retrieval_document_valid() -> None:
    doc = RetrievalDocument(
        id="doc-1",
        content="Python uses indentation.",
        metadata=RetrievalMetadata(
            role=Role.BACKEND_ENGINEER,
            area=InterviewArea.PYTHON,
            source="kb",
        ),
    )

    assert doc.id == "doc-1"
    assert doc.metadata.source == "kb"


def test_retrieval_document_empty_id_invalid() -> None:
    with pytest.raises(ValidationError):
        RetrievalDocument(
            id="",
            content="text",
            metadata=RetrievalMetadata(
                role=Role.BACKEND_ENGINEER,
                area=InterviewArea.PYTHON,
            ),
        )


def test_retrieval_document_empty_content_invalid() -> None:
    with pytest.raises(ValidationError):
        RetrievalDocument(
            id="doc-1",
            content="",
            metadata=RetrievalMetadata(
                role=Role.BACKEND_ENGINEER,
                area=InterviewArea.PYTHON,
            ),
        )


def test_retrieval_document_missing_metadata_invalid() -> None:
    with pytest.raises(ValidationError):
        RetrievalDocument(
            id="doc-1",
            content="text",
        )


def test_retrieval_document_is_frozen() -> None:
    doc = RetrievalDocument(
        id="doc-1",
        content="text",
        metadata=RetrievalMetadata(
            role=Role.BACKEND_ENGINEER,
            area=InterviewArea.PYTHON,
        ),
    )

    with pytest.raises(ValidationError):
        doc.content = "modified"
