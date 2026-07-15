# tests/domain/contracts/progress/test_learning_progress_builder_p2_c2.py
# EPIC-02 / P2-C2 — LearningProgressBuilder migration tests
# Covers: LP-LP-01..LP-LP-07; BehavioralTrend derivation; FeatureTrend computation;
#         language_capability_summary propagation; has_sufficient_data; session ordering;
#         insufficient-data scenarios; serialization; regression compatibility.

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot
from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.longitudinal.longitudinal_profile import (
    CrossSessionLanguageCapability,
    LongitudinalProfile,
    LongitudinalSessionEntry,
    LongitudinalSessionMetadata,
)
from domain.contracts.progress.learning_progress import LearningProgress
from domain.contracts.progress.learning_progress_builder import LearningProgressBuilder

CANDIDATE_ID = "cand-p2c2-001"
CANDIDATE_ID_B = "cand-p2c2-002"
SESSION_0 = "sess-p2c2-000"
SESSION_1 = "sess-p2c2-001"
SESSION_2 = "sess-p2c2-002"
FIXED_DT = datetime(2026, 7, 15, 0, 0, 0, tzinfo=timezone.utc)
DT_1 = datetime(2026, 7, 15, 1, 0, 0, tzinfo=timezone.utc)
DT_2 = datetime(2026, 7, 15, 2, 0, 0, tzinfo=timezone.utc)
FIXED_COMPUTED_AT = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_feature(
    candidate_id: str = CANDIDATE_ID,
    feature_type: FeatureType = FeatureType.REASONING,
    confidence: float = 0.7,
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    return ProfileFeature(
        feature_identity=identity,
        value="HIGH",
        quality=FeatureQuality(
            confidence=FeatureConfidence(value=confidence),
            stability=FeatureStability(state="stable"),
            maturity=FeatureMaturity.from_observation_count(3),
        ),
        provenance=FeatureProvenance(
            feature_identity=identity,
            source_observation_ids=("obs-1",),
            computed_at_question_index=3,
            feature_engine_version="1.0",
            updater_id="updater-reasoning",
        ),
        computed_at_question_index=3,
        candidate_identity_id=candidate_id,
    )


def _make_snapshot(
    candidate_id: str = CANDIDATE_ID,
    features: tuple[ProfileFeature, ...] | None = None,
) -> CandidateProfileSnapshot:
    resolved = features if features is not None else (_make_feature(candidate_id),)
    mean_conf = (
        sum(f.quality.confidence.value for f in resolved) / len(resolved)
        if resolved else 0.0
    )
    return CandidateProfileSnapshot(
        candidate_identity_id=candidate_id,
        features=resolved,
        closed_at_question_index=5,
        source_observation_ids=("obs-1",),
        total_feature_count=len(resolved),
        mean_confidence=mean_conf,
    )


def _make_metadata(
    knowledge_epoch: str = "1",
    language_capabilities: tuple[LanguageCapability, ...] = (),
) -> LongitudinalSessionMetadata:
    return LongitudinalSessionMetadata(
        role="Backend Engineer",
        seniority="senior",
        interview_type="technical",
        question_count=5,
        session_language="en",
        knowledge_epoch=knowledge_epoch,
        total_objectives=2,
        total_narrative_insights=3,
        language_capabilities=language_capabilities,
    )


def _make_session_entry(
    session_id: str = SESSION_0,
    interview_index: int = 0,
    candidate_id: str = CANDIDATE_ID,
    contributed_at: datetime = FIXED_DT,
    confidence: float = 0.7,
    language_capabilities: tuple[LanguageCapability, ...] = (),
) -> LongitudinalSessionEntry:
    return LongitudinalSessionEntry(
        session_id=session_id,
        interview_index=interview_index,
        profile_snapshot=_make_snapshot(candidate_id, (_make_feature(candidate_id, confidence=confidence),)),
        session_metadata=_make_metadata(language_capabilities=language_capabilities),
        contributed_at=contributed_at,
    )


def _make_profile(
    candidate_id: str = CANDIDATE_ID,
    entries: tuple[LongitudinalSessionEntry, ...] | None = None,
    language_capability_summary: tuple[CrossSessionLanguageCapability, ...] = (),
) -> LongitudinalProfile:
    resolved = entries if entries is not None else (_make_session_entry(),)
    highest = max(resolved, key=lambda e: e.interview_index)
    return LongitudinalProfile(
        candidate_identity_id=candidate_id,
        session_snapshots=resolved,
        session_count=len(resolved),
        language_capability_summary=language_capability_summary,
        knowledge_epoch=highest.session_metadata.knowledge_epoch,
        schema_version="1.0",
        created_at=FIXED_DT,
        last_updated_at=FIXED_DT,
    )


def _make_lang_cap(
    language_id: str = "python",
    session_count: int = 2,
    composite_score: float = 0.75,
) -> CrossSessionLanguageCapability:
    return CrossSessionLanguageCapability(
        language_id=language_id,
        session_count_in_language=session_count,
        total_questions_answered=4,
        mean_composite_score=composite_score,
        mean_idiomatic_score=0.70,
        mean_type_error_rate=0.10,
        trend_direction="stable",
    )


def _build(profile: LongitudinalProfile | None, computed_at: datetime = FIXED_COMPUTED_AT) -> LearningProgress:
    return (
        LearningProgressBuilder()
        .with_longitudinal_profile(profile)
        .with_computed_at(computed_at)
        .build()
    )


# ===========================================================================
# LP-LP-07 — Input contract: only LongitudinalProfile accepted
# ===========================================================================

class TestBuilderInputContract:
    def test_with_session_histories_does_not_exist(self) -> None:
        """LP-LP-07: builder must not expose with_session_histories."""
        builder = LearningProgressBuilder()
        assert not hasattr(builder, "with_session_histories"), (
            "with_session_histories must not exist — ADR-034 Decision 5"
        )

    def test_builder_accepts_longitudinal_profile(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.candidate_identity_id == CANDIDATE_ID

    def test_builder_accepts_none_profile(self) -> None:
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_longitudinal_profile(None)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        assert progress.is_empty
        assert progress.has_sufficient_data is False


# ===========================================================================
# LP-LP-01 — session_entries length equals LongitudinalProfile.session_count
# ===========================================================================

class TestLPLP01SessionEntriesLength:
    def test_single_session_profile(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert len(progress.session_entries) == profile.session_count

    def test_two_session_profile(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert len(progress.session_entries) == 2

    def test_three_session_profile(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        e2 = _make_session_entry(session_id=SESSION_2, interview_index=2, contributed_at=DT_2)
        profile = _make_profile(entries=(e0, e1, e2))
        progress = _build(profile)
        assert len(progress.session_entries) == 3


# ===========================================================================
# LP-LP-02 — session_entries ordered by session_index ascending
# ===========================================================================

class TestLPLP02SessionOrdering:
    def test_entries_ordered_ascending(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        e2 = _make_session_entry(session_id=SESSION_2, interview_index=2, contributed_at=DT_2)
        profile = _make_profile(entries=(e0, e1, e2))
        progress = _build(profile)
        indices = [e.session_index for e in progress.session_entries]
        assert indices == sorted(indices)

    def test_session_ids_match_profile_order(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.session_entries[0].session_id == SESSION_0
        assert progress.session_entries[1].session_id == SESSION_1


# ===========================================================================
# LP-LP-03 — has_sufficient_data == (len(session_entries) >= 2)
# ===========================================================================

class TestLPLP03HasSufficientData:
    def test_none_profile_has_sufficient_data_false(self) -> None:
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_longitudinal_profile(None)
            .build()
        )
        assert progress.has_sufficient_data is False

    def test_one_session_has_sufficient_data_false(self) -> None:
        profile = _make_profile(entries=(_make_session_entry(),))
        progress = _build(profile)
        assert progress.has_sufficient_data is False

    def test_two_sessions_has_sufficient_data_true(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.has_sufficient_data is True

    def test_three_sessions_has_sufficient_data_true(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        e2 = _make_session_entry(session_id=SESSION_2, interview_index=2, contributed_at=DT_2)
        profile = _make_profile(entries=(e0, e1, e2))
        progress = _build(profile)
        assert progress.has_sufficient_data is True


# ===========================================================================
# LP-LP-04 — BehavioralTrend.sessions_analysed == len(session_entries)
# ===========================================================================

class TestLPLP04SessionsAnalysed:
    def test_single_session_sessions_analysed(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        assert progress.behavioral_trend.sessions_analysed == 1

    def test_two_sessions_sessions_analysed(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        assert progress.behavioral_trend.sessions_analysed == len(progress.session_entries)

    def test_none_profile_behavioral_trend_is_none(self) -> None:
        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_longitudinal_profile(None)
            .build()
        )
        assert progress.behavioral_trend is None


# ===========================================================================
# BehavioralTrend derivation
# ===========================================================================

class TestBehavioralTrendDerivation:
    def test_insufficient_data_when_single_session(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        assert progress.behavioral_trend.overall_trend_direction == "insufficient_data"
        assert progress.behavioral_trend.feature_trends == ()

    def test_two_sessions_produce_feature_trends(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0, confidence=0.5)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, confidence=0.8, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        assert len(progress.behavioral_trend.feature_trends) > 0

    def test_improving_trend_direction(self) -> None:
        """latest_confidence > earliest_confidence + 0.05 → improving."""
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0, confidence=0.4)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, confidence=0.8, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        ft = progress.behavioral_trend.feature_trends[0]
        assert ft.trend_direction == "improving"
        assert progress.behavioral_trend.overall_trend_direction == "improving"

    def test_declining_trend_direction(self) -> None:
        """latest_confidence < earliest_confidence - 0.05 → declining."""
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0, confidence=0.8)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, confidence=0.4, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        ft = progress.behavioral_trend.feature_trends[0]
        assert ft.trend_direction == "declining"

    def test_stable_trend_direction_within_threshold(self) -> None:
        """|latest - earliest| <= 0.05 → stable."""
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0, confidence=0.7)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, confidence=0.73, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        ft = progress.behavioral_trend.feature_trends[0]
        assert ft.trend_direction == "stable"

    def test_boundary_within_threshold_is_stable(self) -> None:
        """delta == 0.03 (< 0.05) → stable."""
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0, confidence=0.5)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, confidence=0.53, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        ft = progress.behavioral_trend.feature_trends[0]
        assert ft.trend_direction == "stable"

    def test_boundary_above_threshold_is_improving(self) -> None:
        """delta == 0.1 (> 0.05) → improving."""
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0, confidence=0.5)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, confidence=0.6, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        ft = progress.behavioral_trend.feature_trends[0]
        assert ft.trend_direction == "improving"

    def test_lp_lp_05_feature_trends_unique_ids(self) -> None:
        """LP-LP-05: all feature_type_id values in feature_trends are unique."""
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        ids = [ft.feature_type_id for ft in progress.behavioral_trend.feature_trends]
        assert len(ids) == len(set(ids))

    def test_feature_trend_carries_earliest_and_latest_confidence(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0, confidence=0.4)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, confidence=0.9, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        ft = progress.behavioral_trend.feature_trends[0]
        assert ft.earliest_confidence == pytest.approx(0.4)
        assert ft.latest_confidence == pytest.approx(0.9)
        assert ft.sessions_observed == 2

    def test_behavioral_trend_candidate_id_matches_profile(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        assert progress.behavioral_trend.candidate_identity_id == CANDIDATE_ID


# ===========================================================================
# Language capability summary propagation
# ===========================================================================

class TestLanguageCapabilitySummaryPropagation:
    def test_empty_language_capability_summary_when_no_coding_sessions(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.language_capability_summary == ()

    def test_language_capability_summary_propagated_from_profile(self) -> None:
        cap = _make_lang_cap(language_id="python", session_count=2)
        profile = _make_profile(language_capability_summary=(cap,))
        progress = _build(profile)
        assert len(progress.language_capability_summary) == 1
        assert progress.language_capability_summary[0].language_id == "python"

    def test_multiple_language_capabilities_propagated(self) -> None:
        py_cap = _make_lang_cap(language_id="python", session_count=2)
        ts_cap = _make_lang_cap(language_id="typescript", session_count=2)
        profile = _make_profile(language_capability_summary=(py_cap, ts_cap))
        progress = _build(profile)
        lang_ids = {cap.language_id for cap in progress.language_capability_summary}
        assert "python" in lang_ids
        assert "typescript" in lang_ids

    def test_language_ids_present_in_session_entry(self) -> None:
        lc = LanguageCapability(
            language_id="python",
            questions_answered_in_language=3,
            composite_score=0.8,
            idiomatic_usage_score=0.75,
            type_error_rate=0.1,
        )
        entry = _make_session_entry(language_capabilities=(lc,))
        profile = _make_profile(entries=(entry,))
        progress = _build(profile)
        assert "python" in progress.session_entries[0].language_ids_present

    def test_language_ids_empty_when_no_language_capabilities(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.session_entries[0].language_ids_present == ()


# ===========================================================================
# SessionProgressEntry derivation from LongitudinalSessionEntry
# ===========================================================================

class TestSessionEntryDerivation:
    def test_session_id_derived_from_entry(self) -> None:
        entry = _make_session_entry(session_id=SESSION_0)
        profile = _make_profile(entries=(entry,))
        progress = _build(profile)
        assert progress.session_entries[0].session_id == SESSION_0

    def test_session_index_derived_from_interview_index(self) -> None:
        entry = _make_session_entry(interview_index=3)
        profile = _make_profile(entries=(entry,))
        progress = _build(profile)
        assert progress.session_entries[0].session_index == 3

    def test_role_and_seniority_derived_from_metadata(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        entry = progress.session_entries[0]
        assert entry.role == "Backend Engineer"
        assert entry.seniority == "senior"

    def test_mean_confidence_derived_correctly(self) -> None:
        feature = _make_feature(confidence=0.6)
        snap = _make_snapshot(features=(feature,))
        meta = _make_metadata()
        lse = LongitudinalSessionEntry(
            session_id=SESSION_0,
            interview_index=0,
            profile_snapshot=snap,
            session_metadata=meta,
            contributed_at=FIXED_DT,
        )
        profile = _make_profile(entries=(lse,))
        progress = _build(profile)
        assert progress.session_entries[0].mean_confidence == pytest.approx(0.6)

    def test_behavioral_scores_derived_from_features(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        entry = progress.session_entries[0]
        assert len(entry.behavioral_scores) > 0

    def test_total_features_derived(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.session_entries[0].total_features == 1

    def test_immutability_of_produced_entry(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        with pytest.raises(Exception):
            progress.session_entries[0].session_id = "x"  # type: ignore[misc]


# ===========================================================================
# Immutability of produced contracts
# ===========================================================================

class TestImmutability:
    def test_learning_progress_is_immutable(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        with pytest.raises(Exception):
            progress.has_sufficient_data = False  # type: ignore[misc]
        with pytest.raises(Exception):
            progress.behavioral_trend = None  # type: ignore[misc]

    def test_profile_not_mutated_by_builder(self) -> None:
        profile = _make_profile()
        original_session_count = profile.session_count
        _ = _build(profile)
        assert profile.session_count == original_session_count


# ===========================================================================
# Serialization compatibility
# ===========================================================================

class TestSerialization:
    def test_learning_progress_model_dump_contains_new_fields(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        data = progress.model_dump()
        assert "has_sufficient_data" in data
        assert "behavioral_trend" in data
        assert "language_capability_summary" in data

    def test_behavioral_trend_serializes(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        progress = _build(profile)
        assert progress.behavioral_trend is not None
        data = progress.behavioral_trend.model_dump()
        restored = progress.behavioral_trend.__class__.model_validate(data)
        assert restored.sessions_analysed == progress.behavioral_trend.sessions_analysed
        assert restored.overall_trend_direction == progress.behavioral_trend.overall_trend_direction

    def test_session_entry_new_fields_serialise(self) -> None:
        lc = LanguageCapability(
            language_id="python",
            questions_answered_in_language=3,
            composite_score=0.8,
            idiomatic_usage_score=0.75,
            type_error_rate=0.1,
        )
        entry = _make_session_entry(language_capabilities=(lc,))
        profile = _make_profile(entries=(entry,))
        progress = _build(profile)
        data = progress.session_entries[0].model_dump()
        assert "behavioral_scores" in data
        assert "language_ids_present" in data
        assert list(data["language_ids_present"]) == ["python"]


# ===========================================================================
# Determinism
# ===========================================================================

class TestDeterminism:
    def test_same_profile_yields_same_result(self) -> None:
        e0 = _make_session_entry(session_id=SESSION_0, interview_index=0)
        e1 = _make_session_entry(session_id=SESSION_1, interview_index=1, contributed_at=DT_1)
        profile = _make_profile(entries=(e0, e1))
        p1 = _build(profile)
        p2 = _build(profile)
        assert p1.session_count == p2.session_count
        assert p1.has_sufficient_data == p2.has_sufficient_data
        assert p1.behavioral_trend is not None and p2.behavioral_trend is not None
        assert p1.behavioral_trend.overall_trend_direction == p2.behavioral_trend.overall_trend_direction


# ===========================================================================
# Regression compatibility — computed_at, schema_version, metadata
# ===========================================================================

class TestRegressionCompatibility:
    def test_computed_at_is_set(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.computed_at == FIXED_COMPUTED_AT

    def test_computed_at_defaults_to_utc_when_not_set(self) -> None:
        profile = _make_profile()
        progress = (
            LearningProgressBuilder()
            .with_longitudinal_profile(profile)
            .build()
        )
        assert progress.computed_at.tzinfo is not None

    def test_schema_version_default(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.schema_version == "1.0"

    def test_custom_schema_version(self) -> None:
        profile = _make_profile()
        progress = (
            LearningProgressBuilder()
            .with_longitudinal_profile(profile)
            .with_schema_version("2.0")
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        assert progress.schema_version == "2.0"

    def test_metadata_propagated(self) -> None:
        profile = _make_profile()
        progress = (
            LearningProgressBuilder()
            .with_longitudinal_profile(profile)
            .with_metadata({"source": "test"})
            .with_computed_at(FIXED_COMPUTED_AT)
            .build()
        )
        assert progress.metadata == {"source": "test"}

    def test_knowledge_epoch_from_profile(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.knowledge_epoch == "1"

    def test_candidate_identity_id_from_profile(self) -> None:
        profile = _make_profile()
        progress = _build(profile)
        assert progress.candidate_identity_id == CANDIDATE_ID
