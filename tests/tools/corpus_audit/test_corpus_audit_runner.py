# tests/tools/corpus_audit/test_corpus_audit_runner.py

import json
import tempfile
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


def _make_mock_service() -> MagicMock:

    svc = MagicMock()

    svc.compute_coverage.return_value = CoverageMetrics(
        interview_type_distribution={"technical": 5},
        role_distribution={"backend_engineer": 5},
        seniority_distribution={"mid": 5},
        total_documents=5,
        total_chunks=5,
        total_embeddings=5,
    )
    svc.compute_coding_coverage.return_value = CodingCoverageMetrics(
        total_coding_questions=2,
        by_role={"backend_engineer": 2},
        by_seniority={"mid": 2},
    )
    svc.compute_duplicates.return_value = DuplicateMetrics(
        exact_duplicate_count=0,
        duplicate_ratio=0.0,
    )
    svc.compute_retrieval_statistics.return_value = RetrievalStatistics(
        fetch_k=20,
        average_retrieved_documents=2.0,
        duplicate_retrieval_occurrences=0,
    )

    return svc


def test_run_calls_each_compute_method_once() -> None:

    svc = _make_mock_service()

    with tempfile.TemporaryDirectory() as tmp:
        CorpusAuditRunner(metrics_service=svc, output_dir=tmp).run()

    svc.compute_coverage.assert_called_once()
    svc.compute_coding_coverage.assert_called_once()
    svc.compute_duplicates.assert_called_once()
    svc.compute_retrieval_statistics.assert_called_once()


def test_run_returns_corpus_audit_report() -> None:

    svc = _make_mock_service()

    with tempfile.TemporaryDirectory() as tmp:
        result = CorpusAuditRunner(metrics_service=svc, output_dir=tmp).run()

    assert isinstance(result, CorpusAuditReport)


def test_run_assembles_report_from_service_outputs() -> None:

    svc = _make_mock_service()

    with tempfile.TemporaryDirectory() as tmp:
        result = CorpusAuditRunner(metrics_service=svc, output_dir=tmp).run()

    assert result.coverage == svc.compute_coverage.return_value
    assert result.coding_coverage == svc.compute_coding_coverage.return_value
    assert result.duplicates == svc.compute_duplicates.return_value
    assert result.retrieval == svc.compute_retrieval_statistics.return_value


def test_run_writes_all_three_artifacts() -> None:

    svc = _make_mock_service()

    with tempfile.TemporaryDirectory() as tmp:
        CorpusAuditRunner(metrics_service=svc, output_dir=tmp).run()

        assert (Path(tmp) / "audit.json").exists()
        assert (Path(tmp) / "summary.json").exists()
        assert (Path(tmp) / "validation.json").exists()


def test_run_creates_output_dir_if_missing() -> None:

    svc = _make_mock_service()

    with tempfile.TemporaryDirectory() as tmp:
        nested = str(Path(tmp) / "deep" / "nested")
        CorpusAuditRunner(metrics_service=svc, output_dir=nested).run()

        assert (Path(nested) / "audit.json").exists()
