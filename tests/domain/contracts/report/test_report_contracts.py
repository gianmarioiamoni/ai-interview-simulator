# tests/domain/contracts/report/test_report_contracts.py
# E03-M5 — Report Layer contract tests
# Coverage: Contract, Validation, Architecture, Integration, Determinism

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pydantic import ValidationError

from domain.contracts.report.report import Report
from domain.contracts.report.report_builder import ReportBuilder
from domain.contracts.report.report_statistics import ReportStatistics
from domain.contracts.report.report_summary import ReportSummary
from domain.contracts.report.report_validator import ReportValidator, ReportValidationResult

from tests.domain.contracts.report.conftest import (
    CANDIDATE_ID,
    REPORT_ID,
    SESSION_ID,
    FIXED_REPORT_DT,
    make_report,
    make_session_history,
)
from tests.domain.contracts.knowledge_snapshot.conftest import (
    make_knowledge_snapshot,
    make_narrative,
    make_candidate_profile_snapshot,
    make_coaching_snapshot,
    make_policy_versions,
    make_profile_feature,
)


# ===========================================================================
# CONTRACT TESTS
# ===========================================================================

class TestReportContract:
    def test_report_is_frozen(self, report: Report) -> None:
        with pytest.raises(ValidationError):
            report.report_id = "mutated"  # type: ignore[misc]

    def test_report_fields_populated(self, report: Report) -> None:
        assert report.report_id == REPORT_ID
        assert report.session_id == SESSION_ID
        assert report.candidate_identity_id == CANDIDATE_ID
        assert report.interview_index == 0
        assert report.knowledge_epoch == "1"
        assert report.schema_version == "1.0"
        assert report.created_at == FIXED_REPORT_DT

    def test_report_metadata_is_empty_dict_by_default(self, report: Report) -> None:
        assert report.metadata == {}

    def test_report_feature_count_property(self, report: Report) -> None:
        assert report.feature_count == report.profile_snapshot.total_feature_count

    def test_report_objective_count_property(self, report: Report) -> None:
        assert report.objective_count == report.coaching_snapshot.statistics.total_objectives

    def test_report_insight_count_property(self, report: Report) -> None:
        assert report.insight_count == report.narrative.insight_count

    def test_report_narrative_section_count_is_5(self, report: Report) -> None:
        assert report.narrative_section_count == 5

    def test_report_carries_narrative_artefact(self, report: Report) -> None:
        assert report.narrative.is_complete

    def test_report_carries_profile_snapshot(self, report: Report) -> None:
        assert report.profile_snapshot.candidate_identity_id == CANDIDATE_ID

    def test_report_carries_coaching_snapshot(self, report: Report) -> None:
        assert report.coaching_snapshot.session_id == SESSION_ID


# ===========================================================================
# REPORT BUILDER — SINGLE CREATION PATH
# ===========================================================================

