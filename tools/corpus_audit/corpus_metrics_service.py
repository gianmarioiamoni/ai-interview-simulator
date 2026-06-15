# tools/corpus_audit/corpus_metrics_service.py
#
# Responsibility:
# Compute all corpus audit metrics from an injected Chroma collection
# and an injected search callable.
# Pure computation — no I/O, no artifact writing.

from collections import Counter
from typing import Callable

from domain.contracts.interview.interview_area import InterviewArea
from tools.corpus_audit.corpus_audit_report import (
    CodingCoverageMetrics,
    CoverageMetrics,
    DuplicateMetrics,
    RetrievalStatistics,
)

# Neutral probe phrases used to collect retrieval statistics.
# Not interview questions — domain-neutral technical phrases only.
_PROBE_QUERIES: list[str] = [
    "backend engineer distributed systems",
    "frontend engineer react performance",
    "devops kubernetes deployment",
    "data engineer pipeline design",
    "machine learning model evaluation",
    "system design scalability",
    "database query optimization",
    "coding algorithm complexity",
    "technical background experience",
    "case study architecture trade-offs",
]


class CorpusMetricsService:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        # Any object exposing .count() -> int and .get(include=...) -> dict
        chroma_collection: object,
        # Any callable: (query: str, k: int) -> list[object]
        search_fn: Callable[[str, int], list[object]],
        fetch_k: int = 20,
    ) -> None:

        self._collection = chroma_collection
        self._search_fn = search_fn
        self._fetch_k = fetch_k

    # =====================================================
    # PUBLIC
    # =====================================================

    def compute_coverage(self) -> CoverageMetrics:

        result = self._collection.get(include=["metadatas"])

        metadatas: list[dict] = result.get("metadatas") or []

        interview_type_counts: Counter = Counter()
        role_counts: Counter = Counter()
        seniority_counts: Counter = Counter()
        document_ids: set[str] = set()

        for meta in metadatas:

            if not isinstance(meta, dict):
                continue

            interview_type = meta.get("interview_type")
            if interview_type:
                interview_type_counts[str(interview_type)] += 1

            role = meta.get("role")
            if role:
                role_counts[str(role)] += 1

            seniority = meta.get("seniority")
            if seniority:
                seniority_counts[str(seniority)] += 1

            doc_id = meta.get("document_id")
            if doc_id:
                document_ids.add(str(doc_id))

        total_embeddings: int = self._collection.count()

        return CoverageMetrics(
            interview_type_distribution=dict(interview_type_counts),
            role_distribution=dict(role_counts),
            seniority_distribution=dict(seniority_counts),
            total_documents=len(document_ids),
            total_chunks=len(metadatas),
            total_embeddings=total_embeddings,
        )

    def compute_coding_coverage(self) -> CodingCoverageMetrics:

        result = self._collection.get(include=["metadatas"])

        metadatas: list[dict] = result.get("metadatas") or []

        coding_area = InterviewArea.TECH_CODING.value

        by_role: Counter = Counter()
        by_seniority: Counter = Counter()

        for meta in metadatas:

            if not isinstance(meta, dict):
                continue

            if meta.get("area") != coding_area:
                continue

            role = meta.get("role")
            if role:
                by_role[str(role)] += 1

            seniority = meta.get("seniority")
            if seniority:
                by_seniority[str(seniority)] += 1

        return CodingCoverageMetrics(
            total_coding_questions=sum(by_role.values()),
            by_role=dict(by_role),
            by_seniority=dict(by_seniority),
        )

    def compute_duplicates(self) -> DuplicateMetrics:

        result = self._collection.get(include=["documents"])

        documents: list[str] = result.get("documents") or []

        texts = [d for d in documents if isinstance(d, str)]

        total = len(texts)
        unique_count = len(set(texts))
        exact_duplicate_count = total - unique_count

        duplicate_ratio = 0.0
        if total > 0:
            duplicate_ratio = round(exact_duplicate_count / total, 4)

        return DuplicateMetrics(
            exact_duplicate_count=exact_duplicate_count,
            duplicate_ratio=duplicate_ratio,
        )

    def compute_retrieval_statistics(self) -> RetrievalStatistics:

        total_retrieved = 0
        all_doc_ids: list[str] = []

        for query in _PROBE_QUERIES:

            candidates = self._search_fn(query, self._fetch_k)

            total_retrieved += len(candidates)

            for candidate in candidates:

                if hasattr(candidate, "document"):
                    doc_id = candidate.document.metadata.get("document_id", "")
                elif isinstance(candidate, dict):
                    doc_id = candidate.get("document_id", "")
                else:
                    doc_id = ""

                all_doc_ids.append(str(doc_id))

        probe_count = len(_PROBE_QUERIES)

        average_retrieved = 0.0
        if probe_count > 0:
            average_retrieved = round(total_retrieved / probe_count, 2)

        id_counts = Counter(all_doc_ids)
        duplicate_retrieval_occurrences = sum(
            count - 1 for count in id_counts.values() if count > 1
        )

        return RetrievalStatistics(
            fetch_k=self._fetch_k,
            average_retrieved_documents=average_retrieved,
            duplicate_retrieval_occurrences=duplicate_retrieval_occurrences,
        )
