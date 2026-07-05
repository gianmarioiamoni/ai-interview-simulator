# tests/domain/contracts/progress/test_learning_progress_contracts.py
# Contract, validation, architecture, integration, and determinism tests for LearningProgress

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.identity.candidate_identity import CandidateIdentity
from domain.contracts.progress.learning_progress import (
    DimensionalScore,
    LearningProgress,
    SessionProgressEntry,
)
from domain.contracts.progress.learning_progress_builder import LearningProgressBuilder
from domain.contracts.progress.learning_progress_statistics import (
    DimensionalTrend,
    LearningProgressStatistics,
)
from domain.contracts.progress.learning_progress_summary import LearningProgressSummary
from domain.contracts.progress.learning_progress_validator import (
    LearningProgressValidationResult,
    LearningProgressValidator,
)
from domain.contracts.progress.progress_comparison import DimensionalDelta, ProgressComparison
from tests.domain.contracts.progress.conftest import (
    CANDIDATE_ID,
    CANDIDATE_ID_B,
    SESSION_ID,
    SESSION_ID_B,
    FIXED_COMPUTED_AT,
    make_history,
    make_learning_progress,
    make_two_histories,
)


# ===========================================================================
# CONTRACT TESTS — CandidateIdentity
# ===========================================================================

class TestCandidateIdentityContract:
    def test_candidate_identity_uses_existing_contract_field(self) -> None:
        """CandidateIdentity exposes candidate_identity_id — no duplicate model."""
        identity = CandidateIdentity(
            candidate_identity_id=CANDIDATE_ID,
            created_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
        assert identity.candidate_identity_id == CANDIDATE_ID
        assert identity.id == CANDIDATE_ID

    def test_candidate_identity_is_immutable(self) -> None:
        identity = CandidateIdentity(
            candidate_identity_id=CANDIDATE_ID,
            created_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(Exception):
            identity.candidate_identity_id = "other"  # type: ignore[misc]

    def test_candidate_identity_optional_display_name(self) -> None:
        identity = CandidateIdentity(
            candidate_identity_id=CANDIDATE_ID,
            created_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
            display_name="Alice",
        )
        assert identity.display_name == "Alice"

    def test_no_duplicate_candidate_identity_in_session_history(self) -> None:
        """SessionHistory already carries candidate_identity_id — no separate model needed."""
        history = make_history()
        assert history.candidate_identity_id == CANDIDATE_ID


# ===========================================================================
# CONTRACT TESTS — LearningProgress
# ===========================================================================

class TestLearningProgressContract:
    def test_progress_is_immutable(self, learning_progress: LearningProgress) -> None:
        with pytest.raises(Exception):
            learning_progress.candidate_identity_id = "other"  # type: ignore[misc]

    def test_session_count(self, learning_progress: LearningProgress) -> None:
        assert learning_progress.session_count == 2

    def test_is_not_empty(self, learning_progress: LearningProgress) -> None:
        assert not learning_progress.is_empty

    def test_empty_progress(self, empty_progress: LearningProgress) -> None:
        assert empty_progress.is_empty
        assert empty_progress.session_count == 0
        assert empty_progress.latest_entry is None
        assert empty_progress.earliest_entry is None

    def test_entries_ordered_by_session_index(self, learning_progress: LearningProgress) -> None:
        indices = [e.session_index for e in learning_progress.session_entries]
        assert indices == sorted(indices)

    def test_total_questions_answered(self, learning_progress: LearningProgress) -> None:
        total = sum(e.question_count for e in learning_progress.session_entries)
        assert learning_progress.total_questions_answered == total

    def test_latest_entry_is_highest_index(self, learning_progress: LearningProgress) -> None:
        assert learning_progress.latest_entry is not None
        assert learning_progress.latest_entry.session_index == 1

    def test_earliest_entry_is_lowest_index(self, learning_progress: LearningProgress) -> None:
        assert learning_progress.earliest_entry is not None
        assert learning_progress.earliest_entry.session_index == 0

    def test_candidate_identity_id_propagated(self, learning_progress: LearningProgress) -> None:
        assert learning_progress.candidate_identity_id == CANDIDATE_ID


# ===========================================================================
# CONTRACT TESTS — SessionProgressEntry
# ===========================================================================

class TestSessionProgressEntryContract:
    def test_entry_is_immutable(self, learning_progress: LearningProgress) -> None:
        entry = learning_progress.session_entries[0]
        with pytest.raises(Exception):
            entry.session_id = "x"  # type: ignore[misc]

    def test_entry_carries_role_seniority(self, learning_progress: LearningProgress) -> None:
        entry = learning_progress.session_entries[0]
        assert entry.role == "backend_engineer"
        assert entry.seniority == "Senior"

    def test_entry_dimensional_scores_not_empty(self, learning_progress: LearningProgress) -> None:
        entry = learning_progress.session_entries[0]
        assert len(entry.dimensional_scores) > 0

    def test_dimensional_score_is_immutable(self, learning_progress: LearningProgress) -> None:
        score = learning_progress.session_entries[0].dimensional_scores[0]
        with pytest.raises(Exception):
            score.feature_type_id = "x"  # type: ignore[misc]


# ===========================================================================
# BUILDER TESTS
# ===========================================================================

class TestLearningProgressBuilder:
    def test_builder_is_sole_creation_path(self) -> None:
        """LearningProgress must be created via builder, not direct construction."""
        histories = make_two_histories()
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories(histories)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        assert progress.candidate_identity_id == CANDIDATE_ID

    def test_builder_raises_without_candidate_id(self) -> None:
        with pytest.raises(ValueError, match="candidate_identity_id"):
            LearningProgressBuilder().with_session_histories([]).build()

    def test_builder_raises_on_foreign_session_history(self) -> None:
        history_foreign = make_history(candidate_id=CANDIDATE_ID_B)
        with pytest.raises(ValueError, match=CANDIDATE_ID_B):
            (
                LearningProgressBuilder()
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_session_histories([history_foreign])
                .build()
            )

    def test_builder_sorts_by_interview_index(self) -> None:
        h0 = make_history(session_id=SESSION_ID, interview_index=0)
        h1 = make_history(session_id=SESSION_ID_B, interview_index=1)
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories([h1, h0])  # reversed input
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        assert progress.session_entries[0].session_index == 0
        assert progress.session_entries[1].session_index == 1

    def test_builder_never_modifies_session_history(self) -> None:
        histories = make_two_histories()
        original_ids = [h.session_id for h in histories]
        _ = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories(histories)
            .build()
        )
        assert [h.session_id for h in histories] == original_ids

    def test_builder_empty_histories_allowed(self) -> None:
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories([])
            .build()
        )
        assert progress.is_empty

    def test_computed_at_defaults_to_now_utc(self) -> None:
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories([])
            .build()
        )
        assert progress.computed_at.tzinfo is not None


