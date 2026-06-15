# tests/tools/corpus_audit/test_corpus_metrics_service.py

from collections import Counter
from unittest.mock import MagicMock

from langchain_core.documents import Document

from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from tools.corpus_audit.corpus_metrics_service import CorpusMetricsService


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_service(
    metadatas: list[dict] | None = None,
    documents: list[str] | None = None,
    count: int = 0,
    candidates: list | None = None,
    fetch_k: int = 20,
) -> CorpusMetricsService:

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
        fetch_k=fetch_k,
    )


def _make_candidate(document_id: str) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content="Sample text.",
            metadata={"document_id": document_id},
        ),
        semantic_score=0.8,
        quality_score=0.9,
        final_score=0.85,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Coverage Metrics
# ─────────────────────────────────────────────────────────────────────────────

def test_coverage_counts_interview_types() -> None:

    metadatas = [
        {"interview_type": "technical", "role": "backend_engineer", "seniority": "mid", "document_id": "d1"},
        {"interview_type": "technical", "role": "frontend_engineer", "seniority": "junior", "document_id": "d2"},
        {"interview_type": "hr", "role": "backend_engineer", "seniority": "senior", "document_id": "d3"},
    ]

    service = _make_service(metadatas=metadatas, count=3)

    result = service.compute_coverage()

    assert result.interview_type_distribution["technical"] == 2
    assert result.interview_type_distribution["hr"] == 1


def test_coverage_counts_roles() -> None:

    metadatas = [
        {"role": "backend_engineer", "seniority": "mid", "interview_type": "technical", "document_id": "d1"},
        {"role": "backend_engineer", "seniority": "junior", "interview_type": "technical", "document_id": "d2"},
        {"role": "ml_engineer", "seniority": "senior", "interview_type": "technical", "document_id": "d3"},
    ]

    service = _make_service(metadatas=metadatas, count=3)

    result = service.compute_coverage()

    assert result.role_distribution["backend_engineer"] == 2
    assert result.role_distribution["ml_engineer"] == 1


def test_coverage_counts_seniority() -> None:

    metadatas = [
        {"seniority": "junior", "role": "backend_engineer", "interview_type": "technical", "document_id": "d1"},
        {"seniority": "senior", "role": "ml_engineer", "interview_type": "technical", "document_id": "d2"},
        {"seniority": "senior", "role": "frontend_engineer", "interview_type": "technical", "document_id": "d3"},
    ]

    service = _make_service(metadatas=metadatas, count=3)

    result = service.compute_coverage()

    assert result.seniority_distribution["junior"] == 1
    assert result.seniority_distribution["senior"] == 2


def test_coverage_deduplicates_document_ids() -> None:

    metadatas = [
        {"document_id": "doc-1", "role": "backend_engineer", "seniority": "mid", "interview_type": "technical"},
        {"document_id": "doc-1", "role": "backend_engineer", "seniority": "mid", "interview_type": "technical"},
        {"document_id": "doc-2", "role": "ml_engineer", "seniority": "senior", "interview_type": "technical"},
    ]

    service = _make_service(metadatas=metadatas, count=3)

    result = service.compute_coverage()

    assert result.total_documents == 2
    assert result.total_chunks == 3


def test_coverage_reads_total_embeddings_from_collection() -> None:

    service = _make_service(metadatas=[], count=42)

    result = service.compute_coverage()

    assert result.total_embeddings == 42


def test_coverage_skips_non_dict_metadata() -> None:

    collection = MagicMock()
    collection.count.return_value = 0
    collection.get.side_effect = lambda include=None: {
        "metadatas": [
            None,
            "invalid",
            {"role": "backend_engineer", "seniority": "mid", "interview_type": "technical", "document_id": "d1"},
        ]
    }

    service = CorpusMetricsService(
        chroma_collection=collection,
        search_fn=MagicMock(return_value=[]),
    )

    result = service.compute_coverage()

    assert result.role_distribution.get("backend_engineer") == 1


# ─────────────────────────────────────────────────────────────────────────────
# Coding Coverage Metrics
# ─────────────────────────────────────────────────────────────────────────────

def test_coding_coverage_isolates_coding_area() -> None:

    metadatas = [
        {"area": "technical_coding", "role": "backend_engineer", "seniority": "mid", "document_id": "d1"},
        {"area": "technical_coding", "role": "frontend_engineer", "seniority": "junior", "document_id": "d2"},
        {"area": "technical_background", "role": "backend_engineer", "seniority": "mid", "document_id": "d3"},
    ]

    service = _make_service(metadatas=metadatas, count=3)

    result = service.compute_coding_coverage()

    assert result.total_coding_questions == 2


