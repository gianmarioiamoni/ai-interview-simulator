# tests/domain/contracts/session_history/test_session_history_contracts.py
# ADR-022 — SessionHistory contract, validation, architecture, integration, determinism tests

from __future__ import annotations

import ast
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    ReplayMetadata,
    SessionHistory,
    TranscriptEntry,
)
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
from domain.contracts.session_history.session_history_statistics import SessionHistoryStatistics
from domain.contracts.session_history.session_history_summary import SessionHistorySummary
from domain.contracts.session_history.session_history_validator import (
    SessionHistoryValidationResult,
    SessionHistoryValidator,
)

from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    FIXED_HISTORY_DT,
    INTERVIEW_INDEX,
    make_interview_metadata,
    make_language_profile,
    make_question_timeline,
    make_session_history,
    make_transcript,
)

# ---------------------------------------------------------------------------
# CONTRACT — Structure & immutability
# ---------------------------------------------------------------------------


class TestSessionHistoryContract:
    def test_session_history_is_frozen(self, session_history: SessionHistory) -> None:
        with pytest.raises(Exception):
            session_history.session_id = "mutated"  # type: ignore[misc]

    def test_session_history_has_required_fields(self, session_history: SessionHistory) -> None:
        assert session_history.session_id == SESSION_ID
        assert session_history.candidate_identity_id == CANDIDATE_ID
        assert session_history.interview_index == INTERVIEW_INDEX
        assert session_history.knowledge_snapshot is not None
        assert session_history.interview_metadata is not None
        assert session_history.language_profile is not None

    def test_session_history_knowledge_epoch_delegates_to_snapshot(
        self, session_history: SessionHistory
    ) -> None:
        assert session_history.knowledge_epoch == session_history.knowledge_snapshot.knowledge_epoch
        assert session_history.knowledge_epoch == "1"

    def test_session_history_question_count_reflects_transcript(
        self, session_history: SessionHistory
    ) -> None:
        assert session_history.question_count == len(session_history.transcript)

    def test_session_history_is_replay_ready_delegates_to_replay_metadata(
        self, session_history: SessionHistory
    ) -> None:
        assert session_history.is_replay_ready == session_history.replay_metadata.snapshot_is_complete

    def test_session_history_transcript_is_tuple(self, session_history: SessionHistory) -> None:
        assert isinstance(session_history.transcript, tuple)

    def test_session_history_question_timeline_is_tuple(
        self, session_history: SessionHistory
    ) -> None:
        assert isinstance(session_history.question_timeline, tuple)

    def test_schema_version_defaults_to_1_0(self) -> None:
        history = make_session_history()
        assert history.schema_version == "1.0"

    def test_transcript_entry_is_frozen(self) -> None:
        entry = TranscriptEntry(
            question_index=0,
            question_id="q-001",
            question_prompt="prompt",
            answer_content="answer",
            answer_attempt=1,
        )
        with pytest.raises(Exception):
            entry.question_index = 99  # type: ignore[misc]

    def test_interview_metadata_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            InterviewMetadata(  # type: ignore[call-arg]
                role="Engineer",
                seniority="Mid",
                interview_type="technical",
                interview_mode="written",
                session_language="en",
                question_count=5,
                unknown_field="bad",
            )


# ---------------------------------------------------------------------------
# CONTRACT — Builder sole creation path
# ---------------------------------------------------------------------------