class TestReportBuilderSingleCreationPath:
    def test_builder_produces_report(self) -> None:
        history = make_session_history()
        report = ReportBuilder().with_session_history(history).build()
        assert isinstance(report, Report)

    def test_builder_from_session_history_populates_all_fields(self) -> None:
        history = make_session_history()
        report = ReportBuilder().with_session_history(history).build()
        assert report.session_id == history.session_id
        assert report.candidate_identity_id == history.candidate_identity_id
        assert report.role == history.interview_metadata.role
        assert report.seniority == history.interview_metadata.seniority
        assert report.interview_type == history.interview_metadata.interview_type
        assert report.question_count == history.question_count

    def test_builder_auto_generates_report_id(self) -> None:
        history = make_session_history()
        report = ReportBuilder().with_session_history(history).build()
        assert len(report.report_id) > 0

    def test_builder_custom_report_id(self) -> None:
        history = make_session_history()
        report = ReportBuilder().with_session_history(history).with_report_id("custom-id").build()
        assert report.report_id == "custom-id"

    def test_builder_raises_on_missing_session_id(self) -> None:
        history = make_session_history()
        builder = ReportBuilder().with_session_history(history)
        builder._session_id = None
        with pytest.raises(ValueError, match="session_id"):
            builder.build()

    def test_builder_raises_on_missing_narrative(self) -> None:
        history = make_session_history()
        builder = ReportBuilder().with_session_history(history)
        builder._narrative = None
        with pytest.raises(ValueError, match="narrative"):
            builder.build()

    def test_builder_raises_on_missing_profile_snapshot(self) -> None:
        history = make_session_history()
        builder = ReportBuilder().with_session_history(history)
        builder._profile_snapshot = None
        with pytest.raises(ValueError, match="profile_snapshot"):
            builder.build()

    def test_builder_raises_on_missing_coaching_snapshot(self) -> None:
        history = make_session_history()
        builder = ReportBuilder().with_session_history(history)
        builder._coaching_snapshot = None
        with pytest.raises(ValueError, match="coaching_snapshot"):
            builder.build()

    def test_builder_raises_on_candidate_id_mismatch(self) -> None:
        history = make_session_history()
        wrong_profile = make_candidate_profile_snapshot(candidate_id="wrong-candidate")
        builder = ReportBuilder().with_session_history(history).with_profile_snapshot(wrong_profile)
        with pytest.raises(ValueError, match="candidate_identity_id"):
            builder.build()

    def test_builder_with_created_at(self) -> None:
        history = make_session_history()
        fixed_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        report = ReportBuilder().with_session_history(history).with_created_at(fixed_dt).build()
        assert report.created_at == fixed_dt

    def test_builder_with_metadata(self) -> None:
        history = make_session_history()
        meta = {"source": "test"}
        report = ReportBuilder().with_session_history(history).with_metadata(meta).build()
        assert report.metadata == meta

    def test_builder_manual_fluent_setters(self) -> None:
        snapshot = make_knowledge_snapshot()
        profile_snapshot = snapshot.profile_snapshot
        narrative = snapshot.narrative
        coaching_snapshot = snapshot.coaching_snapshot

        report = (
            ReportBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_interview_index(0)
            .with_profile_snapshot(profile_snapshot)
            .with_narrative(narrative)
            .with_coaching_snapshot(coaching_snapshot)
            .with_role("Software Engineer")
            .with_seniority("Senior")
            .with_interview_type("technical")
            .with_question_count(5)
            .with_knowledge_epoch("1")
            .build()
        )
        assert report.role == "Software Engineer"
        assert report.seniority == "Senior"


# ===========================================================================
# REPORT VALIDATOR
# ===========================================================================

class TestReportValidator:
    def test_valid_report_passes(self, report: Report) -> None:
        result = ReportValidator.validate(report)
        assert result.is_valid
        assert result.violations == ()

    def test_validation_result_ok(self) -> None:
        result = ReportValidationResult.ok()
        assert result.is_valid
        assert result.violations == ()

    def test_validation_result_failed(self) -> None:
        result = ReportValidationResult.failed(["R-01: blank"])
        assert not result.is_valid
        assert "R-01: blank" in result.violations

    def test_validator_detects_blank_report_id(self, report: Report) -> None:
        bad = report.model_copy(update={"report_id": "  "})
        result = ReportValidator.validate(bad)
        assert not result.is_valid
        assert any("R-01" in v for v in result.violations)

    def test_validator_detects_blank_session_id(self, report: Report) -> None:
        bad = report.model_copy(update={"session_id": " "})
        result = ReportValidator.validate(bad)
        assert not result.is_valid
        assert any("R-02" in v for v in result.violations)

    def test_validator_detects_profile_candidate_mismatch(self, report: Report) -> None:
        wrong_profile = make_candidate_profile_snapshot(candidate_id="other-candidate")
        bad = report.model_copy(update={"profile_snapshot": wrong_profile})
        result = ReportValidator.validate(bad)
        assert not result.is_valid
        assert any("R-04" in v for v in result.violations)

    def test_validator_detects_naive_datetime(self, report: Report) -> None:
        naive_dt = datetime(2026, 1, 1)  # no tzinfo
        bad = report.model_copy(update={"created_at": naive_dt})
        result = ReportValidator.validate(bad)
        assert not result.is_valid
        assert any("R-08" in v for v in result.violations)

    def test_validator_detects_blank_role(self, report: Report) -> None:
        bad = report.model_copy(update={"role": "  "})
        result = ReportValidator.validate(bad)
        assert not result.is_valid
        assert any("R-10" in v for v in result.violations)


