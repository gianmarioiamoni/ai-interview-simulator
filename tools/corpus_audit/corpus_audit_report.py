# tools/corpus_audit/corpus_audit_report.py
#
# Responsibility:
# Define all data contracts for the corpus audit.
# All sub-models are colocated here — no model proliferation.

from pydantic import BaseModel


class CoverageMetrics(BaseModel):

    interview_type_distribution: dict[str, int]
    role_distribution: dict[str, int]
    seniority_distribution: dict[str, int]
    total_documents: int
    total_chunks: int
    total_embeddings: int

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class CodingCoverageMetrics(BaseModel):

    total_coding_questions: int
    by_role: dict[str, int]
    by_seniority: dict[str, int]

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class DuplicateMetrics(BaseModel):

    exact_duplicate_count: int
    duplicate_ratio: float

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class RetrievalStatistics(BaseModel):

    fetch_k: int
    average_retrieved_documents: float
    duplicate_retrieval_occurrences: int

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class CorpusAuditReport(BaseModel):

    coverage: CoverageMetrics
    coding_coverage: CodingCoverageMetrics
    duplicates: DuplicateMetrics
    retrieval: RetrievalStatistics

    # ISO-8601 UTC timestamp
    generated_at: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