class TestSessionHistoryBuilderContract:
    def test_builder_is_sole_creation_path(self) -> None:
        history = make_session_history()
        assert isinstance(history, SessionHistory)

    def test_builder_raises_on_missing_session_id(self) -> None:
        snapshot = make_knowledge_snapshot()
        with pytest.raises(ValueError, match="session_id"):
            (
                SessionHistoryBuilder()
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_interview_index(0)
                .with_knowledge_snapshot(snapshot)
                .with_interview_metadata(make_interview_metadata())
                .with_language_profile(make_language_profile())
                .build()
            )

    def test_builder_raises_on_missing_candidate_identity_id(self) -> None:
        snapshot = make_knowledge_snapshot()
        with pytest.raises(ValueError, match="candidate_identity_id"):
            (
                SessionHistoryBuilder()
                .with_session_id(SESSION_ID)
                .with_interview_index(0)
                .with_knowledge_snapshot(snapshot)
                .with_interview_metadata(make_interview_metadata())
                .with_language_profile(make_language_profile())
                .build()
            )

    def test_builder_raises_on_missing_knowledge_snapshot(self) -> None:
        with pytest.raises(ValueError, match="knowledge_snapshot"):
            (
                SessionHistoryBuilder()
                .with_session_id(SESSION_ID)
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_interview_index(0)
                .with_interview_metadata(make_interview_metadata())
                .with_language_profile(make_language_profile())
                .build()
            )

    def test_builder_raises_on_missing_interview_metadata(self) -> None:
        snapshot = make_knowledge_snapshot()
        with pytest.raises(ValueError, match="interview_metadata"):
            (
                SessionHistoryBuilder()
                .with_session_id(SESSION_ID)
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_interview_index(0)
                .with_knowledge_snapshot(snapshot)
                .with_language_profile(make_language_profile())
                .build()
            )

    def test_builder_raises_on_missing_language_profile(self) -> None:
        snapshot = make_knowledge_snapshot()
        with pytest.raises(ValueError, match="language_profile"):
            (
                SessionHistoryBuilder()
                .with_session_id(SESSION_ID)
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_interview_index(0)
                .with_knowledge_snapshot(snapshot)
                .with_interview_metadata(make_interview_metadata())
                .build()
            )

    def test_builder_raises_on_candidate_identity_mismatch(self) -> None:
        snapshot = make_knowledge_snapshot(candidate_id=CANDIDATE_ID)
        with pytest.raises(ValueError, match="candidate_identity_id"):
            (
                SessionHistoryBuilder()
                .with_session_id(SESSION_ID)
                .with_candidate_identity_id("different-candidate")
                .with_interview_index(0)
                .with_knowledge_snapshot(snapshot)
                .with_interview_metadata(make_interview_metadata())
                .with_language_profile(make_language_profile())
                .build()
            )

    def test_builder_raises_on_snapshot_session_id_mismatch(self) -> None:
        snapshot = make_knowledge_snapshot(session_id=SESSION_ID)
        with pytest.raises(ValueError, match="session_id"):
            (
                SessionHistoryBuilder()
                .with_session_id("different-session")
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_interview_index(0)
                .with_knowledge_snapshot(snapshot)
                .with_interview_metadata(make_interview_metadata())
                .with_language_profile(make_language_profile(session_id="different-session"))
                .build()
            )

    def test_builder_raises_on_language_profile_session_id_mismatch(self) -> None:
        snapshot = make_knowledge_snapshot()
        with pytest.raises(ValueError, match="session_id"):
            (
                SessionHistoryBuilder()
                .with_session_id(SESSION_ID)
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_interview_index(0)
                .with_knowledge_snapshot(snapshot)
                .with_interview_metadata(make_interview_metadata())
                .with_language_profile(make_language_profile(session_id="wrong-session"))
                .build()
            )

    def test_builder_sets_created_at_to_utc_when_not_provided(self) -> None:
        history = (
            SessionHistoryBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_interview_index(0)
            .with_knowledge_snapshot(make_knowledge_snapshot())
            .with_interview_metadata(make_interview_metadata())
            .with_language_profile(make_language_profile())
            .build()
        )
        assert history.created_at.tzinfo is not None

    def test_builder_preserves_all_optional_fields(self) -> None:
        transcript = make_transcript()
        timeline = make_question_timeline()
        replay = ReplayMetadata(snapshot_is_complete=False, recomputation_available=True)
        history = (
            SessionHistoryBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_interview_index(2)
            .with_knowledge_snapshot(make_knowledge_snapshot())
            .with_interview_metadata(make_interview_metadata())
            .with_language_profile(make_language_profile())
            .with_transcript(transcript)
            .with_question_timeline(timeline)
            .with_replay_metadata(replay)
            .with_schema_version("2.0")
            .with_metadata({"tenant_id": "acme"})
            .with_created_at(FIXED_HISTORY_DT)
            .build()
        )
        assert history.interview_index == 2
        assert len(history.transcript) == 2
        assert len(history.question_timeline) == 2
        assert history.replay_metadata.snapshot_is_complete is False
        assert history.schema_version == "2.0"
        assert history.metadata == {"tenant_id": "acme"}


# ---------------------------------------------------------------------------
# VALIDATION — Invariant checks
# ---------------------------------------------------------------------------


