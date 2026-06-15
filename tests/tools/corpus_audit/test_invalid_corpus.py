# tests/tools/corpus_audit/test_invalid_corpus.py

from unittest.mock import MagicMock

from tools.corpus_audit.corpus_metrics_service import CorpusMetricsService


def _make_service(metadatas=None, documents=None, count=0, candidates=None):

    collection = MagicMock()
    collection.count.return_value = count

    def _get(include=None):
        result = {}
        if include and "metadatas" in include:
            result["metadatas"] = metadatas or []
        if include and "documents" in include:
            result["documents"] = documents or []
        return result

    collection.get.side_effect = _get

    return CorpusMetricsService(
        chroma_collection=collection,
        search_fn=MagicMock(return_value=candidates or []),
        fetch_k=20,
    )


def test_non_dict_metadata_entries_are_skipped_gracefully() -> None:

    metadatas = [
        None,
        "not_a_dict",
        42,
        {"role": "backend_engineer", "seniority": "mid", "interview_type": "technical", "document_id": "d1"},
    ]

    result = _make_service(metadatas=metadatas, count=4).compute_coverage()

    assert result.role_distribution.get("backend_engineer") == 1
    assert result.total_chunks == 4


def test_missing_role_key_does_not_raise() -> None:

    metadatas = [
        {"seniority": "mid", "interview_type": "technical", "document_id": "d1"},
    ]

    result = _make_service(metadatas=metadatas, count=1).compute_coverage()

    assert result.role_distribution == {}


def test_missing_seniority_key_does_not_raise() -> None:

    metadatas = [
        {"role": "backend_engineer", "interview_type": "technical", "document_id": "d1"},
    ]

    result = _make_service(metadatas=metadatas, count=1).compute_coverage()

    assert result.seniority_distribution == {}


def test_missing_document_id_still_counts_chunk() -> None:

    metadatas = [
        {"role": "backend_engineer", "seniority": "mid", "interview_type": "technical"},
    ]

    result = _make_service(metadatas=metadatas, count=1).compute_coverage()

    assert result.total_chunks == 1
    assert result.total_documents == 0


def test_non_string_documents_excluded_from_duplicate_check() -> None:

    documents = ["Valid text.", None, 42, "Valid text."]

    result = _make_service(documents=documents, count=4).compute_duplicates()

    assert result.exact_duplicate_count == 1


def test_empty_probe_results_do_not_crash() -> None:

    collection = MagicMock()
    collection.count.return_value = 0
    collection.get.return_value = {"metadatas": [], "documents": []}

    service = CorpusMetricsService(
        chroma_collection=collection,
        search_fn=MagicMock(return_value=[]),
        fetch_k=20,
    )

    result = service.compute_retrieval_statistics()

    assert result.average_retrieved_documents == 0.0
    assert result.duplicate_retrieval_occurrences == 0


def test_metadata_none_values_do_not_pollute_distributions() -> None:

    metadatas = [
        {"role": None, "seniority": None, "interview_type": None, "document_id": None},
    ]

    result = _make_service(metadatas=metadatas, count=1).compute_coverage()

    assert None not in result.role_distribution
    assert None not in result.seniority_distribution
    assert result.total_documents == 0
