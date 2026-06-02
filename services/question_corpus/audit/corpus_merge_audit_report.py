# services/question_corpus/audit/corpus_merge_audit_report.py

from pydantic import BaseModel

from services.question_corpus.validations.contracts.corpus_validation_issue import (
    CorpusValidationIssue,
)
from services.question_corpus.validations.contracts.corpus_validation_report import (
    CorpusValidationReport,
)
from services.question_corpus.contracts.corpus_statistics_report import (
    CorpusStatisticsReport,
)
from services.question_intelligence.balancing.balancing_report import BalancingReport
from services.question_intelligence.corpus.corpus_diagnostics_report import (
    CorpusDiagnosticsReport,
)


class SourceSummary(BaseModel):

    path: str

    question_count: int

    areas_distribution: dict[str, int]

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class MergeTotals(BaseModel):

    raw_count: int

    unique_id_count: int

    unique_text_count: int

    duplicate_text_count: int

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class CorpusMergeAuditReport(BaseModel):

    sources: list[SourceSummary]

    merge_totals: MergeTotals

    schema_validation: CorpusValidationReport

    near_duplicates_token: list[CorpusValidationIssue]

    statistics: CorpusStatisticsReport

    diagnostics: CorpusDiagnosticsReport

    balancing: BalancingReport

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