class TestSessionHistoryValidator:
    def test_valid_history_passes(self, session_history: SessionHistory) -> None:
        result = SessionHistoryValidator.validate(session_history)
        assert result.is_valid
        assert len(result.violations) == 0

    def test_validation_result_ok_factory(self) -> None:
        result = SessionHistoryValidationResult.ok()
        assert result.is_valid
        assert result.violations == ()

    def test_validation_result_failed_factory(self) -> None:
        result = SessionHistoryValidationResult.failed(["SH-01: bad"])
        assert not result.is_valid
        assert "SH-01" in result.violations[0]

    def test_violates_sh04_when_candidate_identity_mismatch(self) -> None:
        # Construct via model to bypass builder guard (testing validator independence)
        history = make_session_history()
        # We patch the field via model_copy to simulate stored data corruption
        corrupted = history.model_copy(
            update={"candidate_identity_id": "different-candidate"}
        )
        result = SessionHistoryValidator.validate(corrupted)
        assert not result.is_valid
        assert any("SH-04" in v for v in result.violations)

    def test_violates_sh06_when_language_profile_session_mismatch(self) -> None:
        history = make_session_history()
        wrong_profile = make_language_profile(session_id="wrong-sess")
        corrupted = history.model_copy(update={"language_profile": wrong_profile})
        result = SessionHistoryValidator.validate(corrupted)
        assert not result.is_valid
        assert any("SH-06" in v for v in result.violations)

    def test_violates_sh07_when_schema_version_blank(self) -> None:
        history = make_session_history()
        corrupted = history.model_copy(update={"schema_version": "   "})
        result = SessionHistoryValidator.validate(corrupted)
        assert not result.is_valid
        assert any("SH-07" in v for v in result.violations)

    def test_violates_sh08_when_created_at_naive(self) -> None:
        history = make_session_history()
        naive_dt = datetime(2026, 7, 3, 0, 0, 0)
        corrupted = history.model_copy(update={"created_at": naive_dt})
        result = SessionHistoryValidator.validate(corrupted)
        assert not result.is_valid
        assert any("SH-08" in v for v in result.violations)

    def test_violates_sh09_when_transcript_unordered(self) -> None:
        history = make_session_history()
        unordered = (
            TranscriptEntry(
                question_index=5,
                question_id="q-x",
                question_prompt="p",
                answer_content="a",
                answer_attempt=1,
            ),
            TranscriptEntry(
                question_index=0,
                question_id="q-y",
                question_prompt="p",
                answer_content="a",
                answer_attempt=1,
            ),
        )
        corrupted = history.model_copy(update={"transcript": unordered})
        result = SessionHistoryValidator.validate(corrupted)
        assert not result.is_valid
        assert any("SH-09" in v for v in result.violations)

    def test_violates_sh10_when_timeline_unordered(self) -> None:
        history = make_session_history()
        unordered = (
            QuestionTimelineEntry(
                question_index=3,
                question_id="q-x",
                question_type="written",
                question_difficulty="easy",
            ),
            QuestionTimelineEntry(
                question_index=1,
                question_id="q-y",
                question_type="written",
                question_difficulty="medium",
            ),
        )
        corrupted = history.model_copy(update={"question_timeline": unordered})
        result = SessionHistoryValidator.validate(corrupted)
        assert not result.is_valid
        assert any("SH-10" in v for v in result.violations)

    def test_multiple_violations_accumulate(self) -> None:
        history = make_session_history()
        corrupted = history.model_copy(
            update={
                "schema_version": "   ",
                "created_at": datetime(2026, 7, 3, 0, 0, 0),
            }
        )
        result = SessionHistoryValidator.validate(corrupted)
        assert not result.is_valid
        assert len(result.violations) >= 2


# ---------------------------------------------------------------------------
# SUMMARY — Derived view
# ---------------------------------------------------------------------------


class TestSessionHistorySummary:
    def test_summary_from_history(self, session_history: SessionHistory) -> None:
        summary = SessionHistorySummary.from_history(session_history)
        assert summary.session_id == session_history.session_id
        assert summary.candidate_identity_id == session_history.candidate_identity_id
        assert summary.interview_index == session_history.interview_index
        assert summary.question_count == session_history.question_count
        assert summary.knowledge_epoch == "1"
        assert summary.is_replay_ready is True
        assert summary.has_evaluation is False

    def test_summary_is_frozen(self, session_history: SessionHistory) -> None:
        summary = SessionHistorySummary.from_history(session_history)
        with pytest.raises(Exception):
            summary.session_id = "mutated"  # type: ignore[misc]

    def test_summary_mean_feature_confidence_in_range(
        self, session_history: SessionHistory
    ) -> None:
        summary = SessionHistorySummary.from_history(session_history)
        assert 0.0 <= summary.mean_feature_confidence <= 1.0

    def test_summary_role_from_interview_metadata(
        self, session_history: SessionHistory
    ) -> None:
        summary = SessionHistorySummary.from_history(session_history)
        assert summary.role == session_history.interview_metadata.role