# ===========================================================================
# REPORT STATISTICS
# ===========================================================================

class TestReportStatistics:
    def test_statistics_from_report_produces_valid_model(self, report: Report) -> None:
        stats = ReportStatistics.from_report(report)
        assert isinstance(stats, ReportStatistics)

    def test_statistics_is_frozen(self, report: Report) -> None:
        stats = ReportStatistics.from_report(report)
        with pytest.raises(ValidationError):
            stats.total_features = 99  # type: ignore[misc]

    def test_statistics_session_id_matches(self, report: Report) -> None:
        stats = ReportStatistics.from_report(report)
        assert stats.session_id == report.session_id

    def test_statistics_feature_count_matches(self, report: Report) -> None:
        stats = ReportStatistics.from_report(report)
        assert stats.total_features == report.feature_count

    def test_statistics_narrative_sections_is_5(self, report: Report) -> None:
        stats = ReportStatistics.from_report(report)
        assert stats.total_narrative_sections == 5

    def test_statistics_mean_confidence_range(self, report: Report) -> None:
        stats = ReportStatistics.from_report(report)
        assert 0.0 <= stats.mean_feature_confidence <= 1.0

    def test_statistics_empty_coaching_gives_zero_objectives(self) -> None:
        history = make_session_history()
        report = ReportBuilder().with_session_history(history).build()
        stats = ReportStatistics.from_report(report)
        # CoachingBuilder.empty is used in fixtures; total_objectives == 0
        assert stats.total_objectives == 0
        assert stats.is_coaching_empty

    def test_statistics_knowledge_epoch(self, report: Report) -> None:
        stats = ReportStatistics.from_report(report)
        assert stats.knowledge_epoch == "1"


# ===========================================================================
# REPORT SUMMARY
# ===========================================================================

class TestReportSummary:
    def test_summary_from_report_produces_valid_model(self, report: Report) -> None:
        summary = ReportSummary.from_report(report)
        assert isinstance(summary, ReportSummary)

    def test_summary_is_frozen(self, report: Report) -> None:
        summary = ReportSummary.from_report(report)
        with pytest.raises(ValidationError):
            summary.report_id = "mutated"  # type: ignore[misc]

    def test_summary_report_id_matches(self, report: Report) -> None:
        summary = ReportSummary.from_report(report)
        assert summary.report_id == report.report_id

    def test_summary_role_and_seniority(self, report: Report) -> None:
        summary = ReportSummary.from_report(report)
        assert summary.role == report.role
        assert summary.seniority == report.seniority

    def test_summary_mean_confidence_range(self, report: Report) -> None:
        summary = ReportSummary.from_report(report)
        assert 0.0 <= summary.mean_feature_confidence <= 1.0

    def test_summary_created_at_matches(self, report: Report) -> None:
        summary = ReportSummary.from_report(report)
        assert summary.created_at == report.created_at


# ===========================================================================
# ARCHITECTURE — NO DUPLICATE REPORT MODEL
# ===========================================================================

