# tests/ui/replay/test_replay_panel_freeze_invariant.py

from __future__ import annotations

from dataclasses import fields

from app.ui.replay.panels.replay_coaching_panel import (
    CoachingViewModel,
    ReplayCoachingPanel,
)
from app.ui.replay.panels.replay_error_boundary import ErrorViewModel, ReplayErrorBoundary
from app.ui.replay.panels.replay_execution_result_panel import ExecutionResultViewModel
from app.ui.replay.panels.replay_question_panel import QuestionViewModel, ReplayQuestionPanel
from app.ui.replay.panels.replay_scoring_panel import ReplayScoringPanel, ScoringViewModel
from app.ui.replay.panels.replay_session_summary_panel import (
    ReplaySessionSummaryPanel,
    SessionSummaryViewModel,
)
from tests.ui.replay.conftest import (
    make_question_record,
    make_replay_session,
    make_scoring_snapshot,
)

_EXCLUDED_FIELD_NAMES = frozenset(
    {
        "candidate_identity_id",
        "schema_version",
        "replay_mode",
        "replay_level",
        "profile_snapshot",
        "policy_versions",
        "knowledge_epoch",
        "manifest",
        "observation_store_snapshot",
    }
)


def test_view_models_exclude_frozen_replay_session_fields() -> None:
    for model_type in (
        SessionSummaryViewModel,
        QuestionViewModel,
        ExecutionResultViewModel,
        ScoringViewModel,
        CoachingViewModel,
        ErrorViewModel,
    ):
        names = {f.name for f in fields(model_type)}
        assert names.isdisjoint(_EXCLUDED_FIELD_NAMES)


def test_panels_do_not_surface_excluded_session_identity_fields() -> None:
    coding = make_question_record(
        execution_status="passed",
        passed_tests=3,
        total_tests=3,
        strengths=(),
        weaknesses=(),
        follow_up_question=None,
        ai_hint_explanation=None,
        ai_hint_suggestion=None,
    )
    session = make_replay_session(
        question_results=(coding,),
        scoring_snapshot=make_scoring_snapshot(),
        coaching_snapshot=None,
    )
    failed = make_replay_session(
        is_successful=False,
        failure_reason="SessionHistory not found",
    )

    summary = ReplaySessionSummaryPanel(session).render()
    question = ReplayQuestionPanel(coding).render()
    scoring = ReplayScoringPanel(session).render()
    coaching = ReplayCoachingPanel(session).render()
    error = ReplayErrorBoundary(failed).render()

    display_blobs = (
        summary.session_date_display,
        summary.role,
        summary.score_unavailable_label or "",
        question.answer_display,
        question.feedback,
        "" if scoring is None else scoring.percentile_explanation,
        coaching.section_a_label,
        coaching.section_b_label,
        coaching.narrative_empty_label or "",
        coaching.coaching_empty_label or "",
        error.candidate_message,
        error.action_label,
    )
    joined = " ".join(display_blobs)

    assert session.knowledge_epoch not in joined or session.knowledge_epoch == "1"
    # Identity / provenance artifacts must not appear in candidate-facing labels.
    assert session.candidate_identity_id not in joined
    assert "ReplayManifest" not in joined
    assert "policy_versions" not in joined
    assert "profile_snapshot" not in joined
    assert "observation_store_snapshot" not in joined