# ---------------------------------------------------------------------------
# STATISTICS — Derived metrics
# ---------------------------------------------------------------------------


class TestSessionHistoryStatistics:
    def test_statistics_from_history(self, session_history: SessionHistory) -> None:
        stats = SessionHistoryStatistics.from_history(session_history)
        assert stats.session_id == session_history.session_id
        assert stats.candidate_identity_id == session_history.candidate_identity_id
        assert stats.interview_index == session_history.interview_index
        assert stats.question_count == session_history.question_count
        assert stats.timeline_entry_count == len(session_history.question_timeline)

    def test_statistics_is_frozen(self, session_history: SessionHistory) -> None:
        stats = SessionHistoryStatistics.from_history(session_history)
        with pytest.raises(Exception):
            stats.session_id = "mutated"  # type: ignore[misc]

    def test_statistics_confidence_values_in_range(
        self, session_history: SessionHistory
    ) -> None:
        stats = SessionHistoryStatistics.from_history(session_history)
        assert 0.0 <= stats.mean_feature_confidence <= 1.0
        assert 0.0 <= stats.mean_objective_confidence <= 1.0
        assert 0.0 <= stats.mean_insight_confidence <= 1.0

    def test_statistics_knowledge_epoch_preserved(
        self, session_history: SessionHistory
    ) -> None:
        stats = SessionHistoryStatistics.from_history(session_history)
        assert stats.knowledge_epoch == "1"

    def test_statistics_schema_versions_preserved(
        self, session_history: SessionHistory
    ) -> None:
        stats = SessionHistoryStatistics.from_history(session_history)
        assert stats.profile_schema_version == "1.0"
        assert stats.narrative_schema_version == "1.0"
        assert stats.coaching_schema_version == "1.0"


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------


class TestSessionHistoryDeterminism:
    def test_two_builds_with_same_inputs_have_same_key_fields(self) -> None:
        """CoachingSnapshot uses identity equality (no __eq__); verify key fields match."""
        h1 = make_session_history()
        h2 = make_session_history()
        assert h1.session_id == h2.session_id
        assert h1.candidate_identity_id == h2.candidate_identity_id
        assert h1.interview_index == h2.interview_index
        assert h1.knowledge_snapshot.snapshot_id == h2.knowledge_snapshot.snapshot_id
        assert h1.created_at == h2.created_at
        assert h1.schema_version == h2.schema_version
        assert h1.question_count == h2.question_count

    def test_summary_is_deterministic(self) -> None:
        h1 = make_session_history()
        h2 = make_session_history()
        s1 = SessionHistorySummary.from_history(h1)
        s2 = SessionHistorySummary.from_history(h2)
        assert s1 == s2

    def test_statistics_key_fields_are_deterministic(self) -> None:
        h1 = make_session_history()
        h2 = make_session_history()
        st1 = SessionHistoryStatistics.from_history(h1)
        st2 = SessionHistoryStatistics.from_history(h2)
        assert st1.session_id == st2.session_id
        assert st1.total_features == st2.total_features
        assert st1.knowledge_epoch == st2.knowledge_epoch
        assert st1.mean_feature_confidence == st2.mean_feature_confidence

    def test_validation_is_deterministic(self) -> None:
        h1 = make_session_history()
        h2 = make_session_history()
        r1 = SessionHistoryValidator.validate(h1)
        r2 = SessionHistoryValidator.validate(h2)
        assert r1 == r2

    def test_different_interview_indices_produce_different_index(self) -> None:
        h1 = make_session_history(interview_index=0)
        h2 = make_session_history(interview_index=1)
        assert h1.interview_index != h2.interview_index


# ---------------------------------------------------------------------------
# INTEGRATION — Cross-aggregate consistency
# ---------------------------------------------------------------------------


