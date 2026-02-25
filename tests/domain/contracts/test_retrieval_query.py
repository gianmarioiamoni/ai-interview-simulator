# tests/domain/contracts/test_retrieval_query.py

import pytest
from pydantic import ValidationError

from domain.contracts.retrieval_query import RetrievalQuery
from domain.contracts.role import Role
from domain.contracts.role import RoleType
from domain.contracts.interview_area import InterviewArea


def test_retrieval_query_valid_defaults() -> None:
    query = RetrievalQuery(
        query="Explain REST",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Generic IT",
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    )

    assert query.top_k == 5


def test_retrieval_query_invalid_empty_query() -> None:
    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            company="Generic IT",
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        )


def test_retrieval_query_invalid_top_k_low() -> None:
    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="Explain REST",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            company="Generic IT",
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            top_k=0,
        )


def test_retrieval_query_invalid_top_k_high() -> None:
    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="Explain REST",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            company="Generic IT",
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            top_k=25,
        )


def test_retrieval_query_is_frozen() -> None:
    query = RetrievalQuery(
        query="Explain REST",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Generic IT",
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    )

    with pytest.raises(ValidationError):
        query.top_k = 10
