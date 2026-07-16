# tests/ui/views/report/test_learning_progress_bind.py
# EPIC-V13-05 Phase 5 — LearningProgress bind into Unified Report presentation surface.

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.ui.builders.ui_response_builder import UIResponseBuilder
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report.learning_progress_binder import bind_learning_progress
from app.ui.views.report_view import build_report_markdown
from domain.contracts.progress.learning_progress import (
    BehavioralTrend,
    FeatureTrend,
    LearningProgress,
    SessionProgressEntry,
)
from services.progress.progress_tracker import ProgressTracker
from tests.domain.contracts.report.conftest import make_report
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question

CANDIDATE_ID = "cand-phase5-bind-001"
FIXED_DT = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)


def _make_session_entry(session_index: int) -> SessionProgressEntry:
    return SessionProgressEntry(
        session_id=f"sess-{session_index:03d}",
        session_index=session_index,
        created_at=FIXED_DT,
        role="backend_engineer",
        seniority="Senior",
        interview_type="technical",
        question_count=5,
        knowledge_epoch="1",
    )


def _make_learning_progress(session_count: int) -> LearningProgress:
    entries = tuple(_make_session_entry(i) for i in range(session_count))
    behavioral_trend: BehavioralTrend | None = None
    if session_count >= 2:
        behavioral_trend = BehavioralTrend(
            candidate_identity_id=CANDIDATE_ID,
            feature_trends=(
                FeatureTrend(
                    feature_type_id="reasoning_feature",
                    semantic_category="analytical_reasoning",
                    trend_direction="improving",
                    earliest_confidence=0.50,
                    latest_confidence=0.80,
                    sessions_observed=session_count,
                ),
            ),
            overall_trend_direction="improving",
            sessions_analysed=session_count,
        )
    return LearningProgress(
        candidate_identity_id=CANDIDATE_ID,
        session_entries=entries,
        computed_at=FIXED_DT,
        behavioral_trend=behavioral_trend,
        has_sufficient_data=session_count >= 2,
    )


def _report_state():
    question = build_question(qid="q1")
    state = build_interview_state(questions=[question])
    report = make_report(candidate_id=CANDIDATE_ID)
    return state.model_copy(
        update={
            "is_completed": True,
            "report": report,
        }
    )


class TestBindLearningProgress:
    def test_bind_uses_progress_tracker_with_candidate_id(self) -> None:
        expected = _make_learning_progress(0)
        tracker = MagicMock(spec=ProgressTracker)
        tracker.get_progress.return_value = expected

        result = bind_learning_progress(CANDIDATE_ID, progress_tracker=tracker)

        assert result is expected
        tracker.get_progress.assert_called_once_with(CANDIDATE_ID)

    def test_bind_rejects_blank_candidate_id(self) -> None:
        with pytest.raises(ValueError, match="candidate_identity_id"):
            bind_learning_progress("   ")

    def test_bind_does_not_import_session_history(self) -> None:
        import ast

        import app.ui.views.report.learning_progress_binder as binder_mod

        tree = ast.parse(Path(binder_mod.__file__).read_text(encoding="utf-8"))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imported_names.add(module)
                imported_names.update(alias.name for alias in node.names)

        assert not any("session_history" in name for name in imported_names)
        assert "SessionHistory" not in imported_names


class TestReportSurfaceProgressIntegration:
    def test_report_html_includes_insufficient_data_when_session_count_below_3(
        self,
    ) -> None:
        dto = FinalReportDTO.from_report(make_report(candidate_id=CANDIDATE_ID))
        html = build_report_markdown(dto, learning_progress=_make_learning_progress(2))

        assert "Progress Trend" in html
        assert 'data-progress-state="insufficient-data"' in html
        assert "reasoning_feature" not in html

    def test_report_html_includes_trend_when_session_count_at_least_3(self) -> None:
        dto = FinalReportDTO.from_report(make_report(candidate_id=CANDIDATE_ID))
        html = build_report_markdown(dto, learning_progress=_make_learning_progress(3))

        assert "Progress Trend" in html
        assert 'data-progress-state="trend"' in html
        assert "reasoning_feature" in html
        assert "Study Recommendations" in html or "AI Interview Evaluation" in html

    def test_report_html_omits_progress_panel_when_learning_progress_absent(
        self,
    ) -> None:
        dto = FinalReportDTO.from_report(make_report(candidate_id=CANDIDATE_ID))
        html = build_report_markdown(dto)

        assert "Progress Trend" not in html
        assert 'data-progress-state=' not in html

    def test_progress_not_embedded_in_final_report_dto(self) -> None:
        dto = FinalReportDTO.from_report(make_report(candidate_id=CANDIDATE_ID))
        assert not hasattr(dto, "learning_progress")
        assert "learning_progress" not in dto.model_fields
        assert "behavioral_trend" not in dto.model_fields


class TestUIResponseBuilderProgressBind:
    def test_build_report_binds_learning_progress_into_html(self) -> None:
        progress = _make_learning_progress(3)
        builder = UIResponseBuilder()
        state = _report_state()

        with patch(
            "app.ui.builders.ui_response_builder.bind_learning_progress",
            return_value=progress,
        ) as mock_bind:
            response = builder.build(state)

        mock_bind.assert_called_once_with(CANDIDATE_ID)
        assert response.report_section_visible is True
        assert "Progress Trend" in response.report_output
        assert 'data-progress-state="trend"' in response.report_output

    def test_build_report_shows_insufficient_data_for_sparse_progress(self) -> None:
        progress = _make_learning_progress(1)
        builder = UIResponseBuilder()
        state = _report_state()

        with patch(
            "app.ui.builders.ui_response_builder.bind_learning_progress",
            return_value=progress,
        ):
            response = builder.build(state)

        assert 'data-progress-state="insufficient-data"' in response.report_output
        assert "reasoning_feature" not in response.report_output