class TestSessionHistoryIntegration:
    def test_history_candidate_id_propagates_to_snapshot(
        self, session_history: SessionHistory
    ) -> None:
        assert (
            session_history.knowledge_snapshot.candidate_identity_id
            == session_history.candidate_identity_id
        )

    def test_history_session_id_propagates_to_snapshot(
        self, session_history: SessionHistory
    ) -> None:
        assert (
            session_history.knowledge_snapshot.session_id
            == session_history.session_id
        )

    def test_history_session_id_propagates_to_language_profile(
        self, session_history: SessionHistory
    ) -> None:
        assert (
            session_history.language_profile.session_id
            == session_history.session_id
        )

    def test_summary_and_statistics_total_features_agree(
        self, session_history: SessionHistory
    ) -> None:
        summary = SessionHistorySummary.from_history(session_history)
        stats = SessionHistoryStatistics.from_history(session_history)
        assert summary.total_features == stats.total_features

    def test_summary_and_statistics_knowledge_epoch_agree(
        self, session_history: SessionHistory
    ) -> None:
        summary = SessionHistorySummary.from_history(session_history)
        stats = SessionHistoryStatistics.from_history(session_history)
        assert summary.knowledge_epoch == stats.knowledge_epoch

    def test_schema_version_preserved_in_statistics(
        self, session_history: SessionHistory
    ) -> None:
        stats = SessionHistoryStatistics.from_history(session_history)
        assert stats.schema_version == session_history.schema_version

    def test_replay_ready_propagates_through_summary_and_statistics(
        self, session_history: SessionHistory
    ) -> None:
        summary = SessionHistorySummary.from_history(session_history)
        stats = SessionHistoryStatistics.from_history(session_history)
        assert summary.is_replay_ready == stats.is_replay_ready


# ---------------------------------------------------------------------------
# ARCHITECTURE — Import guards (AST-based)
# ---------------------------------------------------------------------------

SESSION_HISTORY_MODULE_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "domain" / "contracts" / "session_history"
)

FORBIDDEN_IMPORTS_IN_SESSION_HISTORY = [
    "openai",
    "anthropic",
    "langchain",
    "langgraph",
    "sqlite",
    "sqlalchemy",
    "infrastructure",
    "services",
]


def _collect_imports(source: str) -> list[str]:
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


class TestSessionHistoryArchitecture:
    def test_no_forbidden_imports_in_session_history_layer(self) -> None:
        py_files = list(SESSION_HISTORY_MODULE_DIR.glob("*.py"))
        assert len(py_files) > 0, "No Python files found in session_history module"

        violations: list[str] = []
        for path in py_files:
            source = path.read_text()
            imports = _collect_imports(source)
            for imp in imports:
                for forbidden in FORBIDDEN_IMPORTS_IN_SESSION_HISTORY:
                    if forbidden in imp.lower():
                        violations.append(f"{path.name}: imports '{imp}'")

        assert violations == [], (
            "SessionHistory layer must not import forbidden modules:\n"
            + "\n".join(violations)
        )

    def test_session_history_has_no_direct_storage_references(self) -> None:
        for path in SESSION_HISTORY_MODULE_DIR.glob("*.py"):
            source = path.read_text()
            assert "sqlite" not in source.lower(), f"{path.name} references sqlite"
            assert "repository" not in source.lower(), f"{path.name} references repository"
            assert "database" not in source.lower(), f"{path.name} references database"

    def test_session_history_model_is_immutable(self) -> None:
        history = make_session_history()
        config = history.model_config
        assert config.get("frozen") is True

    def test_no_live_runtime_imports_in_session_history(self) -> None:
        for path in SESSION_HISTORY_MODULE_DIR.glob("*.py"):
            source = path.read_text()
            imports = _collect_imports(source)
            for imp in imports:
                assert "observation_store" not in imp.lower(), (
                    f"{path.name} must not import ObservationStore: {imp}"
                )
                assert "feature_engine" not in imp.lower(), (
                    f"{path.name} must not import FeatureEngine: {imp}"
                )

    def test_session_history_init_exports_all_public_types(self) -> None:
        from domain.contracts.session_history import __all__
        expected = {
            "SessionHistory",
            "SessionHistoryBuilder",
            "SessionHistoryStatistics",
            "SessionHistorySummary",
            "SessionHistoryValidator",
            "SessionHistoryValidationResult",
            "InterviewMetadata",
            "TranscriptEntry",
            "QuestionTimelineEntry",
            "ReplayMetadata",
        }
        assert expected.issubset(set(__all__))
