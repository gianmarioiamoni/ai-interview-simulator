# tests/domain/contracts/test_retrieval_query.py

import pytest
from pydantic import ValidationError

from domain.contracts.retrieval_query import RetrievalQuery


def test_retrieval_query_valid_defaults() -> None:
    query = RetrievalQuery(
        query="Explain REST",
        role="backend engineer",
        company="Generic IT",
        area="architecture",
    )

    assert query.top_k == 5


def test_retrieval_query_invalid_empty_query() -> None:
    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="",
            role="backend",
            company="Generic IT",
            area="architecture",
        )


def test_retrieval_query_invalid_top_k_low() -> None:
    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="Explain REST",
            role="backend",
            company="Generic IT",
            area="architecture",
            top_k=0,
        )


def test_retrieval_query_invalid_top_k_high() -> None:
    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="Explain REST",
            role="backend",
            company="Generic IT",
            area="architecture",
            top_k=25,
        )


def test_retrieval_query_is_frozen() -> None:
    query = RetrievalQuery(
        query="Explain REST",
        role="backend",
        company="Generic IT",
        area="architecture",
    )

    with pytest.raises(ValidationError):
        query.top_k = 10
