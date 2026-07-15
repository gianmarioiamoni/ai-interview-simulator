# tests/domain/contracts/progress/test_learning_progress_p2_c1_contracts.py
# EPIC-02 / P2-C1 — Contract tests for new LearningProgress field extensions
# Covers: BehavioralScore, FeatureTrend, BehavioralTrend, SessionProgressEntry extensions,
#         LearningProgress extensions; invariants LP-LP-01 through LP-LP-07.

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.longitudinal.longitudinal_profile import CrossSessionLanguageCapability
from domain.contracts.progress.learning_progress import (
    BehavioralScore,
    BehavioralTrend,
    DimensionalScore,
    FeatureTrend,
    LearningProgress,
    SessionProgressEntry,
)

CANDIDATE_ID = "cand-p2c1-001"
FIXED_DT = datetime(2026, 7, 15, 0, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_behavioral_score(
    feature_type_id: str = "reasoning_feature",
    semantic_category: str = "analytical_reasoning",
    confidence: float = 0.7,
    session_index: int = 0,
) -> BehavioralScore:
    return BehavioralScore(
        feature_type_id=feature_type_id,
        semantic_category=semantic_category,
        confidence=confidence,
        session_index=session_index,
    )


def _make_feature_trend(
    feature_type_id: str = "reasoning_feature",
    semantic_category: str = "analytical_reasoning",
    trend_direction: str = "stable",
    earliest_confidence: float | None = None,
    latest_confidence: float | None = None,
    sessions_observed: int = 2,
) -> FeatureTrend:
    return FeatureTrend(
        feature_type_id=feature_type_id,
        semantic_category=semantic_category,
        trend_direction=trend_direction,
        earliest_confidence=earliest_confidence,
        latest_confidence=latest_confidence,
        sessions_observed=sessions_observed,
    )


def _make_behavioral_trend(
    candidate_id: str = CANDIDATE_ID,
    feature_trends: tuple[FeatureTrend, ...] = (),
    overall_trend_direction: str = "stable",
    sessions_analysed: int = 2,
) -> BehavioralTrend:
    return BehavioralTrend(
        candidate_identity_id=candidate_id,
        feature_trends=feature_trends,
        overall_trend_direction=overall_trend_direction,
        sessions_analysed=sessions_analysed,
    )


def _make_cross_session_lang_cap(
    language_id: str = "python",
    session_count: int = 2,
) -> CrossSessionLanguageCapability:
    return CrossSessionLanguageCapability(
        language_id=language_id,
        session_count_in_language=session_count,
        total_questions_answered=4,
        mean_composite_score=0.75,
        mean_idiomatic_score=0.70,
        mean_type_error_rate=0.10,
        trend_direction="stable",
    )


def _make_session_entry(
    session_id: str = "sess-001",
    session_index: int = 0,
    behavioral_scores: tuple[BehavioralScore, ...] = (),
    language_ids_present: tuple[str, ...] = (),
) -> SessionProgressEntry:
    return SessionProgressEntry(
        session_id=session_id,
        session_index=session_index,
        created_at=FIXED_DT,
        role="backend_engineer",
        seniority="Senior",
        interview_type="technical",
        question_count=5,
        knowledge_epoch="1",
        behavioral_scores=behavioral_scores,
        language_ids_present=language_ids_present,
    )


def _make_learning_progress(
    session_entries: tuple[SessionProgressEntry, ...] = (),
    behavioral_trend: BehavioralTrend | None = None,
    language_capability_summary: tuple[CrossSessionLanguageCapability, ...] = (),
    has_sufficient_data: bool = False,
) -> LearningProgress:
    return LearningProgress(
        candidate_identity_id=CANDIDATE_ID,
        session_entries=session_entries,
        computed_at=FIXED_DT,
        behavioral_trend=behavioral_trend,
        language_capability_summary=language_capability_summary,
        has_sufficient_data=has_sufficient_data,
    )


# ===========================================================================
# BehavioralScore contract tests
# ===========================================================================

class TestBehavioralScoreContract:
    def test_behavioral_score_is_immutable(self) -> None:
        score = _make_behavioral_score()
        with pytest.raises(Exception):
            score.feature_type_id = "x"  # type: ignore[misc]

    def test_behavioral_score_confidence_bounds(self) -> None:
        with pytest.raises(Exception):
            BehavioralScore(
                feature_type_id="ft",
                semantic_category="cat",
                confidence=1.1,
                session_index=0,
            )
        with pytest.raises(Exception):
            BehavioralScore(
                feature_type_id="ft",
                semantic_category="cat",
                confidence=-0.1,
                session_index=0,
            )

    def test_behavioral_score_valid_boundary_values(self) -> None:
        low = BehavioralScore(
            feature_type_id="ft", semantic_category="cat", confidence=0.0, session_index=0
        )
        high = BehavioralScore(
            feature_type_id="ft", semantic_category="cat", confidence=1.0, session_index=0
        )
        assert low.confidence == 0.0
        assert high.confidence == 1.0

    def test_behavioral_score_rejects_extra_fields(self) -> None:
        with pytest.raises(Exception):
            BehavioralScore(  # type: ignore[call-arg]
                feature_type_id="ft",
                semantic_category="cat",
                confidence=0.5,
                session_index=0,
                extra_field="bad",
            )


# ===========================================================================
# FeatureTrend contract tests
# ===========================================================================

class TestFeatureTrendContract:
    def test_feature_trend_is_immutable(self) -> None:
        ft = _make_feature_trend()
        with pytest.raises(Exception):
            ft.feature_type_id = "x"  # type: ignore[misc]

    def test_feature_trend_valid_directions(self) -> None:
        for direction in ("improving", "declining", "stable", "insufficient_data"):
            ft = _make_feature_trend(trend_direction=direction)
            assert ft.trend_direction == direction

    def test_feature_trend_rejects_invalid_direction(self) -> None:
        with pytest.raises(ValueError, match="trend_direction"):
            _make_feature_trend(trend_direction="unknown")

    def test_feature_trend_sessions_observed_ge_1(self) -> None:
        with pytest.raises(Exception):
            FeatureTrend(
                feature_type_id="ft",
                semantic_category="cat",
                trend_direction="stable",
                sessions_observed=0,
            )

    def test_feature_trend_optional_confidences(self) -> None:
        ft = _make_feature_trend(earliest_confidence=0.4, latest_confidence=0.6)
        assert ft.earliest_confidence == 0.4
        assert ft.latest_confidence == 0.6

    def test_feature_trend_none_confidences_allowed(self) -> None:
        ft = _make_feature_trend()
        assert ft.earliest_confidence is None
        assert ft.latest_confidence is None

    def test_feature_trend_default_direction_is_stable(self) -> None:
        ft = FeatureTrend(
            feature_type_id="ft", semantic_category="cat", sessions_observed=2
        )
        assert ft.trend_direction == "stable"


# ===========================================================================
# BehavioralTrend contract tests
# ===========================================================================

class TestBehavioralTrendContract:
    def test_behavioral_trend_is_immutable(self) -> None:
        bt = _make_behavioral_trend()
        with pytest.raises(Exception):
            bt.candidate_identity_id = "x"  # type: ignore[misc]

    def test_behavioral_trend_valid_overall_directions(self) -> None:
        for direction in ("improving", "declining", "stable", "insufficient_data"):
            bt = _make_behavioral_trend(overall_trend_direction=direction)
            assert bt.overall_trend_direction == direction

    def test_behavioral_trend_rejects_invalid_overall_direction(self) -> None:
        with pytest.raises(ValueError, match="overall_trend_direction"):
            _make_behavioral_trend(overall_trend_direction="unknown")

    def test_behavioral_trend_default_schema_version(self) -> None:
        bt = _make_behavioral_trend()
        assert bt.schema_version == "1.0"

    def test_behavioral_trend_sessions_analysed_ge_0(self) -> None:
        with pytest.raises(Exception):
            BehavioralTrend(
                candidate_identity_id=CANDIDATE_ID,
                sessions_analysed=-1,
                overall_trend_direction="stable",
            )

    def test_lp_lp_05_unique_feature_type_ids(self) -> None:
        ft1 = _make_feature_trend(feature_type_id="reasoning_feature")
        ft2 = _make_feature_trend(feature_type_id="reasoning_feature")
        with pytest.raises(ValueError, match="LP-LP-05"):
            BehavioralTrend(
                candidate_identity_id=CANDIDATE_ID,
                feature_trends=(ft1, ft2),
                sessions_analysed=2,
                overall_trend_direction="stable",
            )

    def test_behavioral_trend_empty_feature_trends_allowed(self) -> None:
        bt = _make_behavioral_trend(feature_trends=())
        assert bt.feature_trends == ()


# ===========================================================================
# SessionProgressEntry P2-C1 extensions
# ===========================================================================

class TestSessionProgressEntryExtensions:
    def test_behavioral_scores_default_empty(self) -> None:
        entry = _make_session_entry()
        assert entry.behavioral_scores == ()

    def test_language_ids_present_default_empty(self) -> None:
        entry = _make_session_entry()
        assert entry.language_ids_present == ()

    def test_behavioral_scores_populated(self) -> None:
        score = _make_behavioral_score()
        entry = _make_session_entry(behavioral_scores=(score,))
        assert len(entry.behavioral_scores) == 1
        assert entry.behavioral_scores[0].feature_type_id == "reasoning_feature"

    def test_language_ids_present_populated(self) -> None:
        entry = _make_session_entry(language_ids_present=("python", "typescript"))
        assert "python" in entry.language_ids_present
        assert "typescript" in entry.language_ids_present

    def test_entry_is_immutable_with_new_fields(self) -> None:
        entry = _make_session_entry()
        with pytest.raises(Exception):
            entry.behavioral_scores = ()  # type: ignore[misc]
        with pytest.raises(Exception):
            entry.language_ids_present = ()  # type: ignore[misc]

    def test_existing_fields_unchanged(self) -> None:
        score = DimensionalScore(
            feature_type_id="ft",
            semantic_category="cat",
            confidence=0.6,
            session_index=0,
        )
        entry = SessionProgressEntry(
            session_id="s1",
            session_index=0,
            created_at=FIXED_DT,
            role="backend_engineer",
            seniority="Senior",
            interview_type="technical",
            question_count=5,
            knowledge_epoch="1",
            dimensional_scores=(score,),
            mean_confidence=0.6,
            total_features=1,
            total_objectives=2,
            total_narrative_insights=3,
        )
        assert entry.dimensional_scores[0].feature_type_id == "ft"
        assert entry.mean_confidence == 0.6
        assert entry.total_features == 1


# ===========================================================================
# LearningProgress P2-C1 extensions
# ===========================================================================

class TestLearningProgressExtensions:
    def test_has_sufficient_data_default_false(self) -> None:
        progress = _make_learning_progress()
        assert progress.has_sufficient_data is False

    def test_language_capability_summary_default_empty(self) -> None:
        progress = _make_learning_progress()
        assert progress.language_capability_summary == ()

    def test_behavioral_trend_default_none(self) -> None:
        progress = _make_learning_progress()
        assert progress.behavioral_trend is None

    def test_learning_progress_with_behavioral_trend(self) -> None:
        bt = _make_behavioral_trend(sessions_analysed=2)
        entry0 = _make_session_entry(session_id="s0", session_index=0)
        entry1 = _make_session_entry(session_id="s1", session_index=1)
        progress = _make_learning_progress(
            session_entries=(entry0, entry1),
            behavioral_trend=bt,
            has_sufficient_data=True,
        )
        assert progress.behavioral_trend is not None
        assert progress.behavioral_trend.sessions_analysed == 2
        assert progress.has_sufficient_data is True

    def test_learning_progress_with_language_capability_summary(self) -> None:
        cap = _make_cross_session_lang_cap()
        progress = _make_learning_progress(language_capability_summary=(cap,))
        assert len(progress.language_capability_summary) == 1
        assert progress.language_capability_summary[0].language_id == "python"

    def test_lp_lp_03_has_sufficient_data_two_entries(self) -> None:
        entry0 = _make_session_entry(session_id="s0", session_index=0)
        entry1 = _make_session_entry(session_id="s1", session_index=1)
        progress = _make_learning_progress(
            session_entries=(entry0, entry1),
            has_sufficient_data=True,
        )
        assert progress.has_sufficient_data is True
        assert progress.session_count == 2

    def test_lp_lp_03_has_sufficient_data_false_one_entry(self) -> None:
        entry0 = _make_session_entry()
        progress = _make_learning_progress(
            session_entries=(entry0,),
            has_sufficient_data=False,
        )
        assert progress.has_sufficient_data is False
        assert progress.session_count == 1

    def test_lp_lp_03_has_sufficient_data_false_zero_entries(self) -> None:
        progress = _make_learning_progress(has_sufficient_data=False)
        assert progress.has_sufficient_data is False
        assert progress.session_count == 0

    def test_existing_fields_unchanged_after_extension(self) -> None:
        progress = _make_learning_progress()
        assert progress.candidate_identity_id == CANDIDATE_ID
        assert progress.schema_version == "1.0"
        assert progress.knowledge_epoch == "1"
        assert isinstance(progress.metadata, dict)

    def test_learning_progress_is_immutable_with_new_fields(self) -> None:
        progress = _make_learning_progress()
        with pytest.raises(Exception):
            progress.has_sufficient_data = True  # type: ignore[misc]
        with pytest.raises(Exception):
            progress.behavioral_trend = None  # type: ignore[misc]
        with pytest.raises(Exception):
            progress.language_capability_summary = ()  # type: ignore[misc]

    def test_no_persistence_id_on_learning_progress(self) -> None:
        progress = _make_learning_progress()
        assert not hasattr(progress, "progress_id")


# ===========================================================================
# Invariant tests (LP-LP-01 through LP-LP-05)
# ===========================================================================

class TestLPLPInvariants:
    def test_lp_lp_01_session_entries_length(self) -> None:
        """LP-LP-01: session_entries length can equal session_count of source profile."""
        entries = (
            _make_session_entry("s0", 0),
            _make_session_entry("s1", 1),
            _make_session_entry("s2", 2),
        )
        progress = _make_learning_progress(session_entries=entries)
        assert len(progress.session_entries) == 3

    def test_lp_lp_02_entries_ordered_by_session_index(self) -> None:
        """LP-LP-02: session_entries must be ordered by session_index ascending."""
        entries = (
            _make_session_entry("s0", 0),
            _make_session_entry("s1", 1),
            _make_session_entry("s2", 2),
        )
        progress = _make_learning_progress(session_entries=entries)
        indices = [e.session_index for e in progress.session_entries]
        assert indices == sorted(indices)

    def test_lp_lp_04_sessions_analysed_matches_entries(self) -> None:
        """LP-LP-04: BehavioralTrend.sessions_analysed == len(session_entries)."""
        entries = (
            _make_session_entry("s0", 0),
            _make_session_entry("s1", 1),
        )
        bt = _make_behavioral_trend(sessions_analysed=len(entries))
        progress = _make_learning_progress(
            session_entries=entries,
            behavioral_trend=bt,
            has_sufficient_data=True,
        )
        assert progress.behavioral_trend is not None
        assert progress.behavioral_trend.sessions_analysed == len(progress.session_entries)

    def test_lp_lp_05_unique_feature_type_ids_enforced_in_behavioral_trend(self) -> None:
        """LP-LP-05: duplicate feature_type_id raises in BehavioralTrend."""
        ft = _make_feature_trend(feature_type_id="dup_feature")
        with pytest.raises(ValueError, match="LP-LP-05"):
            BehavioralTrend(
                candidate_identity_id=CANDIDATE_ID,
                feature_trends=(ft, ft),
                sessions_analysed=2,
                overall_trend_direction="stable",
            )


# ===========================================================================
# Serialization / round-trip tests
# ===========================================================================

class TestSerialization:
    def test_behavioral_score_model_dump(self) -> None:
        score = _make_behavioral_score(confidence=0.8)
        data = score.model_dump()
        assert data["feature_type_id"] == "reasoning_feature"
        assert data["confidence"] == 0.8

    def test_feature_trend_model_dump(self) -> None:
        ft = _make_feature_trend(
            earliest_confidence=0.5, latest_confidence=0.7, sessions_observed=3
        )
        data = ft.model_dump()
        assert data["earliest_confidence"] == 0.5
        assert data["latest_confidence"] == 0.7
        assert data["sessions_observed"] == 3

    def test_behavioral_trend_round_trip(self) -> None:
        ft = _make_feature_trend()
        bt = _make_behavioral_trend(feature_trends=(ft,))
        data = bt.model_dump()
        restored = BehavioralTrend.model_validate(data)
        assert restored.candidate_identity_id == bt.candidate_identity_id
        assert len(restored.feature_trends) == 1

    def test_learning_progress_new_fields_serialise(self) -> None:
        cap = _make_cross_session_lang_cap()
        bt = _make_behavioral_trend(sessions_analysed=0)
        progress = _make_learning_progress(
            behavioral_trend=bt,
            language_capability_summary=(cap,),
            has_sufficient_data=False,
        )
        data = progress.model_dump()
        assert "behavioral_trend" in data
        assert "language_capability_summary" in data
        assert "has_sufficient_data" in data
        assert data["has_sufficient_data"] is False
        assert len(data["language_capability_summary"]) == 1
