# tests/tools/corpus_audit/test_empty_corpus.py

from unittest.mock import MagicMock

from tools.corpus_audit.corpus_metrics_service import CorpusMetricsService


def _make_empty_service() -> CorpusMetricsService:

    collection = MagicMock()
    collection.count.return_value = 0
    collection.get.return_value = {"metadatas": [], "documents": []}

    return CorpusMetricsService(
        chroma_collection=collection,
        search_fn=MagicMock(return_value=[]),
        fetch_k=20,
    )


def test_empty_coverage_returns_zero_totals() -> None:

    result = _make_empty_service().compute_coverage()

    assert result.total_chunks == 0
    assert result.total_documents == 0
    assert result.total_embeddings == 0
    assert result.interview_type_distribution == {}
    assert result.role_distribution == {}
    assert result.seniority_distribution == {}


def test_empty_coding_coverage_returns_zero() -> None:

    result = _make_empty_service().compute_coding_coverage()

    assert result.total_coding_questions == 0
    assert result.by_role == {}
    assert result.by_seniority == {}


def test_empty_duplicates_returns_zero() -> None:

    result = _make_empty_service().compute_duplicates()

    assert result.exact_duplicate_count == 0
    assert result.duplicate_ratio == 0.0


def test_empty_retrieval_returns_zero_average() -> None:

    result = _make_empty_service().compute_retrieval_statistics()

    assert result.average_retrieved_documents == 0.0
    assert result.duplicate_retrieval_occurrences == 0
    assert result.fetch_k == 20
