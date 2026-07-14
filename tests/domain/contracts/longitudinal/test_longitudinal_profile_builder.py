# tests/domain/contracts/longitudinal/test_longitudinal_profile_builder.py
# P1/C2 unit tests — LongitudinalProfileBuilder
# Covers: first-session path, n-session accumulation, idempotency (LP-07),
#         identity mismatch rejection, language capability aggregation,
#         trend direction computation, missing required fields, immutability of output.

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.longitudinal.longitudinal_profile import (
    CrossSessionLanguageCapability,
    LongitudinalProfile,
)
from domain.contracts.longitudinal.longitudinal_profile_builder import LongitudinalProfileBuilder
from domain.contracts.session_history.session_history import SessionHistory
from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    FIXED_DT,
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    make_session_history,
    make_interview_metadata,
    make_language_profile,
    make_transcript,
    make_question_timeline,
)
from domain.contracts.session_history.session_history import ReplayMetadata
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder

FIXED_TS = datetime(2026, 7, 14, 0, 0, 0, tzinfo=timezone.utc)
LATER_TS = datetime(2026, 7, 14, 1, 0, 0, tzinfo=timezone.utc)
EVEN_LATER_TS = datetime(2026, 7, 14, 2, 0, 0, tzinfo=timezone.utc)


def make_sh(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
    interview_index: int = 0,
) -> SessionHistory:
    return make_session_history(
        session_id=session_id,
        candidate_id=candidate_id,
        interview_index=interview_index,
    )


def make_sh_for_candidate(candidate_id: str, interview_index: int = 0) -> SessionHistory:
    snapshot = make_knowledge_snapshot(session_id=f"sess-{candidate_id}", candidate_id=candidate_id)
    return (
        SessionHistoryBuilder()
        .with_session_id(f"sess-{candidate_id}")
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(interview_index)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=f"sess-{candidate_id}"))
        .with_transcript(make_transcript())
        .with_question_timeline(make_question_timeline())
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_TS)
        .build()
    )


def python_cap(composite: float = 0.7) -> LanguageCapability:
    return LanguageCapability(
        language_id="python",
        questions_answered_in_language=3,
        composite_score=composite,
        idiomatic_usage_score=0.75,
        type_error_rate=0.1,
    )


def typescript_cap(composite: float = 0.6) -> LanguageCapability:
    return LanguageCapability(
        language_id="typescript",
        questions_answered_in_language=2,
        composite_score=composite,
        idiomatic_usage_score=0.65,
        type_error_rate=0.15,
    )


# ===========================================================================
# Missing required fields
# ===========================================================================


class TestBuilderMissingFields:

    def test_missing_session_history_raises(self) -> None:
        with pytest.raises(ValueError, match="session_history"):
            LongitudinalProfileBuilder().with_current_timestamp(FIXED_TS).build()

    def test_missing_current_timestamp_raises(self) -> None:
        with pytest.raises(ValueError, match="current_timestamp"):
            LongitudinalProfileBuilder().with_session_history(make_sh()).build()

    def test_missing_both_required_raises(self) -> None:
        with pytest.raises(ValueError):
            LongitudinalProfileBuilder().build()


# ===========================================================================
# First-session path
# ===========================================================================