# ===========================================================================
# VALIDATION TESTS
# ===========================================================================

class TestLearningProgressValidator:
    def test_valid_progress_passes(self, learning_progress: LearningProgress) -> None:
        result = LearningProgressValidator.validate(learning_progress)
        assert result.is_valid
        assert result.violations == ()

    def test_empty_progress_passes(self, empty_progress: LearningProgress) -> None:
        result = LearningProgressValidator.validate(empty_progress)
        assert result.is_valid

    def test_blank_candidate_id_fails(self) -> None:
        progress = LearningProgress(
            candidate_identity_id="  ",
            computed_at=FIXED_COMPUTED_AT,
            session_entries=(),
        )
        result = LearningProgressValidator.validate(progress)
        assert not result.is_valid
        assert any("LP-01" in v for v in result.violations)

    def test_naive_computed_at_fails(self) -> None:
        progress = LearningProgress(
            candidate_identity_id=CANDIDATE_ID,
            computed_at=datetime(2026, 7, 3),  # no tzinfo
            session_entries=(),
        )
        result = LearningProgressValidator.validate(progress)
        assert not result.is_valid
        assert any("LP-07" in v for v in result.violations)

    def test_unordered_entries_fails(self) -> None:
        e0 = _make_entry(session_id="s0", session_index=0)
        e1 = _make_entry(session_id="s1", session_index=1)
        progress = LearningProgress(
            candidate_identity_id=CANDIDATE_ID,
            computed_at=FIXED_COMPUTED_AT,
            session_entries=(e1, e0),  # wrong order
        )
        result = LearningProgressValidator.validate(progress)
        assert not result.is_valid
        assert any("LP-03" in v for v in result.violations)

    def test_duplicate_session_id_fails(self) -> None:
        e0 = _make_entry(session_id="same", session_index=0)
        e1 = _make_entry(session_id="same", session_index=1)
        progress = LearningProgress(
            candidate_identity_id=CANDIDATE_ID,
            computed_at=FIXED_COMPUTED_AT,
            session_entries=(e0, e1),
        )
        result = LearningProgressValidator.validate(progress)
        assert not result.is_valid
        assert any("LP-04" in v for v in result.violations)

    def test_duplicate_session_index_fails(self) -> None:
        e0 = _make_entry(session_id="s0", session_index=0)
        e1 = _make_entry(session_id="s1", session_index=0)  # duplicate index
        progress = LearningProgress(
            candidate_identity_id=CANDIDATE_ID,
            computed_at=FIXED_COMPUTED_AT,
            session_entries=(e0, e1),
        )
        result = LearningProgressValidator.validate(progress)
        assert not result.is_valid
        assert any("LP-05" in v for v in result.violations)

    def test_validation_result_ok(self) -> None:
        result = LearningProgressValidationResult.ok()
        assert result.is_valid
        assert result.violations == ()

    def test_validation_result_failed(self) -> None:
        result = LearningProgressValidationResult.failed(["LP-01: x", "LP-07: y"])
        assert not result.is_valid
        assert len(result.violations) == 2


