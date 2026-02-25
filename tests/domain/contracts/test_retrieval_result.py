# tests/domain/contracts/test_retrieval_result.py

import pytest
from pydantic import ValidationError

from domain.contracts.retrieval_result import RetrievalResult
from domain.contracts.retrieval_document import RetrievalDocument
from domain.contracts.retrieval_metadata import RetrievalMetadata
from domain.contracts.role import Role, RoleType
from domain.contracts.interview_area import InterviewArea


def test_retrieval_result_empty_valid() -> None:
    result = RetrievalResult()
    assert result.documents == []


def test_retrieval_result_with_documents() -> None:
    doc = RetrievalDocument(
        id="doc-1",
        content="Some content",
        metadata=RetrievalMetadata(
            role=Role(type=RoleType.BACKEND_ENGINEER),
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        ),
    )

    result = RetrievalResult(documents=[doc])

    assert len(result.documents) == 1
    assert result.documents[0].id == "doc-1"


def test_retrieval_result_is_frozen() -> None:
    result = RetrievalResult()

    with pytest.raises(ValidationError):
        result.documents = []