class TestFirstSessionPath:

    def test_first_session_produces_valid_profile(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(None)
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert isinstance(profile, LongitudinalProfile)
        assert profile.session_count == 1
        assert profile.schema_version == "1.0"

    def test_first_session_sets_candidate_identity(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert profile.candidate_identity_id == CANDIDATE_ID

    def test_first_session_creates_at_equals_timestamp(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert profile.created_at == FIXED_TS
        assert profile.last_updated_at == FIXED_TS

    def test_first_session_knowledge_epoch(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert profile.knowledge_epoch == sh.knowledge_epoch

    def test_first_session_session_entry_fields(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        entry = profile.session_snapshots[0]
        assert entry.session_id == sh.session_id
        assert entry.interview_index == sh.interview_index
        assert entry.contributed_at == FIXED_TS

    def test_first_session_metadata_fields_mapped(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        meta = profile.session_snapshots[0].session_metadata
        assert meta.role == sh.interview_metadata.role
        assert meta.seniority == sh.interview_metadata.seniority
        assert meta.interview_type == sh.interview_metadata.interview_type
        assert meta.question_count == sh.interview_metadata.question_count
        assert meta.session_language == sh.interview_metadata.session_language
        assert meta.knowledge_epoch == sh.knowledge_epoch

    def test_first_session_empty_language_summary(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert profile.language_capability_summary == ()

    def test_first_session_profile_snapshot_embedded(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert profile.session_snapshots[0].profile_snapshot == sh.knowledge_snapshot.profile_snapshot

    def test_output_is_immutable(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        from pydantic import ValidationError
        with pytest.raises((TypeError, ValidationError)):
            profile.candidate_identity_id = "changed"  # type: ignore[misc]


# ===========================================================================
# N-session accumulation path
# ===========================================================================


class TestNSessionPath:

    def _build_first(self) -> LongitudinalProfile:
        sh = make_sh(interview_index=0)
        return (
            LongitudinalProfileBuilder()
            .with_prior_profile(None)
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )

    def test_second_session_increments_count(self) -> None:
        prior = self._build_first()
        sh2 = make_sh(session_id="sess-002", interview_index=1)
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(sh2)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert profile.session_count == 2

    def test_second_session_preserves_created_at(self) -> None:
        prior = self._build_first()
        sh2 = make_sh(session_id="sess-002", interview_index=1)
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(sh2)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert profile.created_at == FIXED_TS
        assert profile.last_updated_at == LATER_TS

    def test_second_session_updates_knowledge_epoch(self) -> None:
        prior = self._build_first()
        sh2 = make_sh(session_id="sess-002", interview_index=1)
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(sh2)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert profile.knowledge_epoch == sh2.knowledge_epoch

    def test_snapshots_ordered_ascending(self) -> None:
        prior = self._build_first()
        sh2 = make_sh(session_id="sess-002", interview_index=1)
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(sh2)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        indices = [e.interview_index for e in profile.session_snapshots]
        assert indices == sorted(indices)

    def test_three_session_accumulation(self) -> None:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        p2 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        sh2 = make_sh(session_id="sess-002", interview_index=2)
        p3 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p2)
            .with_session_history(sh2)
            .with_current_timestamp(EVEN_LATER_TS)
            .build()
        )
        assert p3.session_count == 3
        assert [e.interview_index for e in p3.session_snapshots] == [0, 1, 2]

    def test_lp_v01_invariant_satisfied(self) -> None:
        prior = self._build_first()
        sh2 = make_sh(session_id="sess-002", interview_index=1)
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(sh2)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert profile.session_count == len(profile.session_snapshots)


# ===========================================================================
# Idempotency guard (LP-07)
# ===========================================================================


class TestIdempotencyGuard:

    def test_duplicate_interview_index_returns_prior_unchanged(self) -> None:
        sh = make_sh(interview_index=0)
        prior = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        # Same interview_index — should be a no-op.
        result = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(sh)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert result is prior

    def test_duplicate_different_session_id_same_index_is_noop(self) -> None:
        sh0 = make_sh(session_id="sess-a", interview_index=0)
        prior = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh0_alt = make_sh(session_id="sess-b", interview_index=0)
        result = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(sh0_alt)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert result is prior
        assert result.session_count == 1


# ===========================================================================
# Identity mismatch rejection (LP-05)
# ===========================================================================


class TestIdentityMismatch:

    def test_candidate_mismatch_raises_value_error(self) -> None:
        sh_a = make_sh_for_candidate("cand-a", interview_index=0)
        prior = (
            LongitudinalProfileBuilder()
            .with_session_history(sh_a)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh_b = make_sh_for_candidate("cand-b", interview_index=1)
        with pytest.raises(ValueError, match="Identity mismatch"):
            (
                LongitudinalProfileBuilder()
                .with_prior_profile(prior)
                .with_session_history(sh_b)
                .with_current_timestamp(LATER_TS)
                .build()
            )


# ===========================================================================
# Language capability aggregation
# ===========================================================================


class TestLanguageCapabilityAggregation:

    def test_first_session_with_language_cap_creates_summary_entry(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_language_capabilities((python_cap(0.7),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert len(profile.language_capability_summary) == 1
        lc = profile.language_capability_summary[0]
        assert lc.language_id == "python"
        assert lc.session_count_in_language == 1
        assert lc.trend_direction == "insufficient_data"

    def test_second_session_language_cap_accumulates(self) -> None:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_language_capabilities((python_cap(0.7),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        p2 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities((python_cap(0.8),))
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert len(p2.language_capability_summary) == 1
        lc = p2.language_capability_summary[0]
        assert lc.session_count_in_language == 2
        assert lc.total_questions_answered == 6

    def test_running_mean_composite_score(self) -> None:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_language_capabilities((python_cap(0.6),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        p2 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities((python_cap(0.8),))
            .with_current_timestamp(LATER_TS)
            .build()
        )
        lc = p2.language_capability_summary[0]
        assert abs(lc.mean_composite_score - 0.7) < 1e-9

    def test_no_language_caps_summary_unchanged(self) -> None:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_language_capabilities((python_cap(0.7),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        p2 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities(())
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert p2.language_capability_summary == p1.language_capability_summary

    def test_two_languages_in_one_session(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_language_capabilities((python_cap(), typescript_cap()))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        assert len(profile.language_capability_summary) == 2
        lang_ids = {lc.language_id for lc in profile.language_capability_summary}
        assert lang_ids == {"python", "typescript"}

    def test_second_session_adds_new_language(self) -> None:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_language_capabilities((python_cap(),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        p2 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities((typescript_cap(),))
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert len(p2.language_capability_summary) == 2
        py = next(lc for lc in p2.language_capability_summary if lc.language_id == "python")
        ts = next(lc for lc in p2.language_capability_summary if lc.language_id == "typescript")
        assert py.session_count_in_language == 1
        assert ts.session_count_in_language == 1

    def test_lp_v05_unique_language_ids_in_summary(self) -> None:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_language_capabilities((python_cap(),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        p2 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities((python_cap(),))
            .with_current_timestamp(LATER_TS)
            .build()
        )
        lang_ids = [lc.language_id for lc in p2.language_capability_summary]
        assert len(lang_ids) == len(set(lang_ids))


# ===========================================================================
# Trend direction computation (DC §2.6 ±0.05 threshold rule)
# ===========================================================================


class TestTrendDirectionComputation:

    def _build_two_session_profile(self, score_s1: float, score_s2: float) -> LongitudinalProfile:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_language_capabilities((python_cap(score_s1),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        return (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities((python_cap(score_s2),))
            .with_current_timestamp(LATER_TS)
            .build()
        )

    def test_single_session_is_insufficient_data(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_language_capabilities((python_cap(0.7),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        lc = profile.language_capability_summary[0]
        assert lc.trend_direction == "insufficient_data"

    def test_improving_when_delta_above_threshold(self) -> None:
        profile = self._build_two_session_profile(0.6, 0.651)
        lc = next(c for c in profile.language_capability_summary if c.language_id == "python")
        assert lc.trend_direction == "improving"

    def test_declining_when_delta_below_threshold(self) -> None:
        profile = self._build_two_session_profile(0.8, 0.749)
        lc = next(c for c in profile.language_capability_summary if c.language_id == "python")
        assert lc.trend_direction == "declining"

    def test_stable_when_within_threshold(self) -> None:
        profile = self._build_two_session_profile(0.7, 0.75)
        lc = next(c for c in profile.language_capability_summary if c.language_id == "python")
        assert lc.trend_direction == "stable"

    def test_stable_at_exact_threshold_boundary(self) -> None:
        # latest == earliest + 0.05 → stable (not > 0.05)
        profile = self._build_two_session_profile(0.6, 0.65)
        lc = next(c for c in profile.language_capability_summary if c.language_id == "python")
        assert lc.trend_direction == "stable"

    def test_improving_just_above_threshold(self) -> None:
        profile = self._build_two_session_profile(0.6, 0.651)
        lc = next(c for c in profile.language_capability_summary if c.language_id == "python")
        assert lc.trend_direction == "improving"


# ===========================================================================
# Serialization compatibility
# ===========================================================================


class TestSerializationCompatibility:

    def test_built_profile_serialization_round_trip(self) -> None:
        sh = make_sh()
        profile = (
            LongitudinalProfileBuilder()
            .with_session_history(sh)
            .with_language_capabilities((python_cap(),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        serialized = profile.model_dump_json()
        restored = LongitudinalProfile.model_validate_json(serialized)
        assert restored == profile

    def test_two_session_profile_round_trip(self) -> None:
        sh0 = make_sh(interview_index=0)
        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_language_capabilities((python_cap(0.6),))
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        sh1 = make_sh(session_id="sess-001", interview_index=1)
        p2 = (
            LongitudinalProfileBuilder()
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities((python_cap(0.75),))
            .with_current_timestamp(LATER_TS)
            .build()
        )
        serialized = p2.model_dump_json()
        restored = LongitudinalProfile.model_validate_json(serialized)
        assert restored == p2


# ===========================================================================
# Builder reuse
# ===========================================================================


class TestBuilderReuse:

    def test_builder_can_be_reused_for_different_sessions(self) -> None:
        sh0 = make_sh(session_id="sess-a", interview_index=0)
        sh1 = make_sh(session_id="sess-b", interview_index=1)

        builder = LongitudinalProfileBuilder()
        p1 = (
            builder
            .with_prior_profile(None)
            .with_session_history(sh0)
            .with_language_capabilities(())
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        p2 = (
            builder
            .with_prior_profile(p1)
            .with_session_history(sh1)
            .with_language_capabilities(())
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert p2.session_count == 2
        assert p1.session_count == 1

    def test_builder_reset_via_fluent_chain(self) -> None:
        sh0 = make_sh(interview_index=0)
        sh1 = make_sh(session_id="sess-001", interview_index=0)

        p1 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh0)
            .with_current_timestamp(FIXED_TS)
            .build()
        )
        p2 = (
            LongitudinalProfileBuilder()
            .with_session_history(sh1)
            .with_current_timestamp(LATER_TS)
            .build()
        )
        assert p1 != p2