# ===========================================================================
# STATISTICS TESTS
# ===========================================================================

class TestLearningProgressStatistics:
    def test_statistics_from_non_empty_progress(self, learning_progress: LearningProgress) -> None:
        stats = LearningProgressStatistics.from_progress(learning_progress)
        assert stats.session_count == 2
        assert stats.total_questions_answered == learning_progress.total_questions_answered
        assert not stats.is_empty
        assert stats.candidate_identity_id == CANDIDATE_ID

    def test_statistics_from_empty_progress(self, empty_progress: LearningProgress) -> None:
        stats = LearningProgressStatistics.from_progress(empty_progress)
        assert stats.is_empty
        assert stats.session_count == 0
        assert stats.dimensional_trends == ()

    def test_statistics_confidence_delta(self, learning_progress: LearningProgress) -> None:
        stats = LearningProgressStatistics.from_progress(learning_progress)
        delta = stats.mean_confidence_last_session - stats.mean_confidence_first_session
        assert abs(stats.overall_confidence_delta - delta) < 1e-9

    def test_statistics_dimensional_trends_are_immutable(
        self, learning_progress: LearningProgress
    ) -> None:
        stats = LearningProgressStatistics.from_progress(learning_progress)
        with pytest.raises(Exception):
            stats.dimensional_trends = ()  # type: ignore[misc]

    def test_dimensional_trend_fields(self, learning_progress: LearningProgress) -> None:
        stats = LearningProgressStatistics.from_progress(learning_progress)
        for trend in stats.dimensional_trends:
            assert trend.feature_type_id
            assert trend.semantic_category
            assert 0.0 <= trend.first_confidence <= 1.0
            assert 0.0 <= trend.last_confidence <= 1.0
            assert isinstance(trend.is_improving, bool)
            assert isinstance(trend.is_regressing, bool)
            assert isinstance(trend.is_stable, bool)


# ===========================================================================
# SUMMARY TESTS
# ===========================================================================