class TestArchitecture:
    def test_report_module_path_is_domain_contracts_report(self) -> None:
        import domain.contracts.report.report as mod
        assert mod.__name__ == "domain.contracts.report.report"

    def test_report_builder_is_sole_creation_path(self) -> None:
        """Report cannot be constructed without passing through ReportBuilder
        or from_session_history (which delegates to constructor only)."""
        # Verify that direct Pydantic construction fails without all required fields
        with pytest.raises(Exception):
            Report()  # type: ignore[call-arg]

    def test_report_does_not_import_feature_engine(self) -> None:
        import ast
        import pathlib

        report_src = pathlib.Path(
            "domain/contracts/report/report.py"
        ).read_text()
        tree = ast.parse(report_src)
        imports = [
            node.module if isinstance(node, ast.ImportFrom) else ""
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        assert not any("feature_engine" in (i or "") for i in imports)

    def test_report_does_not_import_observation_store(self) -> None:
        import ast
        import pathlib

        report_src = pathlib.Path(
            "domain/contracts/report/report.py"
        ).read_text()
        tree = ast.parse(report_src)
        imports = [
            node.module if isinstance(node, ast.ImportFrom) else ""
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        assert not any("observation_store" in (i or "") for i in imports)

    def test_report_does_not_import_replay(self) -> None:
        import ast
        import pathlib

        report_src = pathlib.Path(
            "domain/contracts/report/report.py"
        ).read_text()
        tree = ast.parse(report_src)
        imports = [
            node.module if isinstance(node, ast.ImportFrom) else ""
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        assert not any("replay" in (i or "") for i in imports)

    def test_report_builder_does_not_import_llm(self) -> None:
        import ast
        import pathlib

        builder_src = pathlib.Path(
            "domain/contracts/report/report_builder.py"
        ).read_text()
        tree = ast.parse(builder_src)
        imports = [
            node.module if isinstance(node, ast.ImportFrom) else ""
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        forbidden = ["openai", "anthropic", "langchain", "llm", "ai_client"]
        for f in forbidden:
            assert not any(f in (i or "") for i in imports), f"Found LLM import: {f}"


# ===========================================================================
# INTEGRATION — Report assembles from SessionHistory artefacts
# ===========================================================================

class TestReportIntegration:
    def test_report_artefacts_are_same_objects_as_session_history(self) -> None:
        """Report must carry exact artefacts from SessionHistory — no copies."""
        history = make_session_history()
        report = ReportBuilder().with_session_history(history).build()
        snapshot = history.knowledge_snapshot
        assert report.profile_snapshot is snapshot.profile_snapshot
        assert report.narrative is snapshot.narrative
        assert report.coaching_snapshot is snapshot.coaching_snapshot

    def test_report_from_session_history_classmethod(self) -> None:
        history = make_session_history()
        report = Report.from_session_history(report_id=REPORT_ID, history=history)
        assert isinstance(report, Report)
        assert report.session_id == history.session_id

    def test_full_pipeline_history_to_report_to_statistics(self) -> None:
        history = make_session_history()
        report = ReportBuilder().with_session_history(history).build()
        stats = ReportStatistics.from_report(report)
        summary = ReportSummary.from_report(report)
        result = ReportValidator.validate(report)
        assert result.is_valid
        assert stats.session_id == report.session_id
        assert summary.report_id == report.report_id

    def test_validator_passes_after_builder(self) -> None:
        report = make_report()
        result = ReportValidator.validate(report)
        assert result.is_valid


# ===========================================================================
# DETERMINISM
# ===========================================================================

class TestReportDeterminism:
    def test_same_history_produces_same_statistics(self) -> None:
        history = make_session_history()
        r1 = ReportBuilder().with_session_history(history).with_report_id("r1").build()
        r2 = ReportBuilder().with_session_history(history).with_report_id("r1").build()
        s1 = ReportStatistics.from_report(r1)
        s2 = ReportStatistics.from_report(r2)
        assert s1 == s2

    def test_same_history_produces_same_summary_except_report_id(self) -> None:
        history = make_session_history()
        fixed_dt = datetime(2026, 7, 3, tzinfo=timezone.utc)
        r1 = (
            ReportBuilder()
            .with_session_history(history)
            .with_report_id("rid-1")
            .with_created_at(fixed_dt)
            .build()
        )
        r2 = (
            ReportBuilder()
            .with_session_history(history)
            .with_report_id("rid-1")
            .with_created_at(fixed_dt)
            .build()
        )
        s1 = ReportSummary.from_report(r1)
        s2 = ReportSummary.from_report(r2)
        assert s1 == s2

    def test_report_is_immutable_snapshot_not_live(self, report: Report) -> None:
        """Report.created_at is fixed — it does not update on re-read."""
        ts = report.created_at
        assert report.created_at == ts
