# tests/ui/views/report/sections/test_progress_trend_panel.py
# EPIC-V13-05 Phase 4 — ProgressTrendPanel unit tests (OI-DM-01 / C-23).

from __future__ import annotations

from datetime import datetime, timezone

from domain.contracts.progress.learning_progress import (
    BehavioralTrend,
    FeatureTrend,
    LearningProgress,
    SessionProgressEntry,
)

from app.ui.views.report.sections.progress_trend_panel import (
    render_progress_trend_panel,
)

CANDIDATE_ID = "cand-progress-panel-001"
FIXED_DT = datetime(2026, 7, 16, 0, 0, 0, tzinfo=timezone.utc)


def _make_session_entry(
    session_id: str,
    session_index: int,
    question_count: int = 5,
) -> SessionProgressEntry:
    return SessionProgressEntry(
        session_id=session_id,
        session_index=session_index,
        created_at=FIXED_DT,
        role="backend_engineer",
        seniority="Senior",
        interview_type="technical",
        question_count=question_count,
        knowledge_epoch="1",
    )


def _make_feature_trend(
    feature_type_id: str = "reasoning_feature",
    trend_direction: str = "improving",
    earliest_confidence: float | None = 0.55,
    latest_confidence: float | None = 0.80,
    sessions_observed: int = 3,
) -> FeatureTrend:
    return FeatureTrend(
        feature_type_id=feature_type_id,
        semantic_category="analytical_reasoning",
        trend_direction=trend_direction,
        earliest_confidence=earliest_confidence,
        latest_confidence=latest_confidence,
        sessions_observed=sessions_observed,
    )


def _make_behavioral_trend(
    sessions_analysed: int,
    feature_trends: tuple[FeatureTrend, ...] = (),
    overall_trend_direction: str = "improving",
) -> BehavioralTrend:
    return BehavioralTrend(
        candidate_identity_id=CANDIDATE_ID,
        feature_trends=feature_trends,
        overall_trend_direction=overall_trend_direction,
        sessions_analysed=sessions_analysed,
    )


def _make_learning_progress(
    session_count: int,
    *,
    has_sufficient_data: bool | None = None,
    with_behavioral_trend: bool = True,
    overall_trend_direction: str = "improving",
) -> LearningProgress:
    entries = tuple(
        _make_session_entry(f"sess-{index:03d}", index)
        for index in range(session_count)
    )
    if has_sufficient_data is None:
        has_sufficient_data = session_count >= 2

    behavioral_trend: BehavioralTrend | None = None
    if with_behavioral_trend and session_count > 0:
        behavioral_trend = _make_behavioral_trend(
            sessions_analysed=session_count,
            feature_trends=(_make_feature_trend(sessions_observed=max(session_count, 1)),),
            overall_trend_direction=overall_trend_direction,
        )

    return LearningProgress(
        candidate_identity_id=CANDIDATE_ID,
        session_entries=entries,
        computed_at=FIXED_DT,
        behavioral_trend=behavioral_trend,
        has_sufficient_data=has_sufficient_data,
    )


class TestProgressTrendPanelVisibilityGate:
    """UI gate is session_count >= 3 only (not has_sufficient_data)."""

    def test_session_count_zero_renders_insufficient_data(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(0))
        assert 'data-progress-state="insufficient-data"' in html
        assert "Insufficient data" in html
        assert 'data-progress-state="trend"' not in html
        assert "reasoning_feature" not in html

    def test_session_count_one_renders_insufficient_data(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(1))
        assert 'data-progress-state="insufficient-data"' in html
        assert "1 session recorded" in html
        assert "reasoning_feature" not in html

    def test_session_count_two_renders_insufficient_data(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(2))
        assert 'data-progress-state="insufficient-data"' in html
        assert "2 sessions recorded" in html
        assert "No trend is extrapolated" in html
        assert "reasoning_feature" not in html
        assert 'data-overall-trend=' not in html

    def test_session_count_two_with_domain_sufficient_flag_still_insufficient(
        self,
    ) -> None:
        """LP-LP-03 may be true at 2; UI gate remains session_count >= 3."""
        progress = _make_learning_progress(2, has_sufficient_data=True)
        assert progress.has_sufficient_data is True
        html = render_progress_trend_panel(progress)
        assert 'data-progress-state="insufficient-data"' in html
        assert 'data-progress-state="trend"' not in html
        assert "reasoning_feature" not in html

    def test_session_count_three_renders_trend(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(3))
        assert 'data-progress-state="trend"' in html
        assert 'data-progress-state="insufficient-data"' not in html
        assert "Progress Trend" in html

    def test_session_count_four_renders_trend(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(4))
        assert 'data-progress-state="trend"' in html
        assert "4 completed sessions" in html


class TestProgressTrendPanelTrendRendering:
    def test_renders_feature_trend_fields(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(3))
        assert "reasoning_feature" in html
        assert "Improving" in html
        assert "55%" in html
        assert "80%" in html
        assert "observed: 3" in html

    def test_renders_overall_trend_direction(self) -> None:
        html = render_progress_trend_panel(
            _make_learning_progress(3, overall_trend_direction="declining")
        )
        assert 'data-overall-trend="declining"' in html
        assert "Overall: Declining" in html

    def test_renders_session_markers_from_entries(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(3))
        assert 'data-progress-markers="session-entries"' in html
        assert "Session 0" in html
        assert "Session 1" in html
        assert "Session 2" in html
        assert "5 questions" in html

    def test_trend_without_behavioral_trend_does_not_fabricate(self) -> None:
        progress = _make_learning_progress(3, with_behavioral_trend=False)
        html = render_progress_trend_panel(progress)
        assert 'data-progress-state="trend"' in html
        assert 'data-progress-trend="absent"' in html
        assert "No behavioral trend summary is available" in html
        assert "reasoning_feature" not in html

    def test_insufficient_data_does_not_include_trend_markers(self) -> None:
        html = render_progress_trend_panel(_make_learning_progress(2))
        assert 'data-progress-markers="session-entries"' not in html
        assert 'data-progress-trend="behavioral"' not in html