class TestLearningProgressSummary:
    def test_summary_from_progress(self, learning_progress: LearningProgress) -> None:
        summary = LearningProgressSummary.from_progress(learning_progress)
        assert summary.candidate_identity_id == CANDIDATE_ID
        assert summary.session_count == 2
        assert summary.computed_at == FIXED_COMPUTED_AT

    def test_summary_is_immutable(self, learning_progress: LearningProgress) -> None:
        summary = LearningProgressSummary.from_progress(learning_progress)
        with pytest.raises(Exception):
            summary.session_count = 99  # type: ignore[misc]

    def test_summary_empty_progress(self, empty_progress: LearningProgress) -> None:
        summary = LearningProgressSummary.from_progress(empty_progress)
        assert summary.is_empty
        assert summary.earliest_session_id is None
        assert summary.latest_session_id is None

    def test_summary_session_ids(self, learning_progress: LearningProgress) -> None:
        summary = LearningProgressSummary.from_progress(learning_progress)
        assert summary.earliest_session_id == SESSION_ID
        assert summary.latest_session_id == SESSION_ID_B


# ===========================================================================
# PROGRESS COMPARISON TESTS
# ===========================================================================

class TestProgressComparison:
    def test_compare_two_entries(self, learning_progress: LearningProgress) -> None:
        comparison = ProgressComparison.between_sessions(
            learning_progress, before_index=0, after_index=1
        )
        assert comparison is not None
        assert comparison.session_before_id == SESSION_ID
        assert comparison.session_after_id == SESSION_ID_B
        assert comparison.candidate_identity_id == CANDIDATE_ID

    def test_compare_returns_none_for_missing_index(
        self, learning_progress: LearningProgress
    ) -> None:
        result = ProgressComparison.between_sessions(
            learning_progress, before_index=0, after_index=99
        )
        assert result is None

    def test_comparison_is_immutable(self, learning_progress: LearningProgress) -> None:
        comparison = ProgressComparison.between_sessions(
            learning_progress, before_index=0, after_index=1
        )
        assert comparison is not None
        with pytest.raises(Exception):
            comparison.candidate_identity_id = "x"  # type: ignore[misc]

    def test_comparison_overall_delta(self, learning_progress: LearningProgress) -> None:
        comparison = ProgressComparison.between_sessions(
            learning_progress, before_index=0, after_index=1
        )
        assert comparison is not None
        expected = comparison.mean_confidence_after - comparison.mean_confidence_before
        assert abs(comparison.overall_delta - expected) < 1e-9

    def test_comparison_direction_values(self, learning_progress: LearningProgress) -> None:
        comparison = ProgressComparison.between_sessions(
            learning_progress, before_index=0, after_index=1
        )
        assert comparison is not None
        assert comparison.overall_direction in ("improving", "regressing", "stable")
        for delta in comparison.dimensional_deltas:
            assert delta.direction in ("improving", "regressing", "stable")

    def test_comparison_new_and_dropped_dimensions(self) -> None:
        entry_before = SessionProgressEntry(
            session_id="s0",
            session_index=0,
            created_at=FIXED_COMPUTED_AT,
            role="SWE",
            seniority="Mid",
            interview_type="technical",
            question_count=3,
            knowledge_epoch="1",
            dimensional_scores=(
                DimensionalScore(
                    feature_type_id="reasoning_feature",
                    semantic_category="analytical_reasoning",
                    confidence=0.6,
                    session_index=0,
                ),
            ),
        )
        entry_after = SessionProgressEntry(
            session_id="s1",
            session_index=1,
            created_at=FIXED_COMPUTED_AT,
            role="SWE",
            seniority="Mid",
            interview_type="technical",
            question_count=3,
            knowledge_epoch="1",
            dimensional_scores=(
                DimensionalScore(
                    feature_type_id="technical_skill_feature",
                    semantic_category="technical_knowledge",
                    confidence=0.7,
                    session_index=1,
                ),
            ),
        )
        comparison = ProgressComparison.compare(CANDIDATE_ID, entry_before, entry_after)
        assert "technical_skill_feature" in comparison.new_dimensions
        assert "reasoning_feature" in comparison.dropped_dimensions


# ===========================================================================
# ARCHITECTURE / DERIVATION TESTS
# ===========================================================================

