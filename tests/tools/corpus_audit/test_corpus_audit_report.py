# tests/tools/corpus_audit/test_corpus_audit_report.py

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from tools.corpus_audit.corpus_audit_report import (
    CodingCoverageMetrics,
    CorpusAuditReport,
    CoverageMetrics,
    DuplicateMetrics,
    RetrievalStatistics,
)
from tools.corpus_audit.corpus_audit_runner import CorpusAuditRunner


def _make_report() -> CorpusAuditReport:

    return CorpusAuditReport(
        coverage=CoverageMetrics(
            interview_type_distribution={"technical": 10, "hr": 5},
            role_distribution={"backend_engineer": 8, "ml_engineer": 7},
            seniority_distribution={"junior": 5, "mid": 6, "senior": 4},
            total_documents=15,
            total_chunks=15,
            total_embeddings=15,
        ),
        coding_coverage=CodingCoverageMetrics(
            total_coding_questions=5,
            by_role={"backend_engineer": 3, "ml_engineer": 2},
            by_seniority={"mid": 3, "senior": 2},
        ),
        duplicates=DuplicateMetrics(
            exact_duplicate_count=1,
            duplicate_ratio=0.0667,
        ),
        retrieval=RetrievalStatistics(
            fetch_k=20,
            average_retrieved_documents=3.0,
            duplicate_retrieval_occurrences=2,
        ),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _make_mock_service(report: CorpusAuditReport) -> MagicMock:

    svc = MagicMock()
    svc.compute_coverage.return_value = report.coverage
    svc.compute_coding_coverage.return_value = report.coding_coverage
    svc.compute_duplicates.return_value = report.duplicates
    svc.compute_retrieval_statistics.return_value = report.retrieval
    return svc


def test_report_is_frozen() -> None:

    report = _make_report()

    raised = False
    try:
        report.generated_at = "tampered"  # type: ignore[misc]
    except Exception:
        raised = True

    assert raised


def test_report_model_dump_is_json_serializable() -> None:

    report = _make_report()

    serialized = json.dumps(report.model_dump())

    assert "coverage" in serialized
    assert "coding_coverage" in serialized
    assert "duplicates" in serialized
    assert "retrieval" in serialized


def test_audit_json_written_with_full_report() -> None:

    report = _make_report()

    with tempfile.TemporaryDirectory() as tmp:

        runner = CorpusAuditRunner(
            metrics_service=_make_mock_service(report),
            output_dir=tmp,
        )
        runner.run()

        content = json.loads((Path(tmp) / "audit.json").read_text())

        assert content["coverage"]["total_chunks"] == 15
        assert content["coding_coverage"]["total_coding_questions"] == 5
        assert content["duplicates"]["exact_duplicate_count"] == 1
        assert content["retrieval"]["fetch_k"] == 20


def test_summary_json_contains_high_level_fields_only() -> None:

    report = _make_report()

    with tempfile.TemporaryDirectory() as tmp:

        runner = CorpusAuditRunner(
            metrics_service=_make_mock_service(report),
            output_dir=tmp,
        )
        runner.run()

        content = json.loads((Path(tmp) / "summary.json").read_text())

        assert "total_chunks" in content
        assert "total_embeddings" in content
        assert "total_coding_questions" in content
        assert "duplicate_ratio" in content
        assert "average_retrieved_documents" in content
        # Nested distributions must not appear in summary
        assert "role_distribution" not in content


def test_validation_json_contains_required_checks() -> None:

    report = _make_report()

    with tempfile.TemporaryDirectory() as tmp:

        runner = CorpusAuditRunner(
            metrics_service=_make_mock_service(report),
            output_dir=tmp,
        )
        runner.run()

        content = json.loads((Path(tmp) / "validation.json").read_text())

        assert "checks" in content

        check_names = {c["check"] for c in content["checks"]}

        assert "corpus_loaded" in check_names
        assert "metadata_available" in check_names
        assert "embeddings_counted" in check_names
        assert "retrieval_statistics_collected" in check_names


def test_validation_checks_fail_on_empty_corpus() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        svc = MagicMock()
        svc.compute_coverage.return_value = CoverageMetrics(
            interview_type_distribution={},
            role_distribution={},
            seniority_distribution={},
            total_documents=0,
            total_chunks=0,
            total_embeddings=0,
        )
        svc.compute_coding_coverage.return_value = CodingCoverageMetrics(
            total_coding_questions=0,
            by_role={},
            by_seniority={},
        )
        svc.compute_duplicates.return_value = DuplicateMetrics(
            exact_duplicate_count=0,
            duplicate_ratio=0.0,
        )
        svc.compute_retrieval_statistics.return_value = RetrievalStatistics(
            fetch_k=20,
            average_retrieved_documents=0.0,
            duplicate_retrieval_occurrences=0,
        )

        runner = CorpusAuditRunner(metrics_service=svc, output_dir=tmp)
        runner.run()

        content = json.loads((Path(tmp) / "validation.json").read_text())
        by_name = {c["check"]: c for c in content["checks"]}

        assert by_name["corpus_loaded"]["passed"] is False
        assert by_name["retrieval_statistics_collected"]["passed"] is False
