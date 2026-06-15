# tools/corpus_audit/corpus_audit_runner.py
#
# Responsibility:
# Orchestrate the audit: collect metrics, build the report, write artifacts.
# No business logic. Errors propagate naturally.

import json
from datetime import datetime, timezone
from pathlib import Path

from tools.corpus_audit.corpus_audit_report import CorpusAuditReport
from tools.corpus_audit.corpus_metrics_service import CorpusMetricsService


class CorpusAuditRunner:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        metrics_service: CorpusMetricsService,
        output_dir: str = "tools/corpus_audit/output",
    ) -> None:

        self._metrics_service = metrics_service
        self._output_dir = Path(output_dir)

    # =====================================================
    # PUBLIC
    # =====================================================

    def run(self) -> CorpusAuditReport:

        coverage = self._metrics_service.compute_coverage()
        coding_coverage = self._metrics_service.compute_coding_coverage()
        duplicates = self._metrics_service.compute_duplicates()
        retrieval = self._metrics_service.compute_retrieval_statistics()

        report = CorpusAuditReport(
            coverage=coverage,
            coding_coverage=coding_coverage,
            duplicates=duplicates,
            retrieval=retrieval,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        self._write_artifacts(report)

        return report

    # =====================================================
    # INTERNALS
    # =====================================================

    def _write_artifacts(self, report: CorpusAuditReport) -> None:

        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._write_audit_json(report)
        self._write_summary_json(report)
        self._write_validation_json(report)

    def _write_audit_json(self, report: CorpusAuditReport) -> None:

        (self._output_dir / "audit.json").write_text(
            json.dumps(report.model_dump(), indent=2),
            encoding="utf-8",
        )

    def _write_summary_json(self, report: CorpusAuditReport) -> None:

        summary = {
            "generated_at": report.generated_at,
            "total_chunks": report.coverage.total_chunks,
            "total_embeddings": report.coverage.total_embeddings,
            "total_documents": report.coverage.total_documents,
            "total_coding_questions": report.coding_coverage.total_coding_questions,
            "exact_duplicate_count": report.duplicates.exact_duplicate_count,
            "duplicate_ratio": report.duplicates.duplicate_ratio,
            "average_retrieved_documents": report.retrieval.average_retrieved_documents,
            "duplicate_retrieval_occurrences": report.retrieval.duplicate_retrieval_occurrences,
        }

        (self._output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )

    def _write_validation_json(self, report: CorpusAuditReport) -> None:

        checks = [
            {
                "check": "corpus_loaded",
                "passed": report.coverage.total_chunks > 0,
                "detail": f"total_chunks={report.coverage.total_chunks}",
            },
            {
                "check": "metadata_available",
                "passed": bool(report.coverage.role_distribution),
                "detail": f"roles_found={len(report.coverage.role_distribution)}",
            },
            {
                "check": "embeddings_counted",
                "passed": report.coverage.total_embeddings > 0,
                "detail": f"total_embeddings={report.coverage.total_embeddings}",
            },
            {
                "check": "retrieval_statistics_collected",
                "passed": report.retrieval.average_retrieved_documents > 0,
                "detail": f"average_retrieved={report.retrieval.average_retrieved_documents}",
            },
        ]

        (self._output_dir / "validation.json").write_text(
            json.dumps({"checks": checks, "generated_at": report.generated_at}, indent=2),
            encoding="utf-8",
        )