class TestArchitectureInvariants:
    def test_progress_never_persisted_marker(self, learning_progress: LearningProgress) -> None:
        """LearningProgress has no persistence ID — it is derived-only."""
        assert not hasattr(learning_progress, "progress_id")

    def test_progress_derived_from_session_history_exclusively(self) -> None:
        """Progress entries only carry fields derivable from SessionHistory."""
        h = make_history()
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories([h])
            .build()
        )
        entry = progress.session_entries[0]
        assert entry.session_id == h.session_id
        assert entry.session_index == h.interview_index
        assert entry.role == h.interview_metadata.role

    def test_progress_does_not_modify_session_history(self) -> None:
        h = make_history()
        original_session_id = h.session_id
        _ = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories([h])
            .build()
        )
        assert h.session_id == original_session_id

    def test_no_duplicate_identity_model_used(self) -> None:
        """Only CandidateIdentity from domain/contracts/identity is used; no duplicate."""
        from domain.contracts.identity.candidate_identity import CandidateIdentity
        identity = CandidateIdentity(
            candidate_identity_id=CANDIDATE_ID,
            created_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
        h = make_history()
        assert h.candidate_identity_id == identity.candidate_identity_id

    def test_learning_progress_schema_version_present(
        self, learning_progress: LearningProgress
    ) -> None:
        assert learning_progress.schema_version == "1.0"

    def test_knowledge_epoch_carried(self, learning_progress: LearningProgress) -> None:
        assert learning_progress.knowledge_epoch == "1"


# ===========================================================================
# DETERMINISM TESTS
# ===========================================================================

class TestDeterminism:
    def test_same_histories_produce_same_session_count(self) -> None:
        histories = make_two_histories()
        p1 = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories(histories)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        p2 = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories(histories)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        assert p1.session_count == p2.session_count

    def test_same_histories_produce_same_dimensional_scores(self) -> None:
        histories = make_two_histories()
        p1 = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories(histories)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        p2 = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories(histories)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        for e1, e2 in zip(p1.session_entries, p2.session_entries):
            assert e1.mean_confidence == e2.mean_confidence
            assert len(e1.dimensional_scores) == len(e2.dimensional_scores)

    def test_statistics_are_deterministic(self) -> None:
        progress = make_learning_progress()
        stats1 = LearningProgressStatistics.from_progress(progress)
        stats2 = LearningProgressStatistics.from_progress(progress)
        assert stats1.overall_confidence_delta == stats2.overall_confidence_delta
        assert stats1.session_count == stats2.session_count

    def test_comparison_is_deterministic(self, learning_progress: LearningProgress) -> None:
        c1 = ProgressComparison.between_sessions(learning_progress, 0, 1)
        c2 = ProgressComparison.between_sessions(learning_progress, 0, 1)
        assert c1 is not None and c2 is not None
        assert c1.overall_delta == c2.overall_delta
        assert c1.overall_direction == c2.overall_direction


# ===========================================================================
# INTEGRATION TESTS
# ===========================================================================

class TestIntegration:
    def test_full_pipeline_single_session(self) -> None:
        h = make_history()
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories([h])
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        assert LearningProgressValidator.validate(progress).is_valid
        stats = LearningProgressStatistics.from_progress(progress)
        assert stats.session_count == 1
        summary = LearningProgressSummary.from_progress(progress)
        assert summary.session_count == 1

    def test_full_pipeline_two_sessions(
        self, learning_progress: LearningProgress
    ) -> None:
        assert LearningProgressValidator.validate(learning_progress).is_valid
        stats = LearningProgressStatistics.from_progress(learning_progress)
        assert stats.session_count == 2
        summary = LearningProgressSummary.from_progress(learning_progress)
        assert summary.session_count == 2
        comparison = ProgressComparison.between_sessions(learning_progress, 0, 1)
        assert comparison is not None

    def test_validator_after_builder(self) -> None:
        histories = make_two_histories()
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_session_histories(histories)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        result = LearningProgressValidator.validate(progress)
        assert result.is_valid, result.violations


# ===========================================================================
# Helpers
# ===========================================================================

def _make_entry(session_id: str, session_index: int) -> SessionProgressEntry:
    return SessionProgressEntry(
        session_id=session_id,
        session_index=session_index,
        created_at=FIXED_COMPUTED_AT,
        role="SWE",
        seniority="Mid",
        interview_type="technical",
        question_count=3,
        knowledge_epoch="1",
    )