def test_coding_coverage_by_role() -> None:

    metadatas = [
        {"area": "technical_coding", "role": "backend_engineer", "seniority": "mid", "document_id": "d1"},
        {"area": "technical_coding", "role": "backend_engineer", "seniority": "senior", "document_id": "d2"},
        {"area": "technical_coding", "role": "ml_engineer", "seniority": "junior", "document_id": "d3"},
    ]

    service = _make_service(metadatas=metadatas, count=3)

    result = service.compute_coding_coverage()

    assert result.by_role["backend_engineer"] == 2
    assert result.by_role["ml_engineer"] == 1


def test_coding_coverage_by_seniority() -> None:

    metadatas = [
        {"area": "technical_coding", "role": "backend_engineer", "seniority": "junior", "document_id": "d1"},
        {"area": "technical_coding", "role": "backend_engineer", "seniority": "junior", "document_id": "d2"},
        {"area": "technical_coding", "role": "ml_engineer", "seniority": "senior", "document_id": "d3"},
    ]

    service = _make_service(metadatas=metadatas, count=3)

    result = service.compute_coding_coverage()

    assert result.by_seniority["junior"] == 2
    assert result.by_seniority["senior"] == 1


def test_coding_coverage_returns_zero_when_no_coding_questions() -> None:

    metadatas = [
        {"area": "technical_background", "role": "backend_engineer", "seniority": "mid", "document_id": "d1"},
    ]

    service = _make_service(metadatas=metadatas, count=1)

    result = service.compute_coding_coverage()

    assert result.total_coding_questions == 0
    assert result.by_role == {}
    assert result.by_seniority == {}


# ─────────────────────────────────────────────────────────────────────────────
# Duplicate Metrics
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicates_detects_exact_match() -> None:

    documents = [
        "Explain SOLID principles.",
        "What is a binary tree?",
        "Explain SOLID principles.",
    ]

    service = _make_service(documents=documents, count=3)

    result = service.compute_duplicates()

    assert result.exact_duplicate_count == 1


def test_duplicates_computes_ratio() -> None:

    documents = ["A", "B", "A", "A"]

    service = _make_service(documents=documents, count=4)

    result = service.compute_duplicates()

    assert result.exact_duplicate_count == 2
    assert result.duplicate_ratio == 0.5


def test_duplicates_returns_zero_when_all_unique() -> None:

    documents = ["A", "B", "C"]

    service = _make_service(documents=documents, count=3)

    result = service.compute_duplicates()

    assert result.exact_duplicate_count == 0
    assert result.duplicate_ratio == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval Statistics
# ─────────────────────────────────────────────────────────────────────────────

def test_retrieval_statistics_returns_correct_fetch_k() -> None:

    service = _make_service(candidates=[], fetch_k=15)

    result = service.compute_retrieval_statistics()

    assert result.fetch_k == 15


def test_retrieval_statistics_averages_retrieved_documents() -> None:

    candidates = [_make_candidate("doc-1"), _make_candidate("doc-2")]

    service = _make_service(candidates=candidates, fetch_k=20)

    result = service.compute_retrieval_statistics()

    assert result.average_retrieved_documents == 2.0


def test_retrieval_statistics_counts_duplicate_occurrences() -> None:

    # doc-1 returned for every probe (10 probes × 1 candidate = 10 occurrences → 9 duplicates)
    candidates = [_make_candidate("doc-1")]

    service = _make_service(candidates=candidates, fetch_k=20)

    result = service.compute_retrieval_statistics()

    assert result.duplicate_retrieval_occurrences == 9


def test_retrieval_statistics_no_duplicates_when_all_distinct() -> None:

    collection = MagicMock()
    collection.count.return_value = 10
    collection.get.return_value = {"metadatas": [], "documents": []}

    search_fn = MagicMock()
    search_fn.side_effect = [
        [_make_candidate(f"doc-{i}")] for i in range(10)
    ]

    service = CorpusMetricsService(
        chroma_collection=collection,
        search_fn=search_fn,
        fetch_k=20,
    )

    result = service.compute_retrieval_statistics()

    assert result.duplicate_retrieval_occurrences == 0
